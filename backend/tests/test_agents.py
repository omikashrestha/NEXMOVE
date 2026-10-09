import pytest
from pathlib import Path

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.schemas.arbitration import RevisionRequest
from backend.app.agents.housing import HousingResearchAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAnalystAgent
from backend.app.agents.document import DocumentIntelligenceAgent
from backend.app.agents.schedule import ScheduleOptimizationAgent
from backend.app.agents.decision import DecisionSynthesisAgent
from backend.app.agents.graph import run_relocation_workflow


# ============================================================================
# 1. Housing Research Agent Tests
# ============================================================================

def test_housing_agent_pet_constraint(sample_profile):
    agent = HousingResearchAgent()
    # Profile has pets == True
    proposal = agent.search(sample_profile)
    assert proposal.pet_friendly is True
    assert proposal.city == "Bengaluru"


def test_housing_agent_respects_revision_limits(sample_profile):
    agent = HousingResearchAgent()
    rev_req = RevisionRequest(
        target_agent="HousingResearchAgent",
        conflict_type="UPFRONT_BUDGET_OVERRUN",
        hard_limits={"max_monthly_rent": 26000.0, "max_security_deposit": 52000.0},
        soft_relaxations={"allow_commute_increase_mins": 15},
        rationale="Budget exceeded"
    )
    proposal = agent.search(sample_profile, revision_request=rev_req)
    assert proposal.monthly_rent_inr <= 26000.0
    assert proposal.security_deposit_inr <= 52000.0


# ============================================================================
# 2. Logistics Agent Tests
# ============================================================================

def test_logistics_agent_tariff_calculation(sample_profile):
    agent = LogisticsAgent()
    estimate = agent.estimate(sample_profile)
    assert estimate.distance_km == 840
    assert estimate.estimated_transit_days == 3
    assert estimate.base_packers_movers_quote_inr == 38000.0
    # Pet specialty fee added because sample_profile.has_pets is True
    assert estimate.vehicle_shipping_inr == 8000.0
    assert estimate.total_logistics_inr == (38000.0 + 8000.0 + 2000.0)


def test_logistics_agent_economy_revision(sample_profile):
    agent = LogisticsAgent()
    rev_req = RevisionRequest(
        target_agent="LogisticsAgent",
        conflict_type="UPFRONT_BUDGET_OVERRUN",
        hard_limits={"prefer_economy_freight": True},
        soft_relaxations={},
        rationale="Save moving freight"
    )
    estimate = agent.estimate(sample_profile, revision_request=rev_req)
    assert "Shared Economy" in estimate.vehicle_type
    assert estimate.estimated_transit_days == 5  # 3 + 2 days


# ============================================================================
# 3. Budget Analyst Agent Tests
# ============================================================================

def test_budget_analyst_feasible_math(sample_profile, sample_housing_proposal, sample_logistics_estimate):
    agent = BudgetAnalystAgent()
    audit = agent.audit(sample_profile, sample_housing_proposal, sample_logistics_estimate)
    # Total upfront = 45,000 (logistics) + 7,500 (travel/supplies) + 60,000 (dep) + 30,000 (1st mo rent) + 2,000 (fee)
    assert audit.upfront_violation is False
    assert audit.monthly_violation is False
    assert audit.overall_financially_feasible is True


def test_budget_analyst_detects_overrun(sample_housing_proposal, sample_logistics_estimate):
    agent = BudgetAnalystAgent()
    tight_profile = RelocationProfile(
        user_id="usr-tight-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=100000.0,  # Far below outlays (~144k)
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=False
    )
    audit = agent.audit(tight_profile, sample_housing_proposal, sample_logistics_estimate)
    assert audit.upfront_violation is True
    assert audit.upfront_variance_inr < 0.0
    assert audit.overall_financially_feasible is False


# ============================================================================
# 4. Document Intelligence Agent Tests
# ============================================================================

def test_document_agent_standard_lease():
    agent = DocumentIntelligenceAgent()
    lease_path = DATA_DIR / "sample_leases" / "lease_standard_inr.txt"
    audit = agent.analyze_document(file_path=lease_path)
    assert audit.parse_status == "SUCCESS"
    assert audit.extracted_monthly_rent_inr == 30000.0
    assert audit.extracted_security_deposit_inr == 60000.0
    assert len(audit.flagged_clauses_for_review) == 0  # Standard lease has no non-standard penalties


def test_document_agent_redflag_lease():
    agent = DocumentIntelligenceAgent()
    lease_path = DATA_DIR / "sample_leases" / "lease_redflag_inr.txt"
    audit = agent.analyze_document(file_path=lease_path)
    assert audit.parse_status == "SUCCESS"
    assert audit.extracted_monthly_rent_inr == 38000.0
    assert audit.extracted_security_deposit_inr == 76000.0
    # Flags painting deduction, pet ban, and elevator hours
    assert len(audit.flagged_clauses_for_review) >= 3
    titles = [c.clause_title for c in audit.flagged_clauses_for_review]
    assert any("Painting" in t for t in titles)
    assert any("Pet" in t for t in titles)
    assert any("Hours" in t or "Elevator" in t for t in titles)


# ============================================================================
# 5. Schedule Optimization Agent Tests
# ============================================================================

def test_schedule_agent_topological_milestones(sample_profile, sample_logistics_estimate, sample_housing_proposal):
    agent = ScheduleOptimizationAgent()
    plan = agent.build_schedule(sample_profile, sample_logistics_estimate, sample_housing_proposal)
    assert plan.is_feasible is True
    assert len(plan.critical_path_milestones) == 6
    step_ids = [m.step_id for m in plan.critical_path_milestones]
    assert step_ids == ["M-01", "M-02", "M-03", "M-04", "M-05", "M-06"]


def test_schedule_agent_detects_delivery_before_lease_clash(sample_profile, sample_logistics_estimate, sample_housing_proposal):
    agent = ScheduleOptimizationAgent()
    # logistics delivery is 2026-11-04, but lease doesn't start until 2026-11-06
    plan = agent.build_schedule(
        sample_profile,
        sample_logistics_estimate,
        sample_housing_proposal,
        lease_start_date="2026-11-06"
    )
    assert plan.is_feasible is False
    assert len(plan.date_conflicts) == 1
    assert plan.date_conflicts[0].conflict_type == "DELIVERY_BEFORE_LEASE_START"
    assert plan.date_conflicts[0].suggested_offset_days == 2


# ============================================================================
# 6. Multi-Agent Orchestration & Decision Agent Tests
# ============================================================================

def test_orchestration_single_pass_consensus():
    """Generous budget scenario converges in Iteration 1 without revision."""
    generous_profile = RelocationProfile(
        user_id="usr-gen-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=200000.0,  # Generous ₹2,00,000
        monthly_budget_limit_inr=55000.0,
        home_bhk=2,
        has_pets=True
    )
    init_state = RelocationState(project_id="proj-gen-1", profile=generous_profile)
    final_state = run_relocation_workflow(init_state)

    assert final_state.status == "CONSENSUS_REACHED"
    assert final_state.iteration_count == 1
    assert final_state.synthesized_plan is not None
    assert final_state.synthesized_plan.plan_status == "CONSENSUS_REACHED"
    assert final_state.synthesized_plan.upfront_buffer_inr > 0


def test_orchestration_budget_overrun_resolved_in_revision():
    """Moderate budget causes Iteration 1 deficit, resolved in Iteration 2 via lower-cost housing."""
    moderate_profile = RelocationProfile(
        user_id="usr-mod-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=128000.0,  # Below initial top candidate outlay (133k), forcing revision
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True
    )
    init_state = RelocationState(project_id="proj-mod-1", profile=moderate_profile)
    final_state = run_relocation_workflow(init_state)

    assert final_state.status == "CONSENSUS_REACHED"
    assert final_state.iteration_count == 2
    assert final_state.active_revision_request is not None
    assert final_state.synthesized_plan.plan_status == "CONSENSUS_REACHED"

    # Trade-offs explanation recorded
    assert len(final_state.synthesized_plan.trade_offs_resolved) > 0


def test_orchestration_impossible_budget_caps_at_two_iterations():
    """Severely underfunded move hits maximum 2-round cap and escalates to AWAITING_USER_DECISION."""
    impossible_profile = RelocationProfile(
        user_id="usr-imp-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=45000.0,  # Impossible: freight alone is ~₹38k, leaving zero for rent/deposit
        monthly_budget_limit_inr=25000.0,
        home_bhk=2,
        has_pets=True
    )
    init_state = RelocationState(project_id="proj-imp-1", profile=impossible_profile)
    final_state = run_relocation_workflow(init_state)

    assert final_state.status == "AWAITING_USER_DECISION"
    assert final_state.iteration_count == 2
    assert final_state.synthesized_plan.plan_status == "AWAITING_USER_DECISION"
    assert len(final_state.synthesized_plan.escalation_options) == 2
    assert final_state.synthesized_plan.escalation_options[0].option_id == "A"
    assert final_state.synthesized_plan.escalation_options[1].option_id == "B"


def test_orchestration_dynamic_replanning_on_budget_change():
    """Simulates dynamic replanning when user changes their budget after an initial run."""
    # Step 1: Initial run with ₹1,80,000 budget
    profile_v1 = RelocationProfile(
        user_id="usr-replan-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=180000.0,
        monthly_budget_limit_inr=50000.0,
        home_bhk=2,
        has_pets=True
    )
    state_v1 = run_relocation_workflow(RelocationState(project_id="proj-replan-1", profile=profile_v1))
    assert state_v1.status == "CONSENSUS_REACHED"

    # Step 2: User cuts budget by ₹50,000 to ₹130,000
    profile_v2 = profile_v1.model_copy(update={"upfront_budget_limit_inr": 130000.0})
    state_v2 = RelocationState(
        project_id="proj-replan-1",
        profile=profile_v2,
        iteration_count=1
    )
    replan_state = run_relocation_workflow(state_v2)

    # Re-run adapts to the new budget constraint
    assert replan_state.status in ["CONSENSUS_REACHED", "AWAITING_USER_DECISION"]
    assert replan_state.budget_audit is not None
    assert replan_state.budget_audit.upfront_budget_limit_inr == 130000.0
