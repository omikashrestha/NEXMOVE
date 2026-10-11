import pytest
from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.agents.graph import run_relocation_workflow
from backend.app.agents.document import DocumentIntelligenceAgent


def test_scenario_pune_to_kolkata_feasible():
    """Scenario A: Pune to Kolkata move with feasible budget yields consensus in Kolkata."""
    profile = RelocationProfile(
        user_id="usr-verify-ccu-01",
        origin_city="Pune",
        destination_city="Kolkata",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=180000.0,
        monthly_budget_limit_inr=50000.0,
        home_bhk=2,
        has_pets=False
    )
    state = run_relocation_workflow(RelocationState(project_id="proj-ccu-01", profile=profile))
    
    assert state.status == "CONSENSUS_REACHED"
    assert state.housing_proposal is not None
    assert state.housing_proposal.city == "Kolkata"
    assert "Kolkata" in state.housing_proposal.title or "Kolkata" in state.logistics_estimate.route
    assert state.logistics_estimate.route == "Pune -> Kolkata"
    assert state.budget_audit.upfront_violation is False
    assert state.budget_audit.monthly_violation is False


def test_scenario_pune_to_kolkata_tight_budget_escalation():
    """Scenario B: Pune to Kolkata move with ₹60,000 upfront budget triggers escalation."""
    profile = RelocationProfile(
        user_id="usr-verify-ccu-tight",
        origin_city="Pune",
        destination_city="Kolkata",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=60000.0,
        monthly_budget_limit_inr=50000.0,
        home_bhk=2,
        has_pets=False
    )
    state = run_relocation_workflow(RelocationState(project_id="proj-ccu-tight", profile=profile))
    
    assert state.status == "AWAITING_USER_DECISION"
    assert any("UPFRONT-BUDGET" in c.conflict_id for c in state.active_conflicts)
    assert len(state.synthesized_plan.escalation_options) == 2
    assert state.synthesized_plan.escalation_options[0].option_id == "A"
    assert state.synthesized_plan.escalation_options[1].option_id == "B"


def test_scenario_unrepresented_destination_no_substitution():
    """Scenario C: Destination without listings (Guwahati) returns NO_HOUSING_AVAILABLE without Bengaluru substitution."""
    profile = RelocationProfile(
        user_id="usr-verify-guwahati",
        origin_city="Pune",
        destination_city="Guwahati",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=150000.0,
        monthly_budget_limit_inr=50000.0,
        home_bhk=2,
        has_pets=False
    )
    state = run_relocation_workflow(RelocationState(project_id="proj-guwahati", profile=profile))
    
    assert state.status == "NO_HOUSING_AVAILABLE"
    assert state.housing_proposal is None
    assert state.synthesized_plan.plan_status == "NO_HOUSING_AVAILABLE"
    assert any("Guwahati" in item for item in state.synthesized_plan.trade_offs_resolved)


def test_scenario_monthly_budget_severe_overrun():
    """Scenario D: Monthly budget set far below rent market triggers monthly violation and escalation."""
    profile = RelocationProfile(
        user_id="usr-verify-monthly-tight",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=200000.0,
        monthly_budget_limit_inr=15000.0,  # Below any feasible 2BHK rental + living cost
        home_bhk=2,
        has_pets=False
    )
    state = run_relocation_workflow(RelocationState(project_id="proj-monthly-tight", profile=profile))
    
    assert state.status == "AWAITING_USER_DECISION"
    assert any("MONTHLY-BUDGET" in c.conflict_id for c in state.active_conflicts)


def test_scenario_lease_missing_financial_terms():
    """Scenario E: Uploaded lease missing financial terms flags NEEDS_MANUAL_REVIEW."""
    agent = DocumentIntelligenceAgent()
    audit = agent.analyze_document(raw_text_content="This standard lease agreement outlines premises rules but specifies no rental figures.")
    
    assert audit.parse_status == "NEEDS_MANUAL_REVIEW"
    assert audit.extracted_monthly_rent_inr is None
    assert audit.extracted_security_deposit_inr is None
    assert any(c.risk_level in ["HIGH", "MEDIUM"] for c in audit.flagged_clauses_for_review)
