import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.arbitration import RevisionRequest


_CUSTOM_LISTINGS: Dict[str, Dict[str, Any]] = {}


class HousingResearchAgent:
    """Specialized agent for filtering and ranking synthetic housing listings in INR."""

    @classmethod
    def register_custom_listing(cls, listing: Dict[str, Any]):
        """Registers a user-provided custom property listing."""
        _CUSTOM_LISTINGS[listing["property_id"]] = listing

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (DATA_DIR / "housing_samples_inr.json")
        self._listings = self._load_listings()

    def _load_listings(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Housing benchmark dataset not found at {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        base_listings = data.get("listings", [])
        return base_listings + list(_CUSTOM_LISTINGS.values())

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
        return [self._listing_to_proposal(c, profile) for c in candidates]

    def search(
        self,
        profile: RelocationProfile,
        revision_request: Optional[RevisionRequest] = None
    ) -> Optional[HousingProposal]:
        candidates = self._filter_and_score_candidates(profile, revision_request)
        if not candidates:
            return None

        # Check if user explicitly selected a property
        if profile.selected_property_id:
            chosen = next((c for c in candidates if c.get("property_id") == profile.selected_property_id), None)
            if not chosen:
                city_lower = profile.destination_city.strip().lower()
                chosen = next((c for c in self._listings if c.get("property_id") == profile.selected_property_id and c.get("city", "").strip().lower() == city_lower), None)
            if chosen:
                return self._listing_to_proposal(chosen, profile)

        return self._listing_to_proposal(candidates[0], profile)
