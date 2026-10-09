from datetime import datetime, timedelta
from typing import List, Optional

from backend.app.schemas.state import RelocationProfile
from backend.app.schemas.logistics import LogisticsEstimate
from backend.app.schemas.housing import HousingProposal
from backend.app.schemas.document import DocumentAudit
from backend.app.schemas.schedule import MilestoneItem, DateConflict, SchedulePlan


class ScheduleOptimizationAgent:
    """Specialized agent building sequenced critical-path relocation timelines and detecting date clashes."""

    def build_schedule(
        self,
        profile: RelocationProfile,
        logistics_estimate: LogisticsEstimate,
        housing_proposal: HousingProposal,
        document_audit: Optional[DocumentAudit] = None,
        lease_start_date: Optional[str] = None
    ) -> SchedulePlan:
        """Constructs topological milestones and validates chronology."""
        conflicts: List[DateConflict] = []

        try:
            target_delivery = datetime.strptime(logistics_estimate.estimated_delivery_date, "%Y-%m-%d")
            pickup_dt = datetime.strptime(logistics_estimate.recommended_pickup_date, "%Y-%m-%d")
        except ValueError:
            target_delivery = datetime.now() + timedelta(days=15)
            pickup_dt = target_delivery - timedelta(days=3)

        lease_dt = None
        if lease_start_date:
            try:
                lease_dt = datetime.strptime(lease_start_date, "%Y-%m-%d")
            except ValueError:
                pass
        else:
            lease_dt = target_delivery  # Default lease starts on delivery day

        # 1. Date Conflict Detection: Delivery Before Lease Access
        if lease_dt and target_delivery < lease_dt:
            conflicts.append(DateConflict(
                conflict_type="DELIVERY_BEFORE_LEASE_START",
                conflicting_task_ids=["M-03", "M-04"],
                description=f"Movers arrive on {target_delivery.strftime('%Y-%m-%d')}, but apartment lease is not accessible until {lease_dt.strftime('%Y-%m-%d')}.",
                suggested_offset_days=(lease_dt - target_delivery).days
            ))

        # Check document restriction annotations
        unloading_note = "Key Handover & Moving Van Delivery Unloading"
        if document_audit:
            for clause in document_audit.flagged_clauses_for_review:
                if "Elevator" in clause.clause_title or "Hours" in clause.clause_title:
                    unloading_note += f" [Note: Coordinate strictly within permitted hours]"

        # 2. Build Topological Milestones
        milestones = [
            MilestoneItem(
                step_id="M-01",
                task_name="Lease Agreement Signing & Advance Payment",
                target_date=(pickup_dt - timedelta(days=4)).strftime("%Y-%m-%d"),
                prerequisites=[],
                is_critical_path=True,
                owner_party="Tenant & Landlord"
            ),
            MilestoneItem(
                step_id="M-02",
                task_name="Utility & Internet Transfer Initiation",
                target_date=(pickup_dt - timedelta(days=2)).strftime("%Y-%m-%d"),
                prerequisites=["M-01"],
                is_critical_path=False,
                owner_party="User"
            ),
            MilestoneItem(
                step_id="M-03",
                task_name="Packers & Movers Goods Loading & Dispatch",
                target_date=pickup_dt.strftime("%Y-%m-%d"),
                prerequisites=["M-01"],
                is_critical_path=True,
                owner_party="Packers & Movers"
            ),
            MilestoneItem(
                step_id="M-04",
                task_name="Highway Interstate Transit Window",
                target_date=f"{pickup_dt.strftime('%Y-%m-%d')} to {target_delivery.strftime('%Y-%m-%d')}",
                prerequisites=["M-03"],
                is_critical_path=True,
                owner_party="Packers & Movers"
            ),
            MilestoneItem(
                step_id="M-05",
                task_name=unloading_note,
                target_date=target_delivery.strftime("%Y-%m-%d"),
                prerequisites=["M-04"],
                is_critical_path=True,
                owner_party="User & Movers"
            ),
            MilestoneItem(
                step_id="M-06",
                task_name="Office Resumption / First Day at Workplace",
                target_date=(target_delivery + timedelta(days=2)).strftime("%Y-%m-%d"),
                prerequisites=["M-05"],
                is_critical_path=True,
                owner_party="User"
            )
        ]

        is_feasible = (len(conflicts) == 0)

        return SchedulePlan(
            relocation_start_date=(pickup_dt - timedelta(days=4)).strftime("%Y-%m-%d"),
            completion_date=(target_delivery + timedelta(days=2)).strftime("%Y-%m-%d"),
            is_feasible=is_feasible,
            critical_path_milestones=milestones,
            date_conflicts=conflicts
        )
