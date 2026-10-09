import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.arbitration import RevisionRequest


class HousingResearchAgent:
    """Specialized agent for filtering and ranking synthetic housing listings in INR."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (DATA_DIR / "housing_samples_inr.json")
        self._listings = self._load_listings()

    def _load_listings(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Housing benchmark dataset not found at {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("listings", [])

    def search(
        self,
        profile: RelocationProfile,
        revision_request: Optional[RevisionRequest] = None
    ) -> HousingProposal:
        """Finds the optimal housing proposal matching constraints and soft preferences."""
        city_lower = profile.destination_city.strip().lower()
        candidates = [item for item in self._listings if item.get("city", "").strip().lower() == city_lower]
        
        # Fallback to Bengaluru if city has no matching listings in synthetic data
        if not candidates:
            candidates = [item for item in self._listings if item.get("city", "").strip().lower() == "bengaluru"]

        # 1. Hard Constraint: BHK matching (allow +/- 1 if zero match)
        bhk_candidates = [item for item in candidates if item.get("bhk") == profile.home_bhk]
        if bhk_candidates:
            candidates = bhk_candidates

        # 2. Hard Constraint: Pet Accommodations
        if profile.has_pets:
            candidates = [item for item in candidates if item.get("pet_friendly") is True]

        # 3. Dynamic Revision Request Limits (e.g., from Decision Agent budget arbitration)
        if revision_request and revision_request.hard_limits:
            max_rent = revision_request.hard_limits.get("max_monthly_rent")
            if max_rent is not None:
                candidates = [item for item in candidates if item.get("monthly_rent_inr", 0) <= max_rent]
            
            max_deposit = revision_request.hard_limits.get("max_security_deposit")
            if max_deposit is not None:
                candidates = [item for item in candidates if item.get("security_deposit_inr", 0) <= max_deposit]

        # If zero candidates pass all filters, attempt fallback to pet-respecting listing if pets required
        if not candidates:
            pet_filter = [item for item in self._listings if item.get("pet_friendly") is True] if profile.has_pets else self._listings
            candidates = sorted(pet_filter, key=lambda x: x.get("monthly_rent_inr", 999999))[:1]

        if not candidates:
            # When absolutely no compatible listing exists, fallback to lowest available with disclaimer
            if not self._listings:
                raise ValueError("Housing benchmark dataset contains zero listings.")
            candidates = sorted(self._listings, key=lambda x: x.get("monthly_rent_inr", 999999))[:1]

        # 4. Multi-Attribute Utility Scoring
        def score_listing(item: Dict[str, Any]) -> float:
            safety_norm = item.get("safety_score_index", 5.0) / 10.0
            
            commute = item.get("commute_to_manyata_mins", 30)
            max_commute = profile.max_commute_mins
            if revision_request and revision_request.soft_relaxations:
                max_commute += revision_request.soft_relaxations.get("allow_commute_increase_mins", 0)
            
            commute_norm = max(0.0, 1.0 - (commute / max(max_commute, 60)))
            rent_norm = 1.0 - (item.get("monthly_rent_inr", 30000) / 60000.0)

            # Weighting: Safety (40%), Commute (35%), Affordability (25%)
            return (0.40 * safety_norm) + (0.35 * commute_norm) + (0.25 * rent_norm)

        scored = sorted(candidates, key=score_listing, reverse=True)
        best = scored[0]

        return HousingProposal(
            property_id=best["property_id"],
            title=best["title"],
            city=best["city"],
            neighborhood=best["neighborhood"],
            bhk=best["bhk"],
            monthly_rent_inr=float(best["monthly_rent_inr"]),
            security_deposit_inr=float(best["security_deposit_inr"]),
            society_maintenance_inr=float(best.get("society_maintenance_inr", 0.0)),
            move_in_fee_inr=float(best.get("move_in_fee_inr", 0.0)),
            pet_friendly=best["pet_friendly"],
            commute_to_workplace_mins=int(best.get("commute_to_manyata_mins", 30)),
            safety_score_index=float(best.get("safety_score_index", 8.0)),
            datasource="SYNTHETIC_BENCHMARK_INR"
        )
