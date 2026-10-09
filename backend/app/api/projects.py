import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.db.models import (
    User,
    RelocationProject,
    BudgetLineItem,
    ScheduleMilestone,
    AgentExecutionLog,
    DocumentRecord
)
from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.budget import BudgetAudit
from backend.app.schemas.document import DocumentAudit, FlaggedClause
from backend.app.schemas.schedule import SchedulePlan, MilestoneItem, DateConflict
from backend.app.schemas.arbitration import ConflictRecord, SynthesizedPlan, EscalationOption
from backend.app.agents.graph import run_relocation_workflow

router = APIRouter(prefix="/api/projects", tags=["Relocation Projects"])


# ============================================================================
# Request & Response Schemas
# ============================================================================

class CreateProjectRequest(BaseModel):
    user_email: str = Field("omika@example.com", description="User email identifier")
    user_name: str = Field("Omika Shrestha", description="User full name")
    origin_city: str = Field("Pune", description="Departure city")
    destination_city: str = Field("Bengaluru", description="Arrival city")
    target_move_date: str = Field("2026-11-05", description="Move date (YYYY-MM-DD)")
    upfront_budget_limit_inr: float = Field(150000.0, gt=0, description="Available upfront budget in INR")
    monthly_budget_limit_inr: float = Field(45000.0, gt=0, description="Max monthly recurring budget in INR")
    home_bhk: int = Field(2, ge=1, le=5, description="Home size category")
    has_pets: bool = Field(True, description="Traveling with pets")
    target_workplace: str = Field("Manyata Tech Park", description="Workplace destination")
    max_commute_mins: int = Field(40, ge=5, le=120, description="Max commute preference")


class ReplanProjectRequest(BaseModel):
    upfront_budget_limit_inr: Optional[float] = Field(None, gt=0)
    monthly_budget_limit_inr: Optional[float] = Field(None, gt=0)
    target_move_date: Optional[str] = None
    has_pets: Optional[bool] = None
    max_commute_mins: Optional[int] = None


class UserDecisionRequest(BaseModel):
    decision_action: str = Field(..., description="APPROVE, REJECT, SELECT_OPTION_A, or SELECT_OPTION_B")
    notes: Optional[str] = Field(None, description="Optional user commentary")


class ProjectSummaryResponse(BaseModel):
    project_id: str
    user_email: str
    user_name: str
    origin_city: str
    destination_city: str
    target_move_date: str
    upfront_budget_limit_inr: float
    monthly_budget_limit_inr: float
    home_bhk: int
    has_pets: bool
    status: str
    created_at: str


class ProjectDetailResponse(ProjectSummaryResponse):
    housing_proposal: Optional[HousingProposal] = None
    logistics_estimate: Optional[LogisticsEstimate] = None
    budget_audit: Optional[BudgetAudit] = None
    document_audit: Optional[DocumentAudit] = None
    schedule_plan: Optional[SchedulePlan] = None
    synthesized_plan: Optional[SynthesizedPlan] = None
    active_conflicts: List[ConflictRecord] = Field(default_factory=list)
    iteration_count: int = 1
    execution_logs: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Persistence Helpers
# ============================================================================

def _persist_workflow_artifacts(project: RelocationProject, state: RelocationState, db: Session):
    """Synchronizes state outputs into relational database tables."""
    project.status = state.status

    # 1. Update Line Items
    db.query(BudgetLineItem).filter_by(project_id=project.id).delete()
    if state.budget_audit:
        # Tier 1: One-time
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="ONE_TIME_RELOCATION",
            item_name="Packers & Movers Freight",
            amount_inr=state.budget_audit.one_time_costs.packers_movers_inr,
            is_confirmed=True
        ))
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="ONE_TIME_RELOCATION",
            item_name="Transit Insurance",
            amount_inr=state.budget_audit.one_time_costs.transit_insurance_inr,
            is_confirmed=True
        ))
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="ONE_TIME_RELOCATION",
            item_name="Travel Tickets (Flight/Train)",
            amount_inr=state.budget_audit.one_time_costs.travel_tickets_inr,
            is_confirmed=False
        ))
        # Tier 2: Housing Outlay
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="INITIAL_HOUSING_OUTLAY",
            item_name="Security Deposit",
            amount_inr=state.budget_audit.housing_outlay.security_deposit_inr,
            is_confirmed=False
        ))
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="INITIAL_HOUSING_OUTLAY",
            item_name="First Month Rent Advance",
            amount_inr=state.budget_audit.housing_outlay.advance_rent_inr,
            is_confirmed=False
        ))
        # Tier 3: Recurring Monthly
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="RECURRING_MONTHLY",
            item_name="Monthly Base Rent",
            amount_inr=state.budget_audit.recurring_monthly_costs.monthly_base_rent_inr,
            is_confirmed=False
        ))
        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="RECURRING_MONTHLY",
            item_name="Society Maintenance",
            amount_inr=state.budget_audit.recurring_monthly_costs.society_maintenance_inr,
            is_confirmed=False
        ))

    # 2. Update Milestones
    db.query(ScheduleMilestone).filter_by(project_id=project.id).delete()
    if state.schedule_plan:
        for m in state.schedule_plan.critical_path_milestones:
            db.add(ScheduleMilestone(
                project_id=project.id,
                task_name=m.task_name,
                target_date=m.target_date,
                prerequisites=m.prerequisites,
                is_critical_path=m.is_critical_path,
                is_completed=False
            ))

    # 3. Append Execution Logs
    for msg in state.history:
        db.add(AgentExecutionLog(
            project_id=project.id,
            agent_name=msg.sender,
            iteration=state.iteration_count,
            status=msg.message_type,
            input_payload={"recipient": msg.recipient},
            output_payload=msg.payload,
            conflict_notes=msg.content
        ))

    db.commit()


def _build_profile_from_project(project: RelocationProject) -> RelocationProfile:
    return RelocationProfile(
        user_id=project.user_id,
        origin_city=project.origin_city,
        destination_city=project.destination_city,
        target_move_date=project.target_move_date,
        upfront_budget_limit_inr=float(project.upfront_budget_limit),
        monthly_budget_limit_inr=float(project.monthly_budget_limit),
        home_bhk=project.home_bhk,
        has_pets=project.has_pets,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )



# ============================================================================
# Endpoints
# ============================================================================

@router.post("", response_model=ProjectSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db)):
    """Creates a new relocation project record and initializes the user."""
    user = db.query(User).filter_by(email=req.user_email).first()
    if not user:
        user = User(email=req.user_email, full_name=req.user_name)
        db.add(user)
        db.commit()
        db.refresh(user)

    project = RelocationProject(
        user_id=user.id,
        origin_city=req.origin_city,
        destination_city=req.destination_city,
        target_move_date=req.target_move_date,
        upfront_budget_limit=req.upfront_budget_limit_inr,
        monthly_budget_limit=req.monthly_budget_limit_inr,
        home_bhk=req.home_bhk,
        has_pets=req.has_pets,
        status="DRAFT"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectSummaryResponse(
        project_id=project.id,
        user_email=user.email,
        user_name=user.full_name,
        origin_city=project.origin_city,
        destination_city=project.destination_city,
        target_move_date=project.target_move_date,
        upfront_budget_limit_inr=project.upfront_budget_limit,
        monthly_budget_limit_inr=project.monthly_budget_limit,
        home_bhk=project.home_bhk,
        has_pets=project.has_pets,
        status=project.status,
        created_at=project.created_at.isoformat()
    )


@router.get("", response_model=List[ProjectSummaryResponse])
def list_projects(db: Session = Depends(get_db)):
    """Lists all stored relocation projects."""
    projects = db.query(RelocationProject).order_by(RelocationProject.created_at.desc()).all()
    return [
        ProjectSummaryResponse(
            project_id=p.id,
            user_email=p.user.email,
            user_name=p.user.full_name,
            origin_city=p.origin_city,
            destination_city=p.destination_city,
            target_move_date=p.target_move_date,
            upfront_budget_limit_inr=p.upfront_budget_limit,
            monthly_budget_limit_inr=p.monthly_budget_limit,
            home_bhk=p.home_bhk,
            has_pets=p.has_pets,
            status=p.status,
            created_at=p.created_at.isoformat()
        )
        for p in projects
    ]



@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieves full project status, plan details, line items, and agent execution logs."""
    project = db.query(RelocationProject).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    # Reconstruct state from latest execution log if available
    profile = _build_profile_from_project(project)
    
    # Query latest logs
    logs = db.query(AgentExecutionLog).filter_by(project_id=project.id).order_by(AgentExecutionLog.created_at.asc()).all()
    serialized_logs = [
        {
            "agent_name": log.agent_name,
            "iteration": log.iteration,
            "status": log.status,
            "notes": log.conflict_notes,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]

    # Run quick evaluation of state to construct detail response if already planned
    init_state = RelocationState(project_id=project.id, profile=profile)
    final_state = run_relocation_workflow(init_state)

    return ProjectDetailResponse(
        project_id=project.id,
        user_email=project.user.email,
        user_name=project.user.full_name,
        origin_city=project.origin_city,
        destination_city=project.destination_city,
        target_move_date=project.target_move_date,
        upfront_budget_limit_inr=project.upfront_budget_limit,
        monthly_budget_limit_inr=project.monthly_budget_limit,
        home_bhk=project.home_bhk,
        has_pets=project.has_pets,
        status=project.status,
        created_at=project.created_at.isoformat(),
        housing_proposal=final_state.housing_proposal,
        logistics_estimate=final_state.logistics_estimate,
        budget_audit=final_state.budget_audit,
        document_audit=final_state.document_audit,
        schedule_plan=final_state.schedule_plan,
        synthesized_plan=final_state.synthesized_plan,
        active_conflicts=final_state.active_conflicts,
        iteration_count=final_state.iteration_count,
        execution_logs=serialized_logs
    )


@router.post("/{project_id}/run", response_model=ProjectDetailResponse)
def run_project_planning(project_id: str, db: Session = Depends(get_db)):
    """Triggers the multi-agent LangGraph workflow for the specified project."""
    project = db.query(RelocationProject).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    profile = _build_profile_from_project(project)
    init_state = RelocationState(project_id=project.id, profile=profile)

    # Check if a document record was uploaded for this project
    doc_record = db.query(DocumentRecord).filter_by(project_id=project.id).first()
    if doc_record:
        init_state.document_audit = DocumentAudit(
            document_filename=doc_record.file_name,
            parse_status="SUCCESS",
            extracted_monthly_rent_inr=doc_record.extracted_terms.get("monthly_rent_inr") if doc_record.extracted_terms else None,
            extracted_security_deposit_inr=doc_record.extracted_terms.get("security_deposit_inr") if doc_record.extracted_terms else None,
            flagged_clauses_for_review=[FlaggedClause(**c) for c in (doc_record.flagged_clauses or [])],
            disclaimer=doc_record.disclaimer
        )

    # Execute multi-agent reasoning
    final_state = run_relocation_workflow(init_state)

    # Persist outputs in DB
    _persist_workflow_artifacts(project, final_state, db)

    return get_project(project_id, db)


@router.post("/{project_id}/replan", response_model=ProjectDetailResponse)
def replan_project(project_id: str, req: ReplanProjectRequest, db: Session = Depends(get_db)):
    """Updates user budget or requirements and triggers dynamic multi-agent replanning."""
    project = db.query(RelocationProject).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    # Apply updates
    if req.upfront_budget_limit_inr is not None:
        project.upfront_budget_limit = req.upfront_budget_limit_inr
    if req.monthly_budget_limit_inr is not None:
        project.monthly_budget_limit = req.monthly_budget_limit_inr
    if req.target_move_date is not None:
        project.target_move_date = req.target_move_date
    if req.has_pets is not None:
        project.has_pets = req.has_pets

    db.commit()

    # Re-run reasoning engine
    return run_project_planning(project_id, db)


@router.post("/{project_id}/decide", response_model=ProjectDetailResponse)
def user_decision(project_id: str, req: UserDecisionRequest, db: Session = Depends(get_db)):
    """Resolves human-in-the-loop choices or final plan approval."""
    project = db.query(RelocationProject).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    action = req.decision_action.strip().upper()

    if action == "APPROVE":
        project.status = "APPROVED"
        db.commit()
    elif action == "REJECT":
        project.status = "REJECTED"
        db.commit()
    elif action == "SELECT_OPTION_A":
        # User accepted Option A: expand upfront budget allowance
        detail = get_project(project_id, db)
        if detail.synthesized_plan and detail.synthesized_plan.escalation_options:
            opt_a = detail.synthesized_plan.escalation_options[0]
            project.upfront_budget_limit = opt_a.upfront_cost_inr
            db.commit()
            return run_project_planning(project_id, db)
        else:
            project.status = "APPROVED"
            db.commit()
    elif action == "SELECT_OPTION_B":
        # User accepted Option B: compromise on transit/commute
        project.status = "APPROVED"
        db.commit()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported decision action '{req.decision_action}'.")

    return get_project(project_id, db)
