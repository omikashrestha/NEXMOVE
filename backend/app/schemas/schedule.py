from typing import List
from pydantic import BaseModel, Field


class MilestoneItem(BaseModel):
    step_id: str = Field(..., description="Unique step identifier (e.g. M-01)")
    task_name: str = Field(..., description="Actionable title for the relocation milestone")
    target_date: str = Field(..., description="Date or date range (YYYY-MM-DD)")
    prerequisites: List[str] = Field(default_factory=list, description="IDs of preceding tasks that must complete first")
    is_critical_path: bool = Field(False, description="Whether this task is on the delay-sensitive critical path")
    owner_party: str = Field("User", description="Responsible party: User, Landlord, Packers & Movers, Employer")


class DateConflict(BaseModel):
    conflict_type: str = Field(..., description="DELIVERY_BEFORE_LEASE_START, NOTICE_TOO_SHORT, etc.")
    conflicting_task_ids: List[str] = Field(..., description="Task IDs involved in the chronological clash")
    description: str = Field(..., description="Explanation of the chronological impossibility")
    suggested_offset_days: int = Field(0, description="Recommended date shift to restore feasibility")


class SchedulePlan(BaseModel):
    relocation_start_date: str = Field(..., description="First milestone commencement date (YYYY-MM-DD)")
    completion_date: str = Field(..., description="Final move-in and handover completion date (YYYY-MM-DD)")
    is_feasible: bool = Field(True, description="True if dependency graph has no circularities or chronological clashes")
    critical_path_milestones: List[MilestoneItem] = Field(default_factory=list)
    date_conflicts: List[DateConflict] = Field(default_factory=list)
