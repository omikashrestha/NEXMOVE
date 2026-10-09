from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.core.config import DATA_DIR
from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.agents.graph import run_relocation_workflow
from backend.app.agents.housing import HousingResearchAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAnalystAgent
from backend.app.agents.schedule import ScheduleOptimizationAgent
from backend.app.agents.document import DocumentIntelligenceAgent


# ============================================================================
# Benchmark Scenario 1: Feasible Relocation (Single-Pass Consensus)
# ============================================================================
def test_scenario_1_feasible_relocation():
    """Scenario 1: Standard relocation with healthy budgets achieves consensus in Round 1."""
    profile = RelocationProfile(
        user_id="usr-bench-01",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=180000.0,
        monthly_budget_limit_inr=50000.0,
        home_bhk=2,
        has_pets=True,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    initial_state = RelocationState(project_id="bench-scen-01", profile=profile)
    final_state = run_relocation_workflow(initial_state)

    # Status check
    assert final_state.status == "CONSENSUS_REACHED"
    assert final_state.iteration_count == 1
    assert len(final_state.active_conflicts) == 0

    # Three-Tier Budget Arithmetic
    b = final_state.budget_audit
    assert b is not None
    assert b.total_upfront_outlay_inr <= 180000.0
    assert b.recurring_monthly_costs.total_recurring_monthly_inr <= 50000.0
    assert b.upfront_violation is False
    assert b.monthly_violation is False

    # Schedule integrity
    s = final_state.schedule_plan
    assert s is not None
    assert s.is_feasible is True
    assert len(s.date_conflicts) == 0


# ============================================================================
# Benchmark Scenario 2: Upfront Budget Overrun (Resolved in Round 2)
# ============================================================================
def test_scenario_2_upfront_budget_overrun_resolution():
    """Scenario 2: Moderate upfront budget limit forces revision and resolves in Round 2."""
    profile = RelocationProfile(
        user_id="usr-bench-02",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=120000.0,  # Below the default 2BHK ~133k outlay
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    initial_state = RelocationState(project_id="bench-scen-02", profile=profile)
    final_state = run_relocation_workflow(initial_state)

    # Should revise and reach consensus in round 2
    assert final_state.status == "CONSENSUS_REACHED"
    assert final_state.iteration_count == 2
    assert final_state.budget_audit.total_upfront_outlay_inr <= 120000.0
    assert final_state.budget_audit.upfront_violation is False

    # Logistics shifted to economy transit
    assert "Economy" in final_state.logistics_estimate.vehicle_type or final_state.logistics_estimate.estimated_transit_days >= 4


# ============================================================================
# Benchmark Scenario 3: Monthly Budget Overrun (Resolved in Revision)
# ============================================================================
def test_scenario_3_monthly_budget_overrun_resolution():
    """Scenario 3: Tight monthly limit triggers monthly overrun and selects lower rent listing."""
    profile = RelocationProfile(
        user_id="usr-bench-03",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=180000.0,
        monthly_budget_limit_inr=26000.0,  # Strict monthly cap
        home_bhk=1,
        has_pets=False,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    initial_state = RelocationState(project_id="bench-scen-03", profile=profile)
    final_state = run_relocation_workflow(initial_state)

    assert final_state.budget_audit.recurring_monthly_costs.total_recurring_monthly_inr <= 26000.0
    assert final_state.housing_proposal.monthly_rent_inr <= 22000.0


# ============================================================================
# Benchmark Scenario 4: Impossible Budget & Escalation (Capped at Round 2)
# ============================================================================
def test_scenario_4_impossible_budget_escalation():
    """Scenario 4: Impossible budget caps at 2 rounds and outputs human decision options."""
    profile = RelocationProfile(
        user_id="usr-bench-04",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=40000.0,  # Impossible for 840 km interstate move
        monthly_budget_limit_inr=18000.0,
        home_bhk=2,
        has_pets=True,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    initial_state = RelocationState(project_id="bench-scen-04", profile=profile)
    final_state = run_relocation_workflow(initial_state)

    assert final_state.status == "AWAITING_USER_DECISION"
    assert final_state.iteration_count == 2
    assert len(final_state.active_conflicts) > 0

    # Must provide trade-off escalation options
    plan = final_state.synthesized_plan
    assert plan is not None
    assert len(plan.escalation_options) >= 2
    opt_ids = [opt.option_id for opt in plan.escalation_options]
    assert "A" in opt_ids and "B" in opt_ids


# ============================================================================
# Benchmark Scenario 5: Pet Restrictions (Hard Constraint Preserved)
# ============================================================================
def test_scenario_5_pet_restriction_preservation():
    """Scenario 5: Family pet constraint is strictly respected under revisions."""
    profile = RelocationProfile(
        user_id="usr-bench-05",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=130000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True,  # Hard requirement
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    initial_state = RelocationState(project_id="bench-scen-05", profile=profile)
    final_state = run_relocation_workflow(initial_state)

    assert final_state.housing_proposal.pet_friendly is True
    # Non-pet listing must never be recommended
    assert "BLR-HSR-201" != final_state.housing_proposal.property_id or final_state.housing_proposal.pet_friendly is True


# ============================================================================
# Benchmark Scenario 6: Lease-Start and Delivery-Date Conflict
# ============================================================================
def test_scenario_6_lease_start_and_delivery_date_conflict():
    """Scenario 6: Delivery arriving before lease start date is flagged with corrective offset."""
    profile = RelocationProfile(
        user_id="usr-bench-06",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=150000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=False
    )
    agent = ScheduleOptimizationAgent()
    housing = HousingResearchAgent().search(profile)
    logistics = LogisticsAgent().estimate(profile)

    # Lease is only available on 2026-11-08, but delivery is 2026-11-05
    plan = agent.build_schedule(
        profile=profile,
        logistics_estimate=logistics,
        housing_proposal=housing,
        lease_start_date="2026-11-08"
    )

    assert plan.is_feasible is False
    assert len(plan.date_conflicts) == 1
    conflict = plan.date_conflicts[0]
    assert conflict.conflict_type == "DELIVERY_BEFORE_LEASE_START"
    assert conflict.suggested_offset_days == 3


# ============================================================================
# Benchmark Scenario 7: Red-Flag Lease Clauses Document Audit
# ============================================================================
def test_scenario_7_red_flag_lease_clauses_audit():
    """Scenario 7: Document Intelligence flags risk clauses and outputs legal disclaimer."""
    lease_path = DATA_DIR / "sample_leases" / "lease_redflag_inr.txt"
    agent = DocumentIntelligenceAgent()
    audit = agent.analyze_document(file_path=lease_path)

    assert audit.parse_status == "SUCCESS"
    assert audit.extracted_monthly_rent_inr == 38000.0
    assert audit.extracted_security_deposit_inr == 76000.0
    assert len(audit.flagged_clauses_for_review) >= 3

    # Check specific flagged risk categories
    clause_titles = [c.clause_title for c in audit.flagged_clauses_for_review]
    assert any("Painting" in t for t in clause_titles)
    assert any("Pet" in t for t in clause_titles)
    assert any("Elevator" in t or "Hours" in t for t in clause_titles)

    # Legal Disclaimer must be present
    assert "legal" in audit.disclaimer.lower()


# ============================================================================
# Benchmark Scenario 8: Budget Reduction & Dynamic Replanning
# ============================================================================
def test_scenario_8_budget_reduction_and_dynamic_replanning():
    """Scenario 8: Reducing budget on existing state discards stale calculations and adapts."""
    profile = RelocationProfile(
        user_id="usr-bench-08",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=160000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True
    )
    s1 = run_relocation_workflow(RelocationState(project_id="bench-scen-08", profile=profile))
    orig_property_id = s1.housing_proposal.property_id
    orig_upfront_outlay = s1.budget_audit.total_upfront_outlay_inr

    # Reduce upfront budget below original outlay
    reduced_profile = profile.model_copy(update={"upfront_budget_limit_inr": 115000.0})
    s2 = run_relocation_workflow(RelocationState(project_id="bench-scen-08", profile=reduced_profile))

    # Stale checks
    assert s2.budget_audit.total_upfront_outlay_inr < orig_upfront_outlay
    assert s2.budget_audit.total_upfront_outlay_inr <= 115000.0
    assert s2.housing_proposal.property_id != orig_property_id
    assert s2.budget_audit.upfront_violation is False


# ============================================================================
# Benchmark Scenario 9: Move Date Change & Schedule Replanning
# ============================================================================
def test_scenario_9_move_date_change_and_schedule_replanning():
    """Scenario 9: Shifting move date recalculates all milestones with zero stale dates."""
    p1 = RelocationProfile(
        user_id="usr-bench-09",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=150000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True
    )
    s1 = run_relocation_workflow(RelocationState(project_id="bench-scen-09", profile=p1))

    p2 = p1.model_copy(update={"target_move_date": "2026-12-25"})
    s2 = run_relocation_workflow(RelocationState(project_id="bench-scen-09", profile=p2))

    assert s1.logistics_estimate.estimated_delivery_date == "2026-11-05"
    assert s2.logistics_estimate.estimated_delivery_date == "2026-12-25"

    # Milestones must reflect the new December dates
    m1_dates = [m.target_date for m in s1.schedule_plan.critical_path_milestones]
    m2_dates = [m.target_date for m in s2.schedule_plan.critical_path_milestones]
    assert all("2026-11" in d or "2026-10" in d for d in m1_dates)
    assert all("2026-12" in d for d in m2_dates)


# ============================================================================
# Benchmark Scenario 10: Missing or Corrupted Inputs Graceful Handling
# ============================================================================
def test_scenario_10_missing_or_corrupted_inputs_graceful_handling():
    """Scenario 10: Missing files and malformed payloads trigger explicit graceful handling."""
    # 1. Non-existent lease file
    agent = DocumentIntelligenceAgent()
    missing_path = DATA_DIR / "sample_leases" / "non_existent_file.txt"
    audit = agent.analyze_document(file_path=missing_path)
    assert audit.parse_status == "FAILED"
    assert len(audit.flagged_clauses_for_review) == 0

    # 2. Pydantic schema rejection on corrupted types
    with pytest.raises(ValidationError):
        RelocationProfile(
            user_id="usr-bench-10",
            origin_city="Pune",
            destination_city="Bengaluru",
            target_move_date="not-a-valid-date",
            upfront_budget_limit_inr=-5000.0,  # Negative budget invalid
            monthly_budget_limit_inr=45000.0,
            home_bhk=2,
            has_pets=True
        )
