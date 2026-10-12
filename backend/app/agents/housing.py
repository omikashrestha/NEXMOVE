import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.arbitration import RevisionRequest


_CUSTOM_LISTINGS: Dict[str, Dict[str, Any]] = {}


def _record_to_dict(r: Any) -> Dict[str, Any]:
    return {
        "property_id": r.id,
        "project_id": r.project_id,
        "title": r.title,
        "city": r.city,
        "neighborhood": r.neighborhood,
        "bhk": r.bhk,
        "monthly_rent_inr": r.monthly_rent_inr,
        "security_deposit_inr": r.security_deposit_inr,
        "society_maintenance_inr": r.society_maintenance_inr,
        "move_in_fee_inr": r.move_in_fee_inr,
        "pet_friendly": r.pet_friendly,
        "commute_to_workplace_mins": r.commute_to_workplace_mins,
        "safety_score_index": r.safety_score_index,
        "datasource": r.datasource,
        "property_type": r.property_type,
        "is_verified": r.is_verified,
    }


def _get_active_db_session():
    """Returns an active DB session, checking FastAPI dependency overrides first if running under test."""
    try:
        from backend.app.main import app
        from backend.app.db.session import get_db
        if get_db in app.dependency_overrides:
            override = app.dependency_overrides[get_db]
            gen = override()
            return (next(gen) if hasattr(gen, "__next__") else gen), True
    except Exception:
        pass
    try:
        from backend.app.db.session import SessionLocal
        return SessionLocal(), True
    except Exception:
        return None, False


def _load_persisted_custom_listings(db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Loads custom properties persisted in SQLite database."""
    records = []
    session = db
    should_close = False
    if session is None:
        session, should_close = _get_active_db_session()

    if session is None:
        return records

    try:
        from backend.app.db.models import CustomPropertyRecord
        db_records = session.query(CustomPropertyRecord).all()
        for r in db_records:
            records.append(_record_to_dict(r))
    except Exception:
        pass
    finally:
        if should_close and session is not None:
            try:
                session.close()
            except Exception:
                pass
    return records


class HousingResearchAgent:
    """Specialized agent for filtering and ranking synthetic housing listings in INR."""

    @classmethod
    def register_custom_listing(cls, listing: Dict[str, Any], db: Optional[Any] = None):
        """Registers a user-provided custom property listing and persists to DB."""
        _CUSTOM_LISTINGS[listing["property_id"]] = listing
        prop_id = listing["property_id"]

        session = db
        should_close = False
        if session is None:
            session, should_close = _get_active_db_session()

        if session is not None:
            try:
                from backend.app.db.models import CustomPropertyRecord
                record_data = {
                    "id": prop_id,
                    "project_id": listing.get("project_id"),
                    "title": listing.get("title") or "Custom Property",
                    "city": listing.get("city") or "",
                    "neighborhood": listing.get("neighborhood") or "",
                    "bhk": int(listing.get("bhk") or 2),
                    "monthly_rent_inr": float(listing.get("monthly_rent_inr") or 0.0),
                    "security_deposit_inr": float(listing.get("security_deposit_inr") or 0.0),
                    "society_maintenance_inr": float(listing.get("society_maintenance_inr") or 0.0),
                    "move_in_fee_inr": float(listing.get("move_in_fee_inr") or 0.0),
                    "pet_friendly": bool(listing.get("pet_friendly", False)),
                    "commute_to_workplace_mins": int(listing.get("commute_to_workplace_mins") or 30),
                    "safety_score_index": float(listing.get("safety_score_index") or 8.5),
                    "datasource": listing.get("datasource") or "USER_MANUAL_ENTRY",
                    "property_type": listing.get("property_type") or "Apartment",
                    "is_verified": bool(listing.get("is_verified", True)),
                }

                existing = session.query(CustomPropertyRecord).filter_by(id=prop_id).first()
                if existing:
                    for k, v in record_data.items():
                        setattr(existing, k, v)
                else:
                    session.add(CustomPropertyRecord(**record_data))

                if should_close:
                    session.commit()
                else:
                    session.flush()
            except Exception:
                pass
            finally:
                if should_close and session is not None:
                    try:
                        session.close()
                    except Exception:
                        pass

    def __init__(self, data_path: Optional[Path] = None, db: Optional[Any] = None):
        self.data_path = data_path or (DATA_DIR / "housing_samples_inr.json")
        self._db = db
        self._listings = self._load_listings()

    def _load_listings(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Housing benchmark dataset not found at {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        base_listings = data.get("listings", [])

        # Merge persisted custom listings and in-memory listings
        custom_map: Dict[str, Dict[str, Any]] = {}
        for item in _load_persisted_custom_listings(db=self._db):
            custom_map[item["property_id"]] = item
        for k, v in _CUSTOM_LISTINGS.items():
            custom_map[k] = v

        return base_listings + list(custom_map.values())

    def _filter_and_score_candidates(
        self,
        profile: RelocationProfile,
        revision_request: Optional[RevisionRequest] = None
    ) -> List[Dict[str, Any]]:
        if not self._listings:
            raise ValueError("Housing benchmark dataset contains zero listings.")

        city_lower = profile.destination_city.strip().lower()
        candidates = [
            item for item in self._listings 
            if item.get("city", "").strip().lower() == city_lower
        ]

        # Critical: Do not substitute another city if no listings exist for destination
        if not candidates:
            return []

        # 1. Hard Constraint: Pet Accommodations (Never violate pet requirement)
        if profile.has_pets:
            pet_candidates = [item for item in candidates if item.get("pet_friendly") is True]
            if not pet_candidates:
                if not any(item.get("pet_friendly") is True for item in self._listings):
                    raise ValueError("No pet-friendly accommodations available in benchmark dataset matching profile.")
                # No pet-friendly home available in destination city satisfying constraints
                return []
            candidates = pet_candidates

        # 2. BHK matching & Dynamic Revision Limits
        if revision_request and revision_request.hard_limits:
            max_rent = revision_request.hard_limits.get("max_monthly_rent")
            max_deposit = revision_request.hard_limits.get("max_security_deposit")

            # Check exact BHK meeting budget
            exact_bhk = [item for item in candidates if item.get("bhk") == profile.home_bhk]
            budget_exact = [
                item for item in exact_bhk
                if (max_rent is None or (item.get("monthly_rent_inr") or 0) <= max_rent)
                and (max_deposit is None or (item.get("security_deposit_inr") or 0) <= max_deposit)
            ]
            if budget_exact:
                candidates = budget_exact
            else:
                # If no exact BHK meets budget, allow +/- 1 BHK in destination city that meets budget
                close_bhk = [
                    item for item in candidates
                    if abs((item.get("bhk") or 0) - profile.home_bhk) <= 1
                    and (max_rent is None or (item.get("monthly_rent_inr") or 0) <= max_rent)
                    and (max_deposit is None or (item.get("security_deposit_inr") or 0) <= max_deposit)
                ]
                if close_bhk:
                    candidates = close_bhk
                elif exact_bhk:
                    candidates = sorted(exact_bhk, key=lambda x: x.get("monthly_rent_inr") or 999999)[:1]
                else:
                    candidates = sorted(candidates, key=lambda x: x.get("monthly_rent_inr") or 999999)[:1]
        else:
            # Normal search: prefer exact BHK match, fallback to adjacent BHK if none available
            exact_bhk = [item for item in candidates if item.get("bhk") == profile.home_bhk]
            if exact_bhk:
                candidates = exact_bhk
            else:
                close_bhk = [item for item in candidates if abs((item.get("bhk") or 0) - profile.home_bhk) <= 1]
                if close_bhk:
                    candidates = close_bhk

        if not candidates:
            return []

        # 3. Multi-Attribute Utility Scoring within destination candidates
        def score_listing(item: Dict[str, Any]) -> float:
            safety_val = item.get("safety_score_index")
            safety_norm = (safety_val if safety_val is not None else 5.0) / 10.0
            
            commute_val = item.get("commute_to_workplace_mins")
            if commute_val is None:
                commute_val = item.get("commute_to_manyata_mins")
            commute = commute_val if commute_val is not None else 30
            max_commute = profile.max_commute_mins
            if revision_request and revision_request.soft_relaxations:
                max_commute += revision_request.soft_relaxations.get("allow_commute_increase_mins", 0)
            
            commute_norm = max(0.0, 1.0 - (commute / max(max_commute, 60)))
            rent_val = item.get("monthly_rent_inr")
            rent_inr = rent_val if rent_val is not None else 30000.0
            rent_norm = 1.0 - (rent_inr / 60000.0)

            # Weighting: Safety (40%), Commute (35%), Affordability (25%)
            return (0.40 * safety_norm) + (0.35 * commute_norm) + (0.25 * rent_norm)

        return sorted(candidates, key=score_listing, reverse=True)

    def _listing_to_proposal(self, item: Dict[str, Any], profile: RelocationProfile) -> HousingProposal:
        monthly_rent = float(item.get("monthly_rent_inr") or 30000.0)
        sec_dep = item.get("security_deposit_inr")
        security_deposit = float(sec_dep) if sec_dep is not None else (monthly_rent * 2.0)
        maint = item.get("society_maintenance_inr")
        society_maintenance = float(maint) if maint is not None else 0.0
        move_fee = item.get("move_in_fee_inr")
        move_in_fee = float(move_fee) if move_fee is not None else 0.0

        commute_val = item.get("commute_to_workplace_mins")
        if commute_val is None:
            commute_val = item.get("commute_to_manyata_mins")
        commute_mins = int(commute_val) if commute_val is not None else 30

        safety_val = item.get("safety_score_index")
        safety_score = float(safety_val) if safety_val is not None else 8.0

        total_upfront = security_deposit + monthly_rent + move_in_fee
        total_monthly = monthly_rent + society_maintenance

        return HousingProposal(
            property_id=item.get("property_id") or "SYNTH-BLR-001",
            title=item.get("title") or f"{item.get('neighborhood', 'Rental')} {item.get('bhk', profile.home_bhk)}BHK",
            city=item.get("city") or profile.destination_city,
            neighborhood=item.get("neighborhood") or "Central",
            bhk=int(item.get("bhk") or profile.home_bhk),
            monthly_rent_inr=monthly_rent,
            security_deposit_inr=security_deposit,
            society_maintenance_inr=society_maintenance,
            move_in_fee_inr=move_in_fee,
            pet_friendly=bool(item.get("pet_friendly", False)),
            commute_to_workplace_mins=commute_mins,
            safety_score_index=safety_score,
            datasource=item.get("datasource") or "SYNTHETIC_BENCHMARK_INR",
            property_type=item.get("property_type") or "Gated Society Apartment",
            is_verified=bool(item.get("is_verified", False)),
            total_upfront_outlay_inr=total_upfront,
            total_recurring_monthly_inr=total_monthly
        )

    def search_all(
        self,
        profile: RelocationProfile,
        revision_request: Optional[RevisionRequest] = None
    ) -> List[HousingProposal]:
        """Returns all matching properties in the destination city matching hard constraints."""
        candidates = self._filter_and_score_candidates(profile, revision_request)
        if profile.selected_property_id:
            if not any(c.get("property_id") == profile.selected_property_id for c in candidates):
                city_lower = profile.destination_city.strip().lower()
                chosen = next((c for c in self._listings if c.get("property_id") == profile.selected_property_id and c.get("city", "").strip().lower() == city_lower), None)
                if chosen:
                    candidates.insert(0, chosen)
        return [self._listing_to_proposal(c, profile) for c in candidates]

    def search(
        self,
        profile: RelocationProfile,
        revision_request: Optional[RevisionRequest] = None
    ) -> Optional[HousingProposal]:
        # Check if user explicitly selected a property
        if profile.selected_property_id:
            city_lower = profile.destination_city.strip().lower()
            chosen = next((c for c in self._listings if c.get("property_id") == profile.selected_property_id and c.get("city", "").strip().lower() == city_lower), None)
            if chosen:
                return self._listing_to_proposal(chosen, profile)

        candidates = self._filter_and_score_candidates(profile, revision_request)
        if not candidates:
            return None

        return self._listing_to_proposal(candidates[0], profile)
