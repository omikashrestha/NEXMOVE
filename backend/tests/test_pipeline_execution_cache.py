import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.session import Base, get_db
import backend.app.api.projects as projects_module


_cache_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
_CacheTestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_cache_test_engine)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=_cache_test_engine)

    def _override():
        db = _CacheTestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    prev_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override
    yield
    if prev_override is not None:
        app.dependency_overrides[get_db] = prev_override
    else:
        app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=_cache_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_project_draft_does_not_execute_pipeline(client):
    """Verifies that calling GET on a newly created DRAFT project does not run the pipeline."""
    create_payload = {
        "user_email": "audit_user@example.com",
        "user_name": "Audit Tester",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 180000.0,
        "monthly_budget_limit_inr": 50000.0,
        "home_bhk": 2,
        "has_pets": True,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 40
    }
    create_res = client.post("/api/projects", json=create_payload)
    assert create_res.status_code == 201
    proj_id = create_res.json()["project_id"]

    with patch.object(projects_module, "run_relocation_workflow", wraps=projects_module.run_relocation_workflow) as mock_workflow:
        # GET on DRAFT project
        get_res = client.get(f"/api/projects/{proj_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["status"] == "DRAFT"
        assert data["housing_proposal"] is None
        assert data["logistics_estimate"] is None
        assert data["synthesized_plan"] is None
        # Pipeline must NOT have been called
        assert mock_workflow.call_count == 0


def test_get_project_uses_cache_and_replan_reruns_pipeline(client):
    """
    Verifies that:
    1. Initial run triggers the pipeline once.
    2. Repeated GET requests do NOT re-run the pipeline and return valid cached plan artifacts.
    3. Explicit replanning DOES re-run the pipeline.
    4. Subsequent GET requests serve the newly updated plan without running the pipeline again.
    """
    create_payload = {
        "user_email": "cache_test@example.com",
        "user_name": "Cache Tester",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 200000.0,
        "monthly_budget_limit_inr": 55000.0,
        "home_bhk": 2,
        "has_pets": True,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 40
    }
    create_res = client.post("/api/projects", json=create_payload)
    proj_id = create_res.json()["project_id"]

    with patch.object(projects_module, "run_relocation_workflow", wraps=projects_module.run_relocation_workflow) as mock_workflow:
        # 1. Trigger initial planning
        run_res = client.post(f"/api/projects/{proj_id}/run")
        assert run_res.status_code == 200
        assert mock_workflow.call_count == 1
        initial_plan = run_res.json()
        assert initial_plan["housing_proposal"] is not None
        assert initial_plan["budget_audit"] is not None

        # 2. Repeated GET requests: MUST read from cache without re-executing workflow
        for _ in range(5):
            get_res = client.get(f"/api/projects/{proj_id}")
            assert get_res.status_code == 200
            cached_data = get_res.json()
            assert cached_data["status"] == initial_plan["status"]
            assert cached_data["housing_proposal"]["title"] == initial_plan["housing_proposal"]["title"]
            assert cached_data["budget_audit"]["upfront_budget_limit_inr"] == 200000.0
            # Workflow call count must remain exactly 1!
            assert mock_workflow.call_count == 1

        # 3. Explicit replan: MUST invalidate cache and re-execute workflow
        replan_res = client.post(
            f"/api/projects/{proj_id}/replan",
            json={"upfront_budget_limit_inr": 60000.0}
        )
        assert replan_res.status_code == 200
        # Workflow was invoked a 2nd time for replanning
        assert mock_workflow.call_count == 2
        replanned_data = replan_res.json()
        assert replanned_data["upfront_budget_limit_inr"] == 60000.0

        # 4. Subsequent GET requests: MUST read the updated plan from cache without running workflow again
        for _ in range(3):
            get_after_replan = client.get(f"/api/projects/{proj_id}")
            assert get_after_replan.status_code == 200
            assert get_after_replan.json()["upfront_budget_limit_inr"] == 60000.0
            # Workflow call count must remain exactly 2!
            assert mock_workflow.call_count == 2


def test_user_decision_approval_syncs_cached_status(client):
    """Verifies that APPROVE/REJECT user decisions update both project and cached plan status."""
    create_payload = {
        "user_email": "decision_test@example.com",
        "user_name": "Decision Tester",
        "origin_city": "Pune",
        "destination_city": "Bengaluru",
        "target_move_date": "2026-11-05",
        "upfront_budget_limit_inr": 200000.0,
        "monthly_budget_limit_inr": 55000.0,
        "home_bhk": 2,
        "has_pets": False,
        "target_workplace": "Manyata Tech Park",
        "max_commute_mins": 40
    }
    create_res = client.post("/api/projects", json=create_payload)
    proj_id = create_res.json()["project_id"]

    client.post(f"/api/projects/{proj_id}/run")

    with patch.object(projects_module, "run_relocation_workflow", wraps=projects_module.run_relocation_workflow) as mock_workflow:
        decide_res = client.post(
            f"/api/projects/{proj_id}/decide",
            json={"decision_action": "APPROVE"}
        )
        assert decide_res.status_code == 200
        assert decide_res.json()["status"] == "APPROVED"
        assert decide_res.json()["synthesized_plan"]["plan_status"] == "APPROVED"
        # Decision APPROVE does not need to re-run all agents from scratch
        assert mock_workflow.call_count == 0

        # Subsequent GET should return APPROVED from cache
        get_res = client.get(f"/api/projects/{proj_id}")
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "APPROVED"
        assert get_res.json()["synthesized_plan"]["plan_status"] == "APPROVED"
        assert mock_workflow.call_count == 0
