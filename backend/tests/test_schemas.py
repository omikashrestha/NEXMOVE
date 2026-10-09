import pytest
from pydantic import ValidationError

from backend.app.schemas.budget import (
    OneTimeRelocationCosts,
    InitialHousingOutlay,
    RecurringMonthlyCosts,
    BudgetAudit
)
from backend.app.schemas.housing import HousingQuery, HousingProposal
from backend.app.schemas.logistics import LogisticsQuery, LogisticsEstimate
from backend.app.schemas.document import FlaggedClause, DocumentAudit
from backend.app.schemas.schedule import MilestoneItem, SchedulePlan, DateConflict
from backend.app.schemas.arbitration import (
    ConflictRecord,
    RevisionRequest,
    EscalationOption,
    SynthesizedPlan
)
from backend.app.schemas.state import RelocationProfile, RelocationState, AgentMessage


def test_one_time_costs_auto_computation():
    costs = OneTimeRelocationCosts(
        packers_movers_inr=38000.0,
        transit_insurance_inr=2000.0,
        travel_tickets_inr=5000.0,
        packing_supplies_inr=1500.0
    )
    assert costs.total_one_time_inr == 46500.0


def test_initial_housing_outlay_auto_computation():
    outlay = InitialHousingOutlay(
        security_deposit_inr=60000.0,
        advance_rent_inr=30000.0,
        move_in_fee_inr=2000.0
    )
    assert outlay.total_housing_outlay_inr == 92000.0


def test_recurring_monthly_auto_computation():
    recurring = RecurringMonthlyCosts(
        monthly_base_rent_inr=30000.0,
        society_maintenance_inr=3500.0,
        estimated_utilities_inr=3500.0,
        estimated_commute_inr=2500.0
    )
    assert recurring.total_recurring_monthly_inr == 39500.0


def test_budget_audit_feasible_scenario():
    one_time = OneTimeRelocationCosts(
        packers_movers_inr=38000.0,
        transit_insurance_inr=2000.0,
        travel_tickets_inr=5000.0
    )
    outlay = InitialHousingOutlay(
        security_deposit_inr=60000.0,
        advance_rent_inr=30000.0
    )
    recurring = RecurringMonthlyCosts(
        monthly_base_rent_inr=30000.0,
        society_maintenance_inr=3500.0,
        estimated_utilities_inr=3500.0,
        estimated_commute_inr=2000.0
    )

    audit = BudgetAudit(
        one_time_costs=one_time,
        housing_outlay=outlay,
        upfront_budget_limit_inr=150000.0,
        recurring_monthly_costs=recurring,
        monthly_budget_limit_inr=45000.0
    )

    # 45,000 + 90,000 = 135,000 upfront outlay (under 150,000)
    assert audit.total_upfront_outlay_inr == 135000.0
    assert audit.upfront_variance_inr == 15000.0
    assert audit.upfront_violation is False

    # 39,000 recurring (under 45,000)
    assert audit.recurring_monthly_costs.total_recurring_monthly_inr == 39000.0
    assert audit.monthly_variance_inr == 6000.0
    assert audit.monthly_violation is False
    assert audit.overall_financially_feasible is True
    assert "Upfront surplus buffer" in audit.summary_notes


def test_budget_audit_upfront_deficit_triggers_hard_violation():
    one_time = OneTimeRelocationCosts(
        packers_movers_inr=42000.0,
        transit_insurance_inr=3000.0,
        travel_tickets_inr=5000.0
    )  # 50,000
    outlay = InitialHousingOutlay(
        security_deposit_inr=76000.0,
        advance_rent_inr=38000.0
    )  # 114,000
    recurring = RecurringMonthlyCosts(
        monthly_base_rent_inr=38000.0,
        society_maintenance_inr=4500.0,
        estimated_utilities_inr=4000.0,
        estimated_commute_inr=3000.0
    )

    audit = BudgetAudit(
        one_time_costs=one_time,
        housing_outlay=outlay,
        upfront_budget_limit_inr=150000.0,  # Cap is 150k, total is 164k
        recurring_monthly_costs=recurring,
        monthly_budget_limit_inr=55000.0
    )

    assert audit.total_upfront_outlay_inr == 164000.0
    assert audit.upfront_variance_inr == -14000.0
    assert audit.upfront_violation is True
    assert audit.overall_financially_feasible is False
    assert "Upfront deficit of ₹14,000.00" in audit.summary_notes


def test_housing_proposal_model(sample_housing_proposal):
    assert sample_housing_proposal.property_id == "BLR-HSR-201"
    assert sample_housing_proposal.monthly_rent_inr == 30000.0
    assert sample_housing_proposal.pet_friendly is True


def test_logistics_estimate_total(sample_logistics_estimate):
    # 38000 + 5000 + 2000 = 45000
    assert sample_logistics_estimate.total_logistics_inr == 45000.0
    assert sample_logistics_estimate.estimated_transit_days == 3


def test_document_audit_with_flagged_clause():
    clause = FlaggedClause(
        clause_title="Repainting Deduction",
        raw_text="Landlord shall deduct 1 month of rent for repainting.",
        risk_level="MEDIUM",
        advisory_note="Standard Bengaluru exit friction clause."
    )
    doc_audit = DocumentAudit(
        document_filename="test_lease.pdf",
        parse_status="SUCCESS",
        extracted_monthly_rent_inr=30000.0,
        extracted_security_deposit_inr=60000.0,
        extracted_notice_period_days=30,
        extracted_lock_in_months=6,
        flagged_clauses_for_review=[clause]
    )
    assert len(doc_audit.flagged_clauses_for_review) == 1
    assert "legal counsel" in doc_audit.disclaimer.lower()


def test_schedule_plan_milestone_ordering():
    m1 = MilestoneItem(
        step_id="M1",
        task_name="Lease Signing",
        target_date="2026-10-28",
        is_critical_path=True
    )
    m2 = MilestoneItem(
        step_id="M2",
        task_name="Mover Pickup",
        target_date="2026-11-01",
        prerequisites=["M1"],
        is_critical_path=True
    )
    plan = SchedulePlan(
        relocation_start_date="2026-10-28",
        completion_date="2026-11-04",
        is_feasible=True,
        critical_path_milestones=[m1, m2]
    )
    assert len(plan.critical_path_milestones) == 2
    assert plan.is_feasible is True


def test_revision_request_and_arbitration_plan():
    rev_req = RevisionRequest(
        target_agent="HousingResearchAgent",
        conflict_type="UPFRONT_BUDGET_OVERRUN",
        hard_limits={"max_monthly_rent": 30000.0, "max_security_deposit": 60000.0},
        soft_relaxations={"allow_commute_increase_mins": 10},
        rationale="Initial proposal caused ₹14,000 upfront deficit."
    )
    assert rev_req.target_agent == "HousingResearchAgent"
    assert rev_req.hard_limits["max_monthly_rent"] == 30000.0

    plan = SynthesizedPlan(
        plan_status="CONSENSUS_REACHED",
        iteration_count=2,
        recommended_housing_id="BLR-HSR-201",
        total_upfront_outlay_inr=137000.0,
        total_recurring_monthly_inr=39500.0,
        upfront_buffer_inr=13000.0,
        monthly_headroom_inr=5500.0,
        trade_offs_resolved=["Switched to HSR Layout to preserve ₹13,000 buffer."]
    )
    assert plan.plan_status == "CONSENSUS_REACHED"
    assert plan.iteration_count == 2


def test_relocation_state_full_assembly(sample_profile, sample_housing_proposal, sample_logistics_estimate):
    state = RelocationState(
        project_id="proj-uuid-999",
        profile=sample_profile,
        housing_proposal=sample_housing_proposal,
        logistics_estimate=sample_logistics_estimate,
        iteration_count=1,
        status="PROPOSING"
    )
    assert state.project_id == "proj-uuid-999"
    assert state.profile.destination_city == "Bengaluru"
    assert state.housing_proposal.property_id == "BLR-HSR-201"
    assert state.logistics_estimate.distance_km == 840
