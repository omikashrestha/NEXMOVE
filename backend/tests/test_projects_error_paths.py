"""
test_projects_error_paths.py
──────────────────────────────────────────────────────────────────────────────
Targeted error-handling and cascade-delete tests for the NEXMOVE Projects API
and SQLAlchemy database models (Tanmay Salunkhe's assigned area).

Covers gaps not addressed by the existing test_api.py and test_db_models.py:
  1. POST /decide with an unrecognised action verb → 400 Bad Request
  2. POST /run  on a non-existent project_id    → 404 Not Found
  3. POST /replan on a non-existent project_id  → 404 Not Found
  4. POST /decide on a non-existent project_id  → 404 Not Found
  5. DB cascade-delete: removing a User purges all child RelocationProjects,
     BudgetLineItems, ScheduleMilestones, AgentExecutionLogs, and
     DocumentRecords in a single operation.
  6. LogisticsEstimate total_logistics_inr computed correctly via model_validator
     when all three fee components are non-zero (regression guard).
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.session import Base, get_db
from backend.app.db.models import (
    User,
    RelocationProject,
    BudgetLineItem,
    ScheduleMilestone,
    AgentExecutionLog,
    DocumentRecord,
)
from backend.app.schemas.logistics import LogisticsEstimate


# ─────────────────────────────────────────────────────────────────────────────
# Isolated in-memory SQLite database (per-test, fixture-scoped override)
# Using a fixture-scoped override (not module-level) avoids cross-file
# test isolation issues when test_api.py also sets app.dependency_overrides.
# ─────────────────────────────────────────────────────────────────────────────
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(autouse=True)
def _reset_db():
    """
    Create all tables before each test and drop them after.
    Also installs and cleans up the DB dependency override so this module's
    tests don't interfere with test_api.py (which sets its own module-level
    override on the same FastAPI app instance).
    """
    Base.metadata.create_all(bind=_test_engine)

    def _override():
        db = _TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: create a project via the API and return its project_id
# ─────────────────────────────────────────────────────────────────────────────
_VALID_PROJECT_PAYLOAD = {
    "user_email": "tanmay-test@nexmove.ai",
    "user_name": "Tanmay Salunkhe",
    "origin_city": "Pune",
    "destination_city": "Bengaluru",
    "target_move_date": "2026-11-05",
    "upfront_budget_limit_inr": 180000.0,
    "monthly_budget_limit_inr": 50000.0,
    "home_bhk": 2,
    "has_pets": False,
    "target_workplace": "Manyata Tech Park",
    "max_commute_mins": 40,
}


def _create_project(client) -> str:
    res = client.post("/api/projects", json=_VALID_PROJECT_PAYLOAD)
    assert res.status_code == 201, f"Project creation failed: {res.text}"
    return res.json()["project_id"]


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 – POST /decide with an unrecognised action verb → 400
# ─────────────────────────────────────────────────────────────────────────────
def test_decide_with_invalid_action_returns_400(client):
    """
    The decide endpoint in projects.py raises HTTPException(400) for any
    action string that is not APPROVE / REJECT / SELECT_OPTION_A / SELECT_OPTION_B.
    This test verifies that guard is exercised and the response body carries
    the offending action string in the detail message.
    """
    proj_id = _create_project(client)

    res = client.post(
        f"/api/projects/{proj_id}/decide",
        json={"decision_action": "FORCE_COMMIT", "notes": "should be rejected"},
    )

    assert res.status_code == 400, (
        f"Expected 400 for invalid decision action, got {res.status_code}: {res.text}"
    )
    detail = res.json()["detail"]
    # The endpoint formats: "Unsupported decision action 'FORCE_COMMIT'."
    assert "FORCE_COMMIT" in detail, f"Error detail did not echo back the invalid action: {detail}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 – POST /run on non-existent project_id → 404
# ─────────────────────────────────────────────────────────────────────────────
def test_run_nonexistent_project_returns_404(client):
    """
    Sending a /run request for a project UUID that does not exist in the DB
    must return 404 with a descriptive 'not found' detail string.
    """
    ghost_id = str(uuid.uuid4())
    res = client.post(f"/api/projects/{ghost_id}/run")

    assert res.status_code == 404, (
        f"Expected 404 for missing project, got {res.status_code}: {res.text}"
    )
    assert "not found" in res.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 – POST /replan on non-existent project_id → 404
# ─────────────────────────────────────────────────────────────────────────────
def test_replan_nonexistent_project_returns_404(client):
    """
    Sending a /replan request for an unknown project must return 404 and not
    cause an unhandled server error (500).
    """
    ghost_id = str(uuid.uuid4())
    res = client.post(
        f"/api/projects/{ghost_id}/replan",
        json={"upfront_budget_limit_inr": 120000.0},
    )

    assert res.status_code == 404, (
        f"Expected 404 for missing project on replan, got {res.status_code}: {res.text}"
    )
    assert "not found" in res.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 – POST /decide on non-existent project_id → 404
# ─────────────────────────────────────────────────────────────────────────────
def test_decide_nonexistent_project_returns_404(client):
    """
    The decide endpoint must return 404 when the project_id is not found,
    regardless of the action verb supplied.
    """
    ghost_id = str(uuid.uuid4())
    res = client.post(
        f"/api/projects/{ghost_id}/decide",
        json={"decision_action": "APPROVE"},
    )

    assert res.status_code == 404, (
        f"Expected 404 for missing project on decide, got {res.status_code}: {res.text}"
    )
    assert "not found" in res.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 – DB cascade-delete propagates through all child tables
# ─────────────────────────────────────────────────────────────────────────────
def test_cascade_delete_user_removes_all_children():
    """
    When a User row is deleted the SQLAlchemy cascade='all, delete-orphan'
    relationship must automatically purge:
      • RelocationProject
      • BudgetLineItem        (via project)
      • ScheduleMilestone     (via project)
      • AgentExecutionLog     (via project)
      • DocumentRecord        (via project)

    This verifies the cascade chain defined in models.py actually works at the
    DB level using the same in-memory SQLite session used by the API tests.
    """
    db = _TestingSessionLocal()
    try:
        # Arrange – build a user with a fully-populated project
        user = User(
            id=str(uuid.uuid4()),
            email="cascade-test@nexmove.ai",
            full_name="Cascade Test User",
        )
        db.add(user)
        db.flush()

        project = RelocationProject(
            id=str(uuid.uuid4()),
            user_id=user.id,
            origin_city="Mumbai",
            destination_city="Hyderabad",
            target_move_date="2026-12-01",
            upfront_budget_limit=120000.0,
            monthly_budget_limit=40000.0,
            home_bhk=1,
            has_pets=False,
            status="DRAFT",
        )
        db.add(project)
        db.flush()

        db.add(BudgetLineItem(
            project_id=project.id,
            tier_category="ONE_TIME_RELOCATION",
            item_name="Synthetic Packers & Movers Freight (Test)",
            amount_inr=32000.0,
            is_confirmed=False,
        ))
        db.add(ScheduleMilestone(
            project_id=project.id,
            task_name="Lease Search Window",
            target_date="2026-11-15",
            prerequisites=[],
            is_critical_path=True,
        ))
        db.add(AgentExecutionLog(
            project_id=project.id,
            agent_name="LogisticsAgent",
            iteration=1,
            status="PASS",
            input_payload={"route": "Mumbai -> Hyderabad"},
            output_payload={"distance_km": 620},
        ))
        db.add(DocumentRecord(
            project_id=project.id,
            file_name="hyd_lease_draft.txt",
            file_type="LEASE",
            extracted_terms={"monthly_rent_inr": 22000.0},
            flagged_clauses=[],
        ))
        db.commit()

        # Verify all children exist before deletion
        assert db.query(RelocationProject).filter_by(user_id=user.id).count() == 1
        assert db.query(BudgetLineItem).filter_by(project_id=project.id).count() == 1
        assert db.query(ScheduleMilestone).filter_by(project_id=project.id).count() == 1
        assert db.query(AgentExecutionLog).filter_by(project_id=project.id).count() == 1
        assert db.query(DocumentRecord).filter_by(project_id=project.id).count() == 1

        # Act – delete the user
        db.delete(user)
        db.commit()

        # Assert – all descendant rows must be gone
        assert db.query(RelocationProject).filter_by(user_id=user.id).count() == 0, \
            "RelocationProject was not cascade-deleted with User"
        assert db.query(BudgetLineItem).filter_by(project_id=project.id).count() == 0, \
            "BudgetLineItem was not cascade-deleted with RelocationProject"
        assert db.query(ScheduleMilestone).filter_by(project_id=project.id).count() == 0, \
            "ScheduleMilestone was not cascade-deleted with RelocationProject"
        assert db.query(AgentExecutionLog).filter_by(project_id=project.id).count() == 0, \
            "AgentExecutionLog was not cascade-deleted with RelocationProject"
        assert db.query(DocumentRecord).filter_by(project_id=project.id).count() == 0, \
            "DocumentRecord was not cascade-deleted with RelocationProject"
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 – LogisticsEstimate model_validator computes total correctly
# ─────────────────────────────────────────────────────────────────────────────
def test_logistics_estimate_total_with_all_components():
    """
    Regression guard: the model_validator(mode='after') in LogisticsEstimate
    must sum base freight + vehicle shipping + transit insurance and round to
    2 decimal places. Exercises the schema independently of the agent so any
    validator regression is caught without needing the tariff dataset.

    All figures are clearly labelled synthetic benchmark values.
    """
    estimate = LogisticsEstimate(
        route="Pune -> Bengaluru (Synthetic Benchmark)",
        distance_km=840,
        vehicle_type="14ft Dedicated Container (Synthetic Benchmark)",
        base_packers_movers_quote_inr=38000.0,   # synthetic tariff
        vehicle_shipping_inr=5000.0,              # synthetic pet/vehicle add-on
        transit_insurance_inr=2000.0,             # synthetic insurance benchmark
        estimated_transit_days=3,
        recommended_pickup_date="2026-11-02",
        estimated_delivery_date="2026-11-05",
        carrier_benchmark_ref="Synthetic Benchmark Carrier (IN-CORR-01)",
        disclaimer="Synthetic benchmark estimate for university prototype demonstration.",
    )

    expected_total = 38000.0 + 5000.0 + 2000.0  # = 45000.0
    assert estimate.total_logistics_inr == expected_total, (
        f"total_logistics_inr mismatch: expected {expected_total}, "
        f"got {estimate.total_logistics_inr}"
    )
    # Ensure disclaimer is preserved and clearly marks synthetic data
    assert "Synthetic" in estimate.disclaimer
    assert "Synthetic Benchmark Carrier" in estimate.carrier_benchmark_ref
