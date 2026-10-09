from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.budget import BudgetAudit
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.document import DocumentAudit
from backend.app.schemas.schedule import SchedulePlan
from backend.app.schemas.arbitration import ConflictRecord, RevisionRequest, SynthesizedPlan


class RelocationProfile(BaseModel):
    user_id: str = Field(..., description="Unique user reference")
    origin_city: str = Field("Pune", description="Origin city")
    destination_city: str = Field("Bengaluru", description="Destination city")
    target_move_date: str = Field(..., description="Target relocation completion date (YYYY-MM-DD)")
    upfront_budget_limit_inr: float = Field(..., gt=0, description="Available capital for moving + deposit")
    monthly_budget_limit_inr: float = Field(..., gt=0, description="Monthly living & rent budget ceiling")
    home_bhk: int = Field(2, ge=1, le=5, description="Home size category")
    has_pets: bool = Field(False, description="Presence of household pets")
    target_workplace: str = Field("Manyata Tech Park", description="Workplace locality for commute tracking")
    max_commute_mins: int = Field(45, ge=5, le=120, description="Soft preference for maximum commute")


class AgentMessage(BaseModel):
    sender: str = Field(..., description="Originating agent name")
    recipient: str = Field(..., description="Target agent or 'ALL'")
    message_type: str = Field(..., description="PROPOSAL, REVISION_REQUEST, AUDIT_PASS, AUDIT_FAIL, SYNTHESIS")
    content: str = Field(..., description="Summary text description")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured Pydantic model dictionary")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RelocationState(BaseModel):
    project_id: str = Field(..., description="Relocation project UUID")
    profile: RelocationProfile
    
    # Domain Agent Proposals
    housing_proposal: Optional[HousingProposal] = None
    logistics_estimate: Optional[LogisticsEstimate] = None
    budget_audit: Optional[BudgetAudit] = None
    document_audit: Optional[DocumentAudit] = None
    schedule_plan: Optional[SchedulePlan] = None

    # Arbitration & Control Loop
    active_conflicts: List[ConflictRecord] = Field(default_factory=list)
    active_revision_request: Optional[RevisionRequest] = None
    synthesized_plan: Optional[SynthesizedPlan] = None
    
    # State tracking
    iteration_count: int = Field(1, description="Current arbitration cycle (1, 2, or max 3)")
    status: str = Field(
        "INITIALIZED",
        description="INITIALIZED, PROPOSING, AUDITING, REVISING, CONSENSUS_REACHED, AWAITING_USER_DECISION, FAILED"
    )
    history: List[AgentMessage] = Field(default_factory=list)
