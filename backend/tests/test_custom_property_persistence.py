import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.session import Base, get_db
from backend.app.db.models import User, RelocationProject, CustomPropertyRecord
from backend.app.agents.housing import HousingResearchAgent, _CUSTOM_LISTINGS
from backend.app.schemas.state import RelocationProfile


_custom_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
_CustomTestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_custom_test_engine)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=_custom_test_engine)

    def _override():
        db = _CustomTestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    prev_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override
    _CUSTOM_LISTINGS.clear()
    yield
    _CUSTOM_LISTINGS.clear()
    if prev_override is not None:
        app.dependency_overrides[get_db] = prev_override
    else:
        app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=_custom_test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_db():
    db = _CustomTestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_custom_property_record_model(test_db):
    """Verifies CustomPropertyRecord schema, fields, and cascade deletion."""
    user = User(id=str(uuid.uuid4()), email="custom_test@nexmove.ai", full_name="Custom Tester")
    test_db.add(user)
    test_db.commit()

    project = RelocationProject(
        id=str(uuid.uuid4()),
        user_id=user.id,
        origin_city="Delhi NCR",
        destination_city="Patna",
        target_move_date="2026-12-01",
        upfront_budget_limit=150000.0,
        monthly_budget_limit=40000.0,
        home_bhk=2,
        has_pets=False,
        status="DRAFT"
    )
    test_db.add(project)
    test_db.commit()

    prop = CustomPropertyRecord(
        id="MANUAL-TEST01",
        project_id=project.id,
        title="2 BHK in Kankarbagh",
        city="Patna",
        neighborhood="Kankarbagh",
        bhk=2,
        monthly_rent_inr=22000.0,
        security_deposit_inr=44000.0,
        society_maintenance_inr=1500.0,
        move_in_fee_inr=500.0,
        pet_friendly=True,
        commute_to_workplace_mins=25,
        safety_score_index=8.5,
        datasource="USER_MANUAL_ENTRY",
        property_type="Independent Floor",
        is_verified=True
    )
    test_db.add(prop)
    test_db.commit()

    fetched = test_db.query(CustomPropertyRecord).filter_by(id="MANUAL-TEST01").first()
    assert fetched is not None
    assert fetched.project_id == project.id
    assert fetched.city == "Patna"
    assert fetched.monthly_rent_inr == 22000.0
    assert fetched.pet_friendly is True

    # Test cascade delete: deleting project removes associated custom property
    test_db.delete(project)
    test_db.commit()
    assert test_db.query(CustomPropertyRecord).filter_by(id="MANUAL-TEST01").first() is None


def test_custom_property_persists_across_memory_wipe(test_db):
    """Proves that custom listing registered in DB survives clearing _CUSTOM_LISTINGS in-memory dict."""
    user = User(id=str(uuid.uuid4()), email="wipe_test@nexmove.ai", full_name="Wipe Tester")
    test_db.add(user)
    test_db.commit()

    project = RelocationProject(
        id=str(uuid.uuid4()),
        user_id=user.id,
        origin_city="Mumbai",
        destination_city="Bhopal",
        target_move_date="2026-11-20",
        upfront_budget_limit=180000.0,
        monthly_budget_limit=50000.0,
        home_bhk=3,
        has_pets=True,
        status="DRAFT"
    )
    test_db.add(project)
    test_db.commit()

    custom_id = "MANUAL-BHP01"
    HousingResearchAgent.register_custom_listing({
        "property_id": custom_id,
        "project_id": project.id,
        "title": "3 BHK Lakeview Residency",
        "city": "Bhopal",
        "neighborhood": "Arera Colony",
        "bhk": 3,
        "monthly_rent_inr": 28000.0,
        "security_deposit_inr": 56000.0,
        "society_maintenance_inr": 2500.0,
        "move_in_fee_inr": 0.0,
        "pet_friendly": True,
        "commute_to_workplace_mins": 20,
        "property_type": "Gated Society Apartment"
    }, db=test_db)
    test_db.commit()

    # SIMULATE SERVER RESTART / PROCESS REBOOT
    _CUSTOM_LISTINGS.clear()
    assert len(_CUSTOM_LISTINGS) == 0

    # Instantiate fresh HousingResearchAgent
    agent = HousingResearchAgent(db=test_db)
    profile = RelocationProfile(
        user_id=user.id,
        origin_city="Mumbai",
        destination_city="Bhopal",
        target_move_date="2026-11-20",
        upfront_budget_limit_inr=180000.0,
        monthly_budget_limit_inr=50000.0,
        home_bhk=3,
        has_pets=True,
        selected_property_id=custom_id
    )

    found_proposal = agent.search(profile)
    assert found_proposal is not None
    assert found_proposal.property_id == custom_id
    assert found_proposal.city == "Bhopal"
    assert found_proposal.monthly_rent_inr == 28000.0
    assert found_proposal.neighborhood == "Arera Colony"

    options = agent.search_all(profile)
    assert any(opt.property_id == custom_id for opt in options)


def test_api_custom_property_endpoint_persists_and_supports_replanning(client, test_db):
    """End-to-end test: add custom property, clear in-memory cache, then replan successfully."""
    create_res = client.post("/api/projects", json={
        "user_email": "e2e_custom@nexmove.ai",
        "user_name": "E2E Relocator",
        "origin_city": "Pune",
        "destination_city": "Indore",
        "target_move_date": "2026-12-15",
        "upfront_budget_limit_inr": 200000,
        "monthly_budget_limit_inr": 45000,
        "home_bhk": 2,
        "has_pets": False,
        "target_workplace": "Vijay Nagar",
        "max_commute_mins": 30
    })
    assert create_res.status_code == 201
    project_id = create_res.json()["project_id"]

    # Initial run for unsupported city produces NO_HOUSING_AVAILABLE
    run_res = client.post(f"/api/projects/{project_id}/run")
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "NO_HOUSING_AVAILABLE"

    # Add custom property via API
    add_prop_res = client.post(f"/api/projects/{project_id}/custom-property", json={
        "title": "2 BHK Apartment in Vijay Nagar",
        "neighborhood": "Vijay Nagar",
        "bhk": 2,
        "monthly_rent_inr": 24000,
        "security_deposit_inr": 48000,
        "society_maintenance_inr": 2000,
        "commute_to_workplace_mins": 15,
        "pet_friendly": False,
        "property_type": "Apartment"
    })
    assert add_prop_res.status_code == 200
    prop_data = add_prop_res.json()
    assert prop_data["housing_proposal"] is not None
    custom_prop_id = prop_data["housing_proposal"]["property_id"]
    assert custom_prop_id.startswith("MANUAL-")
    assert prop_data["housing_proposal"]["city"] == "Indore"
    assert prop_data["status"] == "CONSENSUS_REACHED"

    # Verify record was written to the SQLite custom_properties table
    db_record = test_db.query(CustomPropertyRecord).filter_by(id=custom_prop_id).first()
    assert db_record is not None
    assert db_record.project_id == project_id
    assert db_record.city == "Indore"
    assert db_record.monthly_rent_inr == 24000.0

    # SIMULATE SERVER RESTART / IN-MEMORY CACHE CLEAR
    _CUSTOM_LISTINGS.clear()
    assert len(_CUSTOM_LISTINGS) == 0

    # GET request still returns valid cached plan with custom property
    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["housing_proposal"]["property_id"] == custom_prop_id

    # Dynamic replanning must rerun the pipeline without losing the custom property
    replan_res = client.post(f"/api/projects/{project_id}/replan", json={
        "max_commute_mins": 35
    })
    assert replan_res.status_code == 200
    replanned_data = replan_res.json()
    assert replanned_data["housing_proposal"] is not None
    assert replanned_data["housing_proposal"]["property_id"] == custom_prop_id
    assert replanned_data["housing_proposal"]["city"] == "Indore"
    assert replanned_data["status"] == "CONSENSUS_REACHED"
