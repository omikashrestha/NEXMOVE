import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.session import Base, get_db

from sqlalchemy.pool import StaticPool

# Setup isolated test database session with StaticPool for thread-safe in-memory SQLite
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


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ============================================================================
# API Tests
# ============================================================================

def test_api_health_endpoints(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["service"] == "NEXMOVE Multi-Agent Relocation Assistant"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


def test_api_create_project_valid(client):
    payload = {
        "user_email": "omika@example.com",
        "user_name": "Omika Shrestha",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 150000.0,
        "monthly_budget_limit_inr": 45000.0,
        "home_bhk": 2,
        "has_pets": True,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 40
    }
    res = client.post("/api/projects", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "project_id" in data
    assert data["origin_city"] == "Pune"
    assert data["destination_city"] == "Bengaluru"
    assert data["status"] == "DRAFT"


def test_api_create_project_invalid_input(client):
    # Budget must be > 0
    invalid_payload = {
        "user_email": "invalid@example.com",
        "user_name": "Invalid User",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": -500.0,  # Negative budget
        "monthly_budget_limit_inr": 0.0,     # Zero budget
        "home_bhk": 2,
        "has_pets": False
    }
    res = client.post("/api/projects", json=invalid_payload)
    assert res.status_code == 422  # Pydantic validation failure


def test_api_get_project_missing_404(client):
    res = client.get("/api/projects/non-existent-uuid")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_api_run_project_planning_consensus(client):
    # 1. Create project with healthy budget
    create_payload = {
        "user_email": "omika@example.com",
        "user_name": "Omika Shrestha",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 180000.0,
        "monthly_budget_limit_inr": 50000.0,
        "home_bhk": 2,
        "has_pets": True
    }
    create_res = client.post("/api/projects", json=create_payload)
    proj_id = create_res.json()["project_id"]

    # 2. Run planning
    run_res = client.post(f"/api/projects/{proj_id}/run")
    assert run_res.status_code == 200
    plan_data = run_res.json()

    assert plan_data["status"] == "CONSENSUS_REACHED"
    assert plan_data["housing_proposal"] is not None
    assert plan_data["logistics_estimate"] is not None
    assert plan_data["budget_audit"] is not None
    assert plan_data["schedule_plan"] is not None
    assert plan_data["synthesized_plan"]["plan_status"] == "CONSENSUS_REACHED"
    assert len(plan_data["execution_logs"]) > 0


def test_api_replan_project_budget_change(client):
    # 1. Create project
    create_res = client.post("/api/projects", json={
        "user_email": "omika@example.com",
        "user_name": "Omika Shrestha",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 180000.0,
        "monthly_budget_limit_inr": 50000.0,
        "home_bhk": 2,
        "has_pets": True
    })
    proj_id = create_res.json()["project_id"]
    client.post(f"/api/projects/{proj_id}/run")

    # 2. Replan with budget cut
    replan_res = client.post(f"/api/projects/{proj_id}/replan", json={
        "upfront_budget_limit_inr": 130000.0
    })
    assert replan_res.status_code == 200
    data = replan_res.json()
    assert data["upfront_budget_limit_inr"] == 130000.0
    assert data["budget_audit"]["upfront_budget_limit_inr"] == 130000.0


def test_api_unresolved_conflict_returns_awaiting_decision(client):
    # Severely underfunded move
    create_res = client.post("/api/projects", json={
        "user_email": "tight@example.com",
        "user_name": "Tight Budget User",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 45000.0,  # Impossible
        "monthly_budget_limit_inr": 20000.0,
        "home_bhk": 2,
        "has_pets": True
    })
    proj_id = create_res.json()["project_id"]

    run_res = client.post(f"/api/projects/{proj_id}/run")
    assert run_res.status_code == 200
    data = run_res.json()

    assert data["status"] == "AWAITING_USER_DECISION"
    assert data["synthesized_plan"]["plan_status"] == "AWAITING_USER_DECISION"
    assert len(data["synthesized_plan"]["escalation_options"]) == 2


def test_api_user_decision_approve(client):
    create_res = client.post("/api/projects", json={
        "user_email": "omika@example.com",
        "user_name": "Omika Shrestha",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 180000.0,
        "monthly_budget_limit_inr": 50000.0,
        "home_bhk": 2,
        "has_pets": True
    })
    proj_id = create_res.json()["project_id"]
    client.post(f"/api/projects/{proj_id}/run")

    decide_res = client.post(f"/api/projects/{proj_id}/decide", json={
        "decision_action": "APPROVE",
        "notes": "Plan confirmed by user."
    })
    assert decide_res.status_code == 200
    assert decide_res.json()["status"] == "APPROVED"


def test_api_document_samples_and_analysis(client):
    samples_res = client.get("/api/documents/samples")
    assert samples_res.status_code == 200
    samples = samples_res.json()
    assert len(samples) >= 2

    # Analyze sample
    analyze_res = client.post("/api/documents/analyze-sample?sample_filename=lease_redflag_inr.txt")
    assert analyze_res.status_code == 200
    audit = analyze_res.json()["audit"]
    assert audit["extracted_monthly_rent_inr"] == 38000.0
    assert len(audit["flagged_clauses_for_review"]) >= 3


def test_api_n8n_webhook_resume(client):
    create_res = client.post("/api/projects", json={
        "user_email": "n8n@example.com",
        "user_name": "N8N User",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 180000.0,
        "monthly_budget_limit_inr": 50000.0,
        "home_bhk": 2,
        "has_pets": True
    })
    proj_id = create_res.json()["project_id"]
    client.post(f"/api/projects/{proj_id}/run")

    resume_res = client.post("/api/webhooks/n8n/resume", json={
        "project_id": proj_id,
        "callback_token": "token-xyz-123",
        "user_choice": "APPROVE",
        "notes": "Approved from n8n HITL email button"
    })
    assert resume_res.status_code == 200
    assert resume_res.json()["success"] is True
    assert resume_res.json()["status"] == "APPROVED"
