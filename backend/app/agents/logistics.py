import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.arbitration import RevisionRequest

# Standard interstate road highway distances (km) between major Indian hubs
INDIAN_HIGHWAY_DISTANCES = {
    ("pune", "kolkata"): 1650,
    ("kolkata", "pune"): 1650,
    ("pune", "bengaluru"): 840,
    ("bengaluru", "pune"): 840,
    ("mumbai", "bengaluru"): 980,
    ("bengaluru", "mumbai"): 980,
    ("hyderabad", "bengaluru"): 570,
    ("bengaluru", "hyderabad"): 570,
    ("delhi", "bengaluru"): 2150,
    ("bengaluru", "delhi"): 2150,
    ("delhi", "kolkata"): 1530,
    ("kolkata", "delhi"): 1530,
    ("mumbai", "kolkata"): 1960,
    ("kolkata", "mumbai"): 1960,
    ("bengaluru", "kolkata"): 1870,
    ("kolkata", "bengaluru"): 1870,
    ("pune", "mumbai"): 150,
    ("mumbai", "pune"): 150,
    ("pune", "hyderabad"): 560,
    ("hyderabad", "pune"): 560,
    ("delhi", "mumbai"): 1420,
    ("mumbai", "delhi"): 1420,
    ("chennai", "bengaluru"): 350,
    ("bengaluru", "chennai"): 350,
}


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
        """Computes moving logistics strictly using user's actual origin and destination cities."""
        origin = profile.origin_city.strip().title()
        destination = profile.destination_city.strip().title()
        bhk_key = str(min(max(profile.home_bhk, 1), 3))

        corridors = self._tariffs.get("corridors", [])
        corridor = next(
            (c for c in corridors if c.get("origin", "").lower() == origin.lower() and c.get("destination", "").lower() == destination.lower()),
            None
        )

        if corridor:
            distance_km = int(corridor.get("distance_km", 840))
            transit_days = int(corridor.get("standard_transit_days", 3))
            bhk_tariff = corridor.get("bhk_tariffs", {}).get(bhk_key, {})
            vehicle_type = bhk_tariff.get("vehicle_type", "14ft Dedicated Container")
            base_freight = float(bhk_tariff.get("base_packers_movers_quote_inr", 38000.0))
            insurance = float(bhk_tariff.get("transit_insurance_standard_inr", 2000.0))
            specialty_fee = float(corridor.get("addons", {}).get("pet_relocation_specialty_inr", 8000.0)) if profile.has_pets else 0.0
            corridor_id = corridor.get("corridor_id", "IN-CORR")
        else:
            # Dynamically compute realistic tariff based on actual distance
            pair = (origin.lower(), destination.lower())
            distance_km = INDIAN_HIGHWAY_DISTANCES.get(pair, 1200)
            transit_days = max(2, math.ceil(distance_km / 420.0))
            
            if profile.home_bhk == 1:
                vehicle_type = "Tata 407 (10ft Covered)"
                base_freight = round((distance_km * 22.0) + 12000.0, -2)
                insurance = round(base_freight * 0.05, -2)
            elif profile.home_bhk == 3:
                vehicle_type = "17ft Large Container"
                base_freight = round((distance_km * 38.0) + 20000.0, -2)
                insurance = round(base_freight * 0.055, -2)
            else:
                vehicle_type = "14ft Dedicated Container"
                base_freight = round((distance_km * 30.0) + 16000.0, -2)
                insurance = round(base_freight * 0.05, -2)

            specialty_fee = 8500.0 if profile.has_pets else 0.0
            corridor_id = f"{origin[:3].upper()}-{destination[:3].upper()}"

        # Check for economy shared-container adjustment if budget revision was requested
        if revision_request and revision_request.hard_limits.get("prefer_economy_freight"):
            base_freight = round(base_freight * 0.82, 2)  # 18% savings
            transit_days += 2  # Longer consolidation transit
            vehicle_type = f"{vehicle_type} (Shared Economy Transit)"

        # Check for delivery offset if schedule clash was flagged
        offset_days = 0
        if revision_request and revision_request.hard_limits.get("adjust_delivery_offset_days"):
            offset_days = int(revision_request.hard_limits["adjust_delivery_offset_days"])

        # Scheduled loading and arrival dates
        try:
            target_date = datetime.strptime(profile.target_move_date, "%Y-%m-%d")
        except ValueError:
            target_date = datetime.now() + timedelta(days=20)

        pickup_date = target_date - timedelta(days=transit_days) + timedelta(days=offset_days)
        delivery_date = target_date + timedelta(days=offset_days)

        return LogisticsEstimate(
            route=f"{origin} -> {destination}",
            distance_km=distance_km,
            vehicle_type=vehicle_type,
            base_packers_movers_quote_inr=base_freight,
            vehicle_shipping_inr=specialty_fee,
            transit_insurance_inr=insurance,
            estimated_transit_days=transit_days,
            recommended_pickup_date=pickup_date.strftime("%Y-%m-%d"),
            estimated_delivery_date=delivery_date.strftime("%Y-%m-%d"),
            carrier_benchmark_ref=f"Synthetic Benchmark Carrier ({corridor_id})",
            disclaimer="Synthetic benchmark estimate for university prototype demonstration. Not a live commercial quote or confirmed booking."
        )
