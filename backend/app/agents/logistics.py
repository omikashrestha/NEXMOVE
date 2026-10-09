import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.arbitration import RevisionRequest


class LogisticsAgent:
    """Specialized agent for freight tariffs, vehicle sizing, and transit timing in INR."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (DATA_DIR / "logistics_tariffs_inr.json")
        self._tariffs = self._load_tariffs()

    def _load_tariffs(self) -> Dict[str, Any]:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Logistics tariff dataset not found at {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def estimate(
        self,
        profile: RelocationProfile,
        revision_request: Optional[RevisionRequest] = None
    ) -> LogisticsEstimate:
        """Computes comprehensive moving logistics and transit timelines."""
        origin = profile.origin_city.strip().title()
        destination = profile.destination_city.strip().title()

        corridors = self._tariffs.get("corridors", [])
        if not corridors:
            raise ValueError("Logistics tariff dataset contains zero corridor entries.")

        corridor = next(
            (c for c in corridors if c["origin"].lower() == origin.lower() and c["destination"].lower() == destination.lower()),
            None
        )

        # Fallback to standard Pune -> Bengaluru corridor if pair not listed
        if not corridor:
            corridor = corridors[0]

        distance_km = corridor.get("distance_km", 840)
        transit_days = corridor.get("standard_transit_days", 3)
        bhk_key = str(min(max(profile.home_bhk, 1), 3))
        bhk_tariff = corridor.get("bhk_tariffs", {}).get(bhk_key, {})

        vehicle_type = bhk_tariff.get("vehicle_type", "14ft Dedicated Container")
        base_freight = float(bhk_tariff.get("base_packers_movers_quote_inr", 38000.0))
        insurance = float(bhk_tariff.get("transit_insurance_standard_inr", 2000.0))

        # Check for economy shared-container adjustment if budget revision was requested
        if revision_request and revision_request.hard_limits.get("prefer_economy_freight"):
            base_freight = round(base_freight * 0.82, 2)  # 18% savings
            transit_days += 2  # Longer consolidation transit
            vehicle_type = f"{vehicle_type} (Shared Economy Transit)"

        # Check for delivery offset if schedule clash was flagged
        offset_days = 0
        if revision_request and revision_request.hard_limits.get("adjust_delivery_offset_days"):
            offset_days = int(revision_request.hard_limits["adjust_delivery_offset_days"])

        # Pet shipping specialty add-on
        specialty_fee = 0.0
        if profile.has_pets:
            specialty_fee = float(corridor.get("addons", {}).get("pet_relocation_specialty_inr", 8000.0))

        # Date calculations
        try:
            target_date = datetime.strptime(profile.target_move_date, "%Y-%m-%d")
        except ValueError:
            target_date = datetime.now() + timedelta(days=20)

        pickup_date = target_date - timedelta(days=transit_days) + timedelta(days=offset_days)
        delivery_date = target_date + timedelta(days=offset_days)


        return LogisticsEstimate(
            route=f"{corridor['origin']} -> {corridor['destination']}",
            distance_km=distance_km,
            vehicle_type=vehicle_type,
            base_packers_movers_quote_inr=base_freight,
            vehicle_shipping_inr=specialty_fee,
            transit_insurance_inr=insurance,
            estimated_transit_days=transit_days,
            recommended_pickup_date=pickup_date.strftime("%Y-%m-%d"),
            estimated_delivery_date=delivery_date.strftime("%Y-%m-%d"),
            carrier_benchmark_ref=f"Synthetic Benchmark Carrier ({corridor.get('corridor_id', 'IN-CORR')})",
            disclaimer="Synthetic benchmark estimate for university prototype demonstration."
        )
