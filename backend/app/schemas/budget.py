from typing import Dict
from pydantic import BaseModel, Field, model_validator


class OneTimeRelocationCosts(BaseModel):
    packers_movers_inr: float = Field(..., ge=0, description="Base packing, loading, and freight transit cost")
    transit_insurance_inr: float = Field(0.0, ge=0, description="Transit goods insurance coverage")
    travel_tickets_inr: float = Field(0.0, ge=0, description="Flight/train/bus travel fares for relocating household")
    packing_supplies_inr: float = Field(0.0, ge=0, description="Boxes, bubble wrap, and crating charges")
    total_one_time_inr: float = Field(0.0, ge=0, description="Sum of one-time physical moving costs")

    @model_validator(mode="after")
    def compute_total(self) -> "OneTimeRelocationCosts":
        calculated = (
            self.packers_movers_inr
            + self.transit_insurance_inr
            + self.travel_tickets_inr
            + self.packing_supplies_inr
        )
        self.total_one_time_inr = round(calculated, 2)
        return self


class InitialHousingOutlay(BaseModel):
    security_deposit_inr: float = Field(..., ge=0, description="Rental security deposit (e.g. 2 months rent)")
    advance_rent_inr: float = Field(..., ge=0, description="First month rent paid upfront at signing")
    move_in_fee_inr: float = Field(0.0, ge=0, description="Society move-in onboarding / registration fee")
    total_housing_outlay_inr: float = Field(0.0, ge=0, description="Total upfront capital required for housing lease")

    @model_validator(mode="after")
    def compute_total(self) -> "InitialHousingOutlay":
        calculated = (
            self.security_deposit_inr
            + self.advance_rent_inr
            + self.move_in_fee_inr
        )
        self.total_housing_outlay_inr = round(calculated, 2)
        return self


class RecurringMonthlyCosts(BaseModel):
    monthly_base_rent_inr: float = Field(..., ge=0, description="Base monthly house rent")
    society_maintenance_inr: float = Field(0.0, ge=0, description="Monthly society maintenance charge")
    estimated_utilities_inr: float = Field(..., ge=0, description="Monthly electricity, water, LPG, and internet")
    estimated_commute_inr: float = Field(..., ge=0, description="Monthly metro, bus, or fuel commuting expenses")
    total_recurring_monthly_inr: float = Field(0.0, ge=0, description="Total estimated recurring monthly cost of living")

    @model_validator(mode="after")
    def compute_total(self) -> "RecurringMonthlyCosts":
        calculated = (
            self.monthly_base_rent_inr
            + self.society_maintenance_inr
            + self.estimated_utilities_inr
            + self.estimated_commute_inr
        )
        self.total_recurring_monthly_inr = round(calculated, 2)
        return self


class BudgetAudit(BaseModel):
    # Tier 1 & Tier 2: Upfront Capital Analysis
    one_time_costs: OneTimeRelocationCosts
    housing_outlay: InitialHousingOutlay
    total_upfront_outlay_inr: float = Field(0.0, ge=0)
    upfront_budget_limit_inr: float = Field(..., gt=0)
    upfront_variance_inr: float = Field(0.0, description="Positive = surplus, Negative = deficit")
    upfront_violation: bool = Field(False, description="True if total_upfront_outlay exceeds upfront_budget_limit")

    # Tier 3: Monthly Operational Living Analysis
    recurring_monthly_costs: RecurringMonthlyCosts
    monthly_budget_limit_inr: float = Field(..., gt=0)
    monthly_variance_inr: float = Field(0.0, description="Positive = surplus, Negative = deficit")
    monthly_violation: bool = Field(False, description="True if total_recurring_monthly exceeds monthly_budget_limit")

    # Summary Flags
    overall_financially_feasible: bool = Field(False)
    summary_notes: str = Field("", description="Human-readable financial audit commentary")

    @model_validator(mode="after")
    def evaluate_audit(self) -> "BudgetAudit":
        # Calculate upfront total & variance
        self.total_upfront_outlay_inr = round(
            self.one_time_costs.total_one_time_inr + self.housing_outlay.total_housing_outlay_inr, 2
        )
        self.upfront_variance_inr = round(
            self.upfront_budget_limit_inr - self.total_upfront_outlay_inr, 2
        )
        self.upfront_violation = self.upfront_variance_inr < 0.0

        # Calculate monthly variance
        self.monthly_variance_inr = round(
            self.monthly_budget_limit_inr - self.recurring_monthly_costs.total_recurring_monthly_inr, 2
        )
        self.monthly_violation = self.monthly_variance_inr < 0.0

        # Overall feasibility
        self.overall_financially_feasible = (not self.upfront_violation) and (not self.monthly_violation)

        notes = []
        if self.upfront_violation:
            notes.append(f"Upfront deficit of ₹{abs(self.upfront_variance_inr):,.2f}.")
        else:
            notes.append(f"Upfront surplus buffer of ₹{self.upfront_variance_inr:,.2f}.")

        if self.monthly_violation:
            notes.append(f"Monthly recurring deficit of ₹{abs(self.monthly_variance_inr):,.2f}.")
        else:
            notes.append(f"Monthly recurring headroom of ₹{self.monthly_variance_inr:,.2f}.")

        self.summary_notes = " ".join(notes)
        return self
