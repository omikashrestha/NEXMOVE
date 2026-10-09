import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.session import Base
from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.budget import (
    OneTimeRelocationCosts,
    InitialHousingOutlay,
    RecurringMonthlyCosts,
    BudgetAudit
)


@pytest.fixture
def db_session():
    """In-memory SQLite session fixture for isolated database testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_profile() -> RelocationProfile:
    """Standard relocation profile for Pune -> Bengaluru move."""
    return RelocationProfile(
        user_id="usr-test-101",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit_inr=150000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )


@pytest.fixture
def sample_housing_proposal() -> HousingProposal:
    """Sample HousingProposal for HSR Layout unit."""
    return HousingProposal(
        property_id="BLR-HSR-201",
        title="Green Glen Garden 2BHK",
        city="Bengaluru",
        neighborhood="HSR Layout Sector 2",
        bhk=2,
        monthly_rent_inr=30000.0,
        security_deposit_inr=60000.0,
        society_maintenance_inr=3500.0,
        move_in_fee_inr=2000.0,
        pet_friendly=True,
        commute_to_workplace_mins=25,
        safety_score_index=8.5,
        datasource="SAMPLE_BENCHMARK_INR"
    )


@pytest.fixture
def sample_logistics_estimate() -> LogisticsEstimate:
    """Sample LogisticsEstimate for Pune -> Bengaluru 2BHK move."""
    return LogisticsEstimate(
        route="Pune -> Bengaluru",
        distance_km=840,
        vehicle_type="14ft Dedicated Container",
        base_packers_movers_quote_inr=38000.0,
        vehicle_shipping_inr=5000.0,
        transit_insurance_inr=2000.0,
        estimated_transit_days=3,
        recommended_pickup_date="2026-11-01",
        estimated_delivery_date="2026-11-04"
    )
