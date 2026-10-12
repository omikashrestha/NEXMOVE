"""Comprehensive automated regression tests for NEXMOVE functional enhancements.

Covers:
1. Destination integrity (Kolkata destination guarantees Kolkata housing and logistics route)
2. Multiple housing options retrieval and candidate selection
3. Unsupported destination handling and custom property fallback
4. City autocomplete and places search API
5. Workplace commute estimation and dynamic distance calculation
6. Budget math consistency and upfront vs recurring separation
7. Moving timeline chronological milestones (M-01 to M-06)
8. Lease document analysis (standard, penalty, and draft/ambiguous terms)
9. Dynamic replanning with reduced budget triggering escalation options
10. Escalation decision resolution (Option A and Option B)
11. Multi-agent state orchestration and artifact persistence
12. Complete end-to-end API project lifecycle
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.places import (
    search_indian_cities,
    search_workplaces,
    calculate_intercity_distance_km
)
from backend.app.agents.housing import HousingResearchAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAnalystAgent
from backend.app.agents.schedule import ScheduleOptimizationAgent
from backend.app.agents.document import DocumentIntelligenceAgent
from backend.app.agents.decision import DecisionSynthesisAgent
from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.agents.graph import run_relocation_workflow


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.db.session import Base, get_db

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# SCENARIO 1: Destination Integrity
# ---------------------------------------------------------------------------
def test_scenario_01_destination_integrity():
    """Selecting Kolkata guarantees Kolkata housing, route, and transit."""
    profile = RelocationProfile(
        user_id="usr-01",
        origin_city="Pune",
        destination_city="Kolkata",
        target_move_date="2026-11-20",
        upfront_budget_limit_inr=180000,
        monthly_budget_limit_inr=50000,
        home_bhk=2,
        has_pets=True,
        target_workplace="Salt Lake Sector V",
        max_commute_mins=45
    )
    housing_agent = HousingResearchAgent()
    proposal = housing_agent.search(profile)
    assert proposal is not None
    assert proposal.city.lower() == "kolkata"
    assert "bengaluru" not in proposal.city.lower()

    logistics_agent = LogisticsAgent()
    logistics = logistics_agent.estimate(profile)
    assert "kolkata" in logistics.route.lower()
    assert logistics.distance_km >= 1200  # Pune to Kolkata is ~1600+ km


# ---------------------------------------------------------------------------
# SCENARIO 2: Multiple Housing Options & Selection
# ---------------------------------------------------------------------------
def test_scenario_02_multiple_housing_options_and_selection(client):
    """Destination returns multiple matching candidate options and supports property selection."""
    create_res = client.post("/api/projects", json={
        "user_email": "test@nexmove.internal",
        "user_name": "Test User",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-15",
        "upfront_budget_limit_inr": 200000,
        "monthly_budget_limit_inr": 60000,
        "home_bhk": 2,
        "has_pets": False,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 45
    })
    assert create_res.status_code == 201
    project_id = create_res.json()["project_id"]

    run_res = client.post(f"/api/projects/{project_id}/run")
    assert run_res.status_code == 200
    plan_data = run_res.json()

    options = plan_data.get("available_housing_options", [])
    assert len(options) >= 2, "Expected multiple candidate housing options in Bengaluru"

    initial_prop_id = plan_data["housing_proposal"]["property_id"]
    alt_prop = next(p for p in options if p["property_id"] != initial_prop_id)

    # Switch to alternate candidate
    select_res = client.post(f"/api/projects/{project_id}/select-property", json={
        "property_id": alt_prop["property_id"]
    })
    assert select_res.status_code == 200
    updated_plan = select_res.json()
    assert updated_plan["selected_property_id"] == alt_prop["property_id"]
    assert updated_plan["housing_proposal"]["property_id"] == alt_prop["property_id"]


# ---------------------------------------------------------------------------
# SCENARIO 3: Unsupported Destination Handling & Custom Property Entry
# ---------------------------------------------------------------------------
def test_scenario_03_unsupported_destination_and_custom_property(client):
    """Unsupported destination produces NO_HOUSING_AVAILABLE without faking data, and manual entry works."""
    create_res = client.post("/api/projects", json={
        "user_email": "test@nexmove.internal",
        "user_name": "Patna Relocator",
        "origin_city": "Delhi NCR",
        "destination_city": "Patna",
        "target_move_date": "2026-12-01",
        "upfront_budget_limit_inr": 150000,
        "monthly_budget_limit_inr": 40000,
        "home_bhk": 2,
        "has_pets": False,
        "target_workplace": "Dak Bungalow Crossing",
        "max_commute_mins": 30
    })
    assert create_res.status_code == 201
    project_id = create_res.json()["project_id"]

    run_res = client.post(f"/api/projects/{project_id}/run")
    assert run_res.status_code == 200
    plan_data = run_res.json()
    assert plan_data["status"] == "NO_HOUSING_AVAILABLE"
    assert plan_data["housing_proposal"] is None

    # Add custom property manually
    custom_res = client.post(f"/api/projects/{project_id}/custom-property", json={
        "title": "2BHK Apartment in Kankarbagh",
        "neighborhood": "Kankarbagh",
        "bhk": 2,
        "monthly_rent_inr": 22000,
        "security_deposit_inr": 44000,
        "society_maintenance_inr": 2000,
        "commute_to_workplace_mins": 20,
        "pet_friendly": False,
        "property_type": "Independent Floor"
    })
    assert custom_res.status_code == 200
    custom_data = custom_res.json()
    assert custom_data["housing_proposal"] is not None
    assert custom_data["housing_proposal"]["city"] == "Patna"
    assert custom_data["housing_proposal"]["monthly_rent_inr"] == 22000
    assert custom_data["status"] in ["CONSENSUS_REACHED", "APPROVED"]


# ---------------------------------------------------------------------------
# SCENARIO 4: City Autocomplete and Places Search
# ---------------------------------------------------------------------------
def test_scenario_04_places_api(client):
    """Tests /api/places/cities, workplaces, and distance endpoints."""
    # City search
    res = client.get("/api/places/cities?q=kol")
    assert res.status_code == 200
    cities = res.json()
    assert any(c["name"] == "Kolkata" for c in cities)

    # Workplace search for Kolkata
    wp_res = client.get("/api/places/workplaces?city=Kolkata")
    assert wp_res.status_code == 200
    workplaces = wp_res.json()
    assert any(w["name"] == "Salt Lake Sector V" for w in workplaces)

    # Distance calculation
    dist_res = client.get("/api/places/distance?origin=Pune&destination=Bengaluru")
    assert dist_res.status_code == 200
    dist_data = dist_res.json()
    assert 700 <= dist_data["distance_km"] <= 1000


# ---------------------------------------------------------------------------
# SCENARIO 5: Workplace Commute Estimation
# ---------------------------------------------------------------------------
def test_scenario_05_workplace_commute_estimation():
    """Commute times are calculated based on destination coordinates and workplace hubs."""
    agent = HousingResearchAgent()
    profile = RelocationProfile(
        user_id="usr-05",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=200000,
        monthly_budget_limit_inr=60000,
        home_bhk=2,
        has_pets=False,
        target_workplace="Manyata Tech Park",
        max_commute_mins=45
    )
    proposal = agent.search(profile)
    assert proposal is not None
    assert proposal.commute_to_workplace_mins > 0
    assert proposal.commute_to_workplace_mins <= 60


# ---------------------------------------------------------------------------
# SCENARIO 6: Budget Math Consistency & Strict Cost Separation
# ---------------------------------------------------------------------------
def test_scenario_06_budget_math_and_separation():
    """Verifies upfront relocation costs are strictly separated from recurring monthly living costs."""
    profile = RelocationProfile(
        user_id="usr-06",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=160000,
        monthly_budget_limit_inr=45000,
        home_bhk=2,
        has_pets=True,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    housing = HousingResearchAgent().search(profile)
    logistics = LogisticsAgent().estimate(profile)
    audit = BudgetAnalystAgent().audit(profile, housing, logistics)

    # 1. Non-zero costs
    assert audit.total_upfront_outlay_inr > 0
    assert audit.recurring_monthly_costs.total_recurring_monthly_inr > 0

    # 2. Mathematical sum verification for upfront costs
    expected_one_time = (
        audit.one_time_costs.packers_movers_inr +
        audit.one_time_costs.transit_insurance_inr +
        audit.one_time_costs.travel_tickets_inr +
        audit.one_time_costs.packing_supplies_inr
    )
    assert abs(audit.one_time_costs.total_one_time_inr - expected_one_time) < 0.01

    expected_housing_outlay = (
        audit.housing_outlay.security_deposit_inr +
        audit.housing_outlay.advance_rent_inr +
        audit.housing_outlay.move_in_fee_inr
    )
    assert abs(audit.housing_outlay.total_housing_outlay_inr - expected_housing_outlay) < 0.01

    assert abs(audit.total_upfront_outlay_inr - (expected_one_time + expected_housing_outlay)) < 0.01

    # 3. Mathematical sum verification for recurring monthly costs
    expected_monthly = (
        audit.recurring_monthly_costs.monthly_base_rent_inr +
        audit.recurring_monthly_costs.society_maintenance_inr +
        audit.recurring_monthly_costs.estimated_utilities_inr +
        audit.recurring_monthly_costs.estimated_commute_inr
    )
    assert abs(audit.recurring_monthly_costs.total_recurring_monthly_inr - expected_monthly) < 0.01


# ---------------------------------------------------------------------------
# SCENARIO 7: Moving Timeline Chronological Milestones
# ---------------------------------------------------------------------------
def test_scenario_07_moving_timeline_milestones():
    """Timeline strictly maintains milestone steps M-01 to M-06 ordered chronologically."""
    profile = RelocationProfile(
        user_id="usr-07",
        origin_city="Pune",
        destination_city="Kolkata",
        target_move_date="2026-11-20",
        upfront_budget_limit_inr=180000,
        monthly_budget_limit_inr=50000,
        home_bhk=2,
        has_pets=True,
        target_workplace="Salt Lake Sector V",
        max_commute_mins=45
    )
    housing = HousingResearchAgent().search(profile)
    logistics = LogisticsAgent().estimate(profile)
    doc_audit = DocumentIntelligenceAgent().analyze_document()
    schedule = ScheduleOptimizationAgent().build_schedule(profile, logistics, housing, doc_audit)

    assert len(schedule.critical_path_milestones) == 6
    step_ids = [m.step_id for m in schedule.critical_path_milestones]
    assert step_ids == ["M-01", "M-02", "M-03", "M-04", "M-05", "M-06"]

    # Verify chronological order
    dates = [m.target_date for m in schedule.critical_path_milestones]
    assert dates == sorted(dates), "Milestone target dates must be strictly non-decreasing"


# ---------------------------------------------------------------------------
# SCENARIO 8: Lease Document Analysis
# ---------------------------------------------------------------------------
def test_scenario_08_lease_document_analysis(client):
    """Tests sample lease audit and document upload endpoints."""
    # 1. Standard lease
    std_res = client.post("/api/documents/analyze-sample?sample_filename=lease_standard_inr.txt")
    assert std_res.status_code == 200
    std_audit = std_res.json()["audit"]
    assert std_audit["extracted_monthly_rent_inr"] == 30000
    assert std_audit["extracted_security_deposit_inr"] == 60000
    assert len(std_audit["flagged_clauses_for_review"]) == 0

    # 2. Red flag lease
    red_res = client.post("/api/documents/analyze-sample?sample_filename=lease_redflag_inr.txt")
    assert red_res.status_code == 200
    red_audit = red_res.json()["audit"]
    assert len(red_audit["flagged_clauses_for_review"]) >= 2
    high_severities = [c for c in red_audit["flagged_clauses_for_review"] if c.get("risk_level") == "HIGH" or c.get("severity") == "HIGH"]
    assert len(high_severities) >= 1

    # 3. Direct document upload
    sample_text = (
        "RENTAL AGREEMENT\n"
        "The Monthly Rent shall be Rs. 35,000 payable on 5th of every month.\n"
        "The Tenant agrees to pay a Refundable Security Deposit of Rs. 70,000.\n"
        "Notice period of 30 days is mandatory.\n"
    )
    files = {"file": ("uploaded_lease.txt", sample_text.encode("utf-8"), "text/plain")}
    upload_res = client.post("/api/documents/upload", files=files)
    assert upload_res.status_code == 200
    up_audit = upload_res.json()["audit"]
    assert up_audit["extracted_monthly_rent_inr"] == 35000
    assert up_audit["extracted_security_deposit_inr"] == 70000


# ---------------------------------------------------------------------------
# SCENARIO 9: Dynamic Replanning with Reduced Budget
# ---------------------------------------------------------------------------
def test_scenario_09_dynamic_replanning(client):
    """Rechecking plan with reduced budget triggers AWAITING_USER_DECISION with escalation options."""
    create_res = client.post("/api/projects", json={
        "user_email": "replan@nexmove.internal",
        "user_name": "Replan User",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-15",
        "upfront_budget_limit_inr": 180000,
        "monthly_budget_limit_inr": 50000,
        "home_bhk": 2,
        "has_pets": False,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 40
    })
    project_id = create_res.json()["project_id"]
    client.post(f"/api/projects/{project_id}/run")

    # Tighten budget to ₹45,000
    replan_res = client.post(f"/api/projects/{project_id}/replan", json={
        "upfront_budget_limit_inr": 45000
    })
    assert replan_res.status_code == 200
    replan_data = replan_res.json()
    assert replan_data["status"] == "AWAITING_USER_DECISION"
    assert replan_data["synthesized_plan"]["escalation_options"] is not None
    assert len(replan_data["synthesized_plan"]["escalation_options"]) >= 2


# ---------------------------------------------------------------------------
# SCENARIO 10: Escalation Decision Handling
# ---------------------------------------------------------------------------
def test_scenario_10_escalation_decision(client):
    """User selecting Option A or Option B resolves conflict and marks status APPROVED."""
    create_res = client.post("/api/projects", json={
        "user_email": "decision@nexmove.internal",
        "user_name": "Decision User",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-15",
        "upfront_budget_limit_inr": 45000,  # Deliberately tight to trigger escalation
        "monthly_budget_limit_inr": 35000,
        "home_bhk": 2,
        "has_pets": False,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 30
    })
    project_id = create_res.json()["project_id"]
    client.post(f"/api/projects/{project_id}/run")

    # Resolve with Choice A
    decide_res = client.post(f"/api/projects/{project_id}/decide", json={
        "decision_action": "SELECT_OPTION_A"
    })
    assert decide_res.status_code == 200
    decide_data = decide_res.json()
    assert decide_data["status"] in ["APPROVED", "CONSENSUS_REACHED"]


# ---------------------------------------------------------------------------
# SCENARIO 11: Multi-Agent State Orchestration
# ---------------------------------------------------------------------------
def test_scenario_11_multi_agent_state_orchestration():
    """Verifies all agents contribute their respective models to the LangGraph execution."""
    profile = RelocationProfile(
        user_id="usr-11",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=160000,
        monthly_budget_limit_inr=45000,
        home_bhk=2,
        has_pets=False,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )
    init_state = RelocationState(project_id="orch-test-01", profile=profile)
    final_state = run_relocation_workflow(init_state)

    assert final_state.housing_proposal is not None
    assert final_state.logistics_estimate is not None
    assert final_state.budget_audit is not None
    assert final_state.document_audit is not None
    assert final_state.schedule_plan is not None
    assert final_state.synthesized_plan is not None
    assert len(final_state.history) >= 4


# ---------------------------------------------------------------------------
# SCENARIO 12: End-to-End Project Workflow via API
# ---------------------------------------------------------------------------
def test_scenario_12_end_to_end_project_lifecycle(client):
    """Complete lifecycle: create -> run -> select candidate -> upload lease -> approve."""
    # 1. Create
    c_res = client.post("/api/projects", json={
        "user_email": "e2e@nexmove.internal",
        "user_name": "E2E User",
        "origin_city": "Pune",
        "destination_city": "Kolkata",
        "target_move_date": "2026-11-25",
        "upfront_budget_limit_inr": 200000,
        "monthly_budget_limit_inr": 55000,
        "home_bhk": 2,
        "has_pets": True,
        "target_workplace": "Salt Lake Sector V",
        "max_commute_mins": 45
    })
    assert c_res.status_code == 201
    pid = c_res.json()["project_id"]

    # 2. Run planning
    r_res = client.post(f"/api/projects/{pid}/run")
    assert r_res.status_code == 200
    plan = r_res.json()
    assert plan["status"] in ["CONSENSUS_REACHED", "AWAITING_USER_DECISION"]

    # 3. Select property if candidates exist
    options = plan.get("available_housing_options", [])
    if len(options) > 1:
        s_res = client.post(f"/api/projects/{pid}/select-property", json={
            "property_id": options[0]["property_id"]
        })
        assert s_res.status_code == 200

    # 4. Attach sample document
    d_res = client.post(f"/api/documents/analyze-sample?sample_filename=lease_standard_inr.txt&project_id={pid}")
    assert d_res.status_code == 200

    # 5. Approve plan
    a_res = client.post(f"/api/projects/{pid}/decide", json={"decision_action": "APPROVE"})
    assert a_res.status_code == 200
    assert a_res.json()["status"] == "APPROVED"
