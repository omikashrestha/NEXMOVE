import pytest
import json
import tempfile
from pathlib import Path

from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.schemas.arbitration import RevisionRequest, EscalationOption
from backend.app.agents.housing import HousingResearchAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAnalystAgent
from backend.app.agents.document import DocumentIntelligenceAgent
from backend.app.agents.schedule import ScheduleOptimizationAgent
from backend.app.agents.decision import DecisionSynthesisAgent
from backend.app.agents.graph import run_relocation_workflow


# ============================================================================
# AUDIT ITEM 1: LangGraph Revision Loop & Two-Round Maximum
# ============================================================================

def test_audit_revision_loop_consumption_and_cap():
    """Verifies that revision requests mutate candidate proposals and strictly cap at 2 rounds."""
    # Underfunded move that cannot be resolved in 2 rounds
    unresolvable_profile = RelocationProfile(
        user_id="usr-audit-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=50000.0,  # Far below minimum feasible outlays (~125k)
        monthly_budget_limit_inr=20000.0,
        home_bhk=2,
        has_pets=True
    )
    init_state = RelocationState(project_id="proj-audit-1", profile=unresolvable_profile)
    final_state = run_relocation_workflow(init_state)

    # Must terminate at exactly 2 iterations without infinite looping
    assert final_state.iteration_count == 2
    assert final_state.status == "AWAITING_USER_DECISION"
    assert final_state.synthesized_plan is not None
    assert final_state.synthesized_plan.plan_status == "AWAITING_USER_DECISION"
    assert len(final_state.synthesized_plan.escalation_options) == 2
    assert "Unresolvable" in final_state.synthesized_plan.trade_offs_resolved[0]


# ============================================================================
# AUDIT ITEM 2: Hard Constraint Preservation
# ============================================================================

def test_audit_pet_restriction_never_silently_discarded():
    """An agent must not silently discard pet restrictions to produce a feasible plan."""
    pet_profile = RelocationProfile(
        user_id="usr-audit-pets",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=150000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True
    )
    agent = HousingResearchAgent()
    # Search with aggressive budget restriction
    rev_req = RevisionRequest(
        target_agent="HousingResearchAgent",
        conflict_type="UPFRONT_BUDGET_OVERRUN",
        hard_limits={"max_monthly_rent": 22000.0},
        soft_relaxations={},
        rationale="Budget cap"
    )
    proposal = agent.search(pet_profile, revision_request=rev_req)
    # Even under budget pressure, the selected unit MUST remain pet-friendly
    assert proposal.pet_friendly is True


def test_audit_monthly_budget_violation_triggers_arbitration():
    """Confirm that exceeding monthly budget is audited separately from upfront capital."""
    monthly_tight_profile = RelocationProfile(
        user_id="usr-audit-mo",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=250000.0,  # Abundant upfront capital (₹2.5L)
        monthly_budget_limit_inr=26000.0,   # Very strict monthly living ceiling (₹26k)
        home_bhk=2,
        has_pets=False
    )
    init_state = RelocationState(project_id="proj-audit-mo", profile=monthly_tight_profile)
    final_state = run_relocation_workflow(init_state)

    # Monthly deficit must be flagged in audit
    assert final_state.budget_audit is not None
    # Upfront is completely fine
    assert final_state.budget_audit.upfront_violation is False
    # If monthly budget cannot be satisfied, it escalates to AWAITING_USER_DECISION
    if final_state.status == "AWAITING_USER_DECISION":
        assert any("MONTHLY" in c.conflict_id for c in final_state.active_conflicts)


def test_audit_schedule_clash_resolution_via_logistics_offset():
    """Confirm schedule delivery offset is requested and applied on date clash."""
    # Create profile and state with date clash
    profile = RelocationProfile(
        user_id="usr-audit-sched",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-03",
        upfront_budget_limit_inr=180000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=False
    )
    logistics_agent = LogisticsAgent()
    initial_estimate = logistics_agent.estimate(profile)

    # Delivery date is 2026-11-03, but apartment is available only on 2026-11-05
    sched_agent = ScheduleOptimizationAgent()
    plan_with_clash = sched_agent.build_schedule(
        profile=profile,
        logistics_estimate=initial_estimate,
        housing_proposal=HousingResearchAgent().search(profile),
        lease_start_date="2026-11-05"
    )
    assert plan_with_clash.is_feasible is False
    assert len(plan_with_clash.date_conflicts) == 1
    offset_needed = plan_with_clash.date_conflicts[0].suggested_offset_days

    # When logistics receives revision request with offset:
    rev = RevisionRequest(
        target_agent="LogisticsAgent",
        conflict_type="SCHEDULE_DATE_CLASH",
        hard_limits={"adjust_delivery_offset_days": offset_needed},
        soft_relaxations={},
        rationale="Shift delivery to match lease access"
    )
    adjusted_estimate = logistics_agent.estimate(profile, revision_request=rev)
    assert adjusted_estimate.estimated_delivery_date == "2026-11-05"


# ============================================================================
# AUDIT ITEM 3: Budget-Change Replanning & Stale Data Elimination
# ============================================================================

def test_audit_budget_change_recomputes_downstream_state():
    """Changing budget updates downstream housing, logistics, and budget audits without stale caching."""
    profile_high = RelocationProfile(
        user_id="usr-audit-replan",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=200000.0,
        monthly_budget_limit_inr=55000.0,
        home_bhk=2,
        has_pets=True
    )
    state_high = run_relocation_workflow(RelocationState(project_id="proj-replan", profile=profile_high))
    assert state_high.status == "CONSENSUS_REACHED"
    initial_buffer = state_high.budget_audit.upfront_variance_inr

    # User slashes upfront budget to ₹128,000
    profile_low = profile_high.model_copy(update={"upfront_budget_limit_inr": 128000.0})
    state_low = RelocationState(project_id="proj-replan", profile=profile_low)
    replan_state = run_relocation_workflow(state_low)

    # Budget limits, variances, and line items must reflect the new inputs
    assert replan_state.budget_audit.upfront_budget_limit_inr == 128000.0
    assert replan_state.budget_audit.upfront_variance_inr != initial_buffer
    assert replan_state.budget_audit.upfront_variance_inr >= 0.0


# ============================================================================
# AUDIT ITEM 4: Failure and Escalation Paths
# ============================================================================

def test_audit_missing_benchmark_files_raise_explicit_errors():
    """Missing or corrupted benchmark files must raise clear exceptions, not silent nulls."""
    with pytest.raises(FileNotFoundError):
        HousingResearchAgent(data_path=Path("non_existent_housing.json"))

    with pytest.raises(FileNotFoundError):
        LogisticsAgent(data_path=Path("non_existent_tariffs.json"))


def test_audit_empty_benchmark_listings_raise_value_error():
    """Empty datasets must raise descriptive ValueErrors."""
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        json.dump({"metadata": {}, "listings": []}, tmp)
        tmp_path = Path(tmp.name)

    try:
        agent = HousingResearchAgent(data_path=tmp_path)
        dummy_profile = RelocationProfile(
            user_id="usr-empty",
            origin_city="Pune",
            destination_city="Bengaluru",
            target_move_date="2026-11-05",
            upfront_budget_limit_inr=100000.0,
            monthly_budget_limit_inr=30000.0,
            home_bhk=2,
            has_pets=False
        )
        with pytest.raises(ValueError, match="zero listings"):
            agent.search(dummy_profile)
    finally:
        tmp_path.unlink()


def test_audit_empty_document_produces_failed_status():
    """Document Intelligence Agent with unreadable or missing input returns parse_status FAILED."""
    agent = DocumentIntelligenceAgent()
    audit = agent.analyze_document(file_path=Path("missing_lease.txt"))
    assert audit.parse_status == "FAILED"
    assert "Not legal counsel" in audit.disclaimer or "legal counsel" in audit.disclaimer.lower()


# ============================================================================
# AUDIT ITEM 5: Synthetic-Data and Document Safety
# ============================================================================

def test_audit_synthetic_labels_and_disclaimers(sample_profile):
    """All agent proposals and estimates must carry synthetic and non-legal disclaimers."""
    housing = HousingResearchAgent().search(sample_profile)
    assert housing.datasource == "SYNTHETIC_BENCHMARK_INR"

    logistics = LogisticsAgent().estimate(sample_profile)
    assert "Synthetic benchmark" in logistics.disclaimer

    doc = DocumentIntelligenceAgent().analyze_document(raw_text_content="Standard lease agreement ₹30,000")
    assert "Does not constitute formal legal counsel" in doc.disclaimer
