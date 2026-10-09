import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Integer,
    JSON
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    projects = relationship("RelocationProject", back_populates="user", cascade="all, delete-orphan")


class RelocationProject(Base):
    __tablename__ = "relocation_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    origin_city = Column(String(100), nullable=False)
    destination_city = Column(String(100), nullable=False)
    target_move_date = Column(String(10), nullable=False)  # ISO YYYY-MM-DD
    
    # Financial bounds in INR
    upfront_budget_limit = Column(Float, nullable=False)
    monthly_budget_limit = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)

    # Move context
    home_bhk = Column(Integer, default=2, nullable=False)
    has_pets = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)  # DRAFT, REASONING, CONSENSUS_REACHED, AWAITING_USER_DECISION, ACTIVE

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="projects")
    line_items = relationship("BudgetLineItem", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ScheduleMilestone", back_populates="project", cascade="all, delete-orphan")
    agent_logs = relationship("AgentExecutionLog", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("DocumentRecord", back_populates="project", cascade="all, delete-orphan")


class BudgetLineItem(Base):
    __tablename__ = "budget_line_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("relocation_projects.id", ondelete="CASCADE"), nullable=False)
    
    # Category strictly matches three-tier model
    tier_category = Column(String(50), nullable=False)  # ONE_TIME_RELOCATION, INITIAL_HOUSING_OUTLAY, RECURRING_MONTHLY
    item_name = Column(String(255), nullable=False)
    amount_inr = Column(Float, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)

    project = relationship("RelocationProject", back_populates="line_items")


class ScheduleMilestone(Base):
    __tablename__ = "schedule_milestones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("relocation_projects.id", ondelete="CASCADE"), nullable=False)
    
    task_name = Column(String(255), nullable=False)
    target_date = Column(String(25), nullable=False)  # YYYY-MM-DD or date range
    prerequisites = Column(JSON, default=list, nullable=False)
    is_critical_path = Column(Boolean, default=False, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    project = relationship("RelocationProject", back_populates="milestones")


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("relocation_projects.id", ondelete="CASCADE"), nullable=False)
    
    agent_name = Column(String(100), nullable=False)
    iteration = Column(Integer, default=1, nullable=False)
    status = Column(String(50), nullable=False)  # PASS, REVISION_REQUESTED, HARD_CONFLICT, FAILED
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    conflict_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("RelocationProject", back_populates="agent_logs")


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("relocation_projects.id", ondelete="CASCADE"), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # LEASE, MOVER_QUOTE, INVENTORY
    extracted_terms = Column(JSON, nullable=True)
    flagged_clauses = Column(JSON, nullable=True)
    disclaimer = Column(Text, nullable=False, default="Automated extraction for human review only. Not legal advice.")
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("RelocationProject", back_populates="documents")
