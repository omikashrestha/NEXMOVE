from typing import Optional
from pydantic import BaseModel, Field, model_validator


class LogisticsQuery(BaseModel):
    origin_city: str = Field(..., description="Relocation starting city (e.g. Pune)")
    destination_city: str = Field(..., description="Relocation destination city (e.g. Bengaluru)")
    target_pickup_date: str = Field(..., description="Desired moving pickup date (YYYY-MM-DD)")
    home_bhk: int = Field(2, ge=1, le=5, description="Home configuration / volume category")
    include_vehicle_shipping: bool = Field(False, description="Ship two-wheeler or car")
    include_transit_insurance: bool = Field(True, description="Opt-in for transit loss/damage coverage")


class LogisticsEstimate(BaseModel):
    route: str = Field(..., description="Route description (e.g. Pune -> Bengaluru)")
    distance_km: int = Field(..., ge=1, description="Estimated highway transit distance in km")
    vehicle_type: str = Field(..., description="Recommended carrier vehicle (e.g. 14ft Dedicated Container)")
    base_packers_movers_quote_inr: float = Field(..., ge=0, description="Base packing, labor, loading and transit charge")
    vehicle_shipping_inr: float = Field(0.0, ge=0, description="Specialized vehicle transit fee")
    transit_insurance_inr: float = Field(0.0, ge=0, description="Transit insurance fee")
    total_logistics_inr: float = Field(0.0, ge=0, description="Total one-time moving logistics estimate")
    estimated_transit_days: int = Field(..., ge=1, description="Estimated door-to-door transit duration in days")
    recommended_pickup_date: str = Field(..., description="Scheduled loading date (YYYY-MM-DD)")
    estimated_delivery_date: str = Field(..., description="Earliest delivery arrival date (YYYY-MM-DD)")
    carrier_benchmark_ref: str = Field("Sample Interstate Carrier Grade-A", description="Benchmark provider reference")
    disclaimer: str = Field(
        "Synthetic benchmark tariff for university prototype demonstration.",
        description="Non-commercial prototype disclaimer"
    )

    @model_validator(mode="after")
    def compute_total(self) -> "LogisticsEstimate":
        self.total_logistics_inr = round(
            self.base_packers_movers_quote_inr + self.vehicle_shipping_inr + self.transit_insurance_inr, 2
        )
        return self
