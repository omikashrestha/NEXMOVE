from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ConflictRecord(BaseModel):
    conflict_id: str = Field(..., description="Unique conflict identifier")
    source_agent: str = Field(..., description="Agent that detected or caused the constraint issue")
    constraint_category: str = Field(..., description="HARD_CONSTRAINT or SOFT_PREFERENCE")
    metric_name: str = Field(..., description="e.g. upfront_budget_limit, pet_friendly, delivery_date")
    description: str = Field(..., description="Human-readable explanation of the clash")
    severity: str = Field("HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    delta_value: Optional[float] = Field(None, description="Numeric shortfall or overshoot if applicable")


class RevisionRequest(BaseModel):
    target_agent: str = Field(..., description="Agent receiving the structured feedback directive")
    conflict_type: str = Field(..., description="e.g. UPFRONT_BUDGET_OVERRUN, PET_RESTRICTION, DATE_CLASH")
    hard_limits: Dict[str, Any] = Field(default_factory=dict, description="Non-negotiable parameters for next search")
    soft_relaxations: Dict[str, Any] = Field(default_factory=dict, description="Acceptable compromises to explore")
    rationale: str = Field(..., description="Decision Agent explanation for why this revision was issued")


class EscalationOption(BaseModel):
    option_id: str = Field(..., description="A or B")
    title: str = Field(..., description="Summary headline for the choice")
    trade_off_summary: str = Field(..., description="Clear explanation of compromise (e.g. higher budget vs longer commute)")
    upfront_cost_inr: float = Field(..., ge=0)
    monthly_cost_inr: float = Field(..., ge=0)
    commute_mins: int = Field(..., ge=0)


class SynthesizedPlan(BaseModel):
    plan_status: str = Field(..., description="CONSENSUS_REACHED, AWAITING_USER_DECISION, or REJECTED")
    iteration_count: int = Field(1, ge=1, le=3, description="Number of arbitration cycles performed (capped at 2 revisions)")
    recommended_housing_id: Optional[str] = Field(None)
    recommended_housing_title: Optional[str] = Field(None)
    total_upfront_outlay_inr: float = Field(..., ge=0)
    total_recurring_monthly_inr: float = Field(..., ge=0)
    upfront_buffer_inr: float = Field(0.0)
    monthly_headroom_inr: float = Field(0.0)
    transit_pickup_date: Optional[str] = Field(None)
    transit_delivery_date: Optional[str] = Field(None)
    trade_offs_resolved: List[str] = Field(default_factory=list, description="Explanations of automated compromises made")
    user_advisories: List[str] = Field(default_factory=list, description="Advisories (e.g. flagged lease clauses) for human sign-off")
    escalation_options: List[EscalationOption] = Field(default_factory=list, description="Provided when human must resolve conflict")
