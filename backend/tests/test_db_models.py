import uuid
from backend.app.db.models import (
    User,
    RelocationProject,
    BudgetLineItem,
    ScheduleMilestone,
    AgentExecutionLog,
    DocumentRecord
)


def test_user_and_project_creation(db_session):
    user = User(
        id=str(uuid.uuid4()),
        email="omika@example.com",
        full_name="Omika Shrestha"
    )
    db_session.add(user)
    db_session.commit()

    project = RelocationProject(
        id=str(uuid.uuid4()),
        user_id=user.id,
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit=150000.0,
        monthly_budget_limit=45000.0,
        currency="INR",
        home_bhk=2,
        has_pets=True,
        status="DRAFT"
    )
    db_session.add(project)
    db_session.commit()

    fetched = db_session.query(RelocationProject).filter_by(id=project.id).first()
    assert fetched is not None
    assert fetched.user.email == "omika@example.com"
    assert fetched.currency == "INR"
    assert fetched.upfront_budget_limit == 150000.0


def test_budget_line_items_relationships(db_session):
    user = User(id=str(uuid.uuid4()), email="test@nexmove.ai", full_name="Test User")
    db_session.add(user)
    db_session.commit()

    project = RelocationProject(
        id=str(uuid.uuid4()),
        user_id=user.id,
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit=150000.0,
        monthly_budget_limit=45000.0
    )
    db_session.add(project)
    db_session.commit()

    item1 = BudgetLineItem(
        project_id=project.id,
        tier_category="ONE_TIME_RELOCATION",
        item_name="Packers & Movers Freight",
        amount_inr=38000.0,
        is_confirmed=True
    )
    item2 = BudgetLineItem(
        project_id=project.id,
        tier_category="INITIAL_HOUSING_OUTLAY",
        item_name="Security Deposit",
        amount_inr=60000.0,
        is_confirmed=False
    )
    item3 = BudgetLineItem(
        project_id=project.id,
        tier_category="RECURRING_MONTHLY",
        item_name="Monthly Base Rent",
        amount_inr=30000.0,
        is_confirmed=False
    )
    db_session.add_all([item1, item2, item3])
    db_session.commit()

    items = db_session.query(BudgetLineItem).filter_by(project_id=project.id).all()
    assert len(items) == 3
    tiers = {i.tier_category for i in items}
    assert tiers == {"ONE_TIME_RELOCATION", "INITIAL_HOUSING_OUTLAY", "RECURRING_MONTHLY"}


def test_schedule_milestone_json_prerequisites(db_session):
    user = User(id=str(uuid.uuid4()), email="neel@example.com", full_name="Neel Khule")
    db_session.add(user)
    db_session.commit()

    project = RelocationProject(
        id=str(uuid.uuid4()),
        user_id=user.id,
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit=150000.0,
        monthly_budget_limit=45000.0
    )
    db_session.add(project)
    db_session.commit()

    m1 = ScheduleMilestone(
        project_id=project.id,
        task_name="Lease Finalization",
        target_date="2026-10-28",
        prerequisites=[],
        is_critical_path=True
    )
    m2 = ScheduleMilestone(
        project_id=project.id,
        task_name="Movers Dispatch",
        target_date="2026-11-01",
        prerequisites=["Lease Finalization"],
        is_critical_path=True
    )
    db_session.add_all([m1, m2])
    db_session.commit()

    milestones = db_session.query(ScheduleMilestone).filter_by(project_id=project.id).all()
    assert len(milestones) == 2
    assert milestones[1].prerequisites == ["Lease Finalization"]


def test_agent_execution_logs_and_document_record(db_session):
    user = User(id=str(uuid.uuid4()), email="pritika@example.com", full_name="Pritika Kurup")
    db_session.add(user)
    db_session.commit()

    project = RelocationProject(
        id=str(uuid.uuid4()),
        user_id=user.id,
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-05",
        upfront_budget_limit=150000.0,
        monthly_budget_limit=45000.0
    )
    db_session.add(project)
    db_session.commit()

    log = AgentExecutionLog(
        project_id=project.id,
        agent_name="HousingResearchAgent",
        iteration=1,
        status="PASS",
        input_payload={"destination": "Bengaluru", "bhk": 2},
        output_payload={"property_id": "BLR-HSR-201", "rent": 30000.0}
    )
    doc = DocumentRecord(
        project_id=project.id,
        file_name="lease_standard_inr.txt",
        file_type="LEASE",
        extracted_terms={"monthly_rent": 30000.0, "deposit": 60000.0},
        flagged_clauses=[]
    )
    db_session.add_all([log, doc])
    db_session.commit()

    fetched_log = db_session.query(AgentExecutionLog).filter_by(project_id=project.id).first()
    fetched_doc = db_session.query(DocumentRecord).filter_by(project_id=project.id).first()
    assert fetched_log.agent_name == "HousingResearchAgent"
    assert fetched_doc.file_name == "lease_standard_inr.txt"
    assert "Not legal advice" in fetched_doc.disclaimer
