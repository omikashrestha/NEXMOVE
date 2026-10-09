from typing import Optional
from pydantic import BaseModel, Field


class HousingQuery(BaseModel):
    destination_city: str = Field(..., description="Target destination city (e.g., Bengaluru)")
    target_workplace: Optional[str] = Field("Manyata Tech Park", description="Workplace or reference location for commute estimation")
    preferred_bhk: int = Field(2, ge=1, le=5, description="Number of bedrooms (BHK)")
    max_monthly_rent_inr: float = Field(..., gt=0, description="Upper bound for base monthly rent in INR")
    pets_allowed_required: bool = Field(False, description="Whether pet accommodation is mandatory")
    max_commute_minutes: int = Field(45, ge=5, le=120, description="Max acceptable one-way commute duration")


class HousingProposal(BaseModel):
    property_id: str = Field(..., description="Unique property identifier (e.g. BLR-HSR-204)")
    title: str = Field(..., description="Display title for the rental property")
    city: str = Field("Bengaluru", description="City location")
    neighborhood: str = Field(..., description="Locality / neighborhood name")
    bhk: int = Field(..., ge=1, description="Bedrooms count")
    monthly_rent_inr: float = Field(..., gt=0, description="Monthly base rent in INR")
    security_deposit_inr: float = Field(..., ge=0, description="Security deposit in INR")
    society_maintenance_inr: float = Field(0.0, ge=0, description="Monthly society maintenance charge in INR")
    move_in_fee_inr: float = Field(0.0, ge=0, description="One-time society move-in fee in INR")
    pet_friendly: bool = Field(..., description="Whether pets are explicitly permitted")
    commute_to_workplace_mins: int = Field(..., ge=0, description="Estimated metro/transit commute in minutes")
    safety_score_index: float = Field(..., ge=1.0, le=10.0, description="Safety index from 1.0 to 10.0")
    datasource: str = Field("SAMPLE_BENCHMARK_INR", description="Source indicator for synthetic evaluation data")
