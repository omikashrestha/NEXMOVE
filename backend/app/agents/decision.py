from typing import Tuple, List, Optional

from backend.app.schemas.state import RelocationState, AgentMessage
from backend.app.schemas.arbitration import (
    ConflictRecord,
    RevisionRequest,
    EscalationOption,
    SynthesizedPlan
)


class DecisionSynthesisAgent:
    """Master consensus arbitrator, trade-off evaluator, and dynamic replanner."""

    def evaluate_and_arbitrate(self, state: RelocationState) -> RelocationState:
        """Inspects state, enforces hard constraints, triggers bounded revisions, or synthesizes consensus."""
        conflicts: List[ConflictRecord] = []
        trade_offs: List[str] = []
        advisories: List[str] = []

        # 1. Inspect Budget Conflicts
        if state.budget_audit:
            if state.budget_audit.upfront_violation:
                deficit = abs(state.budget_audit.upfront_variance_inr)
                conflicts.append(ConflictRecord(
                    conflict_id="CONF-UPFRONT-BUDGET",
                    source_agent="BudgetAnalystAgent",
                    constraint_category="HARD_CONSTRAINT",
                    metric_name="upfront_budget_limit_inr",
                    description=f"Initial upfront costs exceed budget limit by ₹{deficit:,.2f}.",
                    severity="CRITICAL",
                    delta_value=deficit
                ))

            if state.budget_audit.monthly_violation:
                deficit = abs(state.budget_audit.monthly_variance_inr)
                conflicts.append(ConflictRecord(
                    conflict_id="CONF-MONTHLY-BUDGET",
                    source_agent="BudgetAnalystAgent",
                    constraint_category="HARD_CONSTRAINT",
                    metric_name="monthly_budget_limit_inr",
                    description=f"Recurring monthly costs exceed budget ceiling by ₹{deficit:,.2f}.",
                    severity="CRITICAL",
                    delta_value=deficit
                ))

        # 2. Inspect Housing Hard Constraints (Pet Accommodations)
        if state.profile.has_pets and state.housing_proposal and not state.housing_proposal.pet_friendly:
            conflicts.append(ConflictRecord(
                conflict_id="CONF-HOUSING-PET-RESTRICTION",
                source_agent="HousingResearchAgent",
                constraint_category="HARD_CONSTRAINT",
                metric_name="pet_friendly",
                description="Selected rental property prohibits pets, violating user's mandatory pet requirement.",
                severity="CRITICAL"
            ))

        # 3. Inspect Schedule Conflicts
        if state.schedule_plan and state.schedule_plan.date_conflicts:
            for sc in state.schedule_plan.date_conflicts:
                conflicts.append(ConflictRecord(
                    conflict_id="CONF-SCHEDULE-CLASH",
                    source_agent="ScheduleOptimizationAgent",
                    constraint_category="HARD_CONSTRAINT",
                    metric_name=sc.conflict_type,
                    description=sc.description,
                    severity="HIGH"
                ))

        # 4. Inspect Document Advisories
        if state.document_audit:
            for clause in state.document_audit.flagged_clauses_for_review:
                advisories.append(f"Lease advisory [{clause.clause_title}]: {clause.advisory_note}")
                if clause.risk_level == "HIGH" and state.profile.has_pets and "Pet" in clause.clause_title:
                    conflicts.append(ConflictRecord(
                        conflict_id="CONF-DOC-PET-BAN",
                        source_agent="DocumentIntelligenceAgent",
                        constraint_category="HARD_CONSTRAINT",
                        metric_name="pet_friendly",
                        description="Uploaded lease strictly prohibits pets, violating user hard constraint.",
                        severity="CRITICAL"
                    ))

        state.active_conflicts = conflicts

        # 5. Arbitration Logic: Bounded Revision Loop (Max 2 Iterations)
        hard_conflicts = [c for c in conflicts if c.constraint_category == "HARD_CONSTRAINT"]

        if hard_conflicts:
            if state.iteration_count < 2:
                # Trigger Iteration 1 -> 2 Revision
                primary_conflict = hard_conflicts[0]
                
                if "BUDGET" in primary_conflict.conflict_id:
                    # Calculate required target rent/deposit to balance budget
                    current_rent = state.housing_proposal.monthly_rent_inr if state.housing_proposal else 35000.0
                    deficit = primary_conflict.delta_value or 10000.0
                    
                    target_rent_cap = max(18000.0, round(current_rent - (deficit / 3.0), -2))
                    target_deposit_cap = round(target_rent_cap * 2.0, -2)

                    revision_req = RevisionRequest(
                        target_agent="HousingResearchAgent",
                        conflict_type="UPFRONT_BUDGET_OVERRUN",
                        hard_limits={
                            "max_monthly_rent": target_rent_cap,
                            "max_security_deposit": target_deposit_cap,
                            "prefer_economy_freight": True
                        },
                        soft_relaxations={"allow_commute_increase_mins": 15},
                        rationale=f"Upfront deficit of ₹{deficit:,.2f} requires rent capped at ₹{target_rent_cap:,.2f} with deposit ₹{target_deposit_cap:,.2f}."
                    )
                elif "SCHEDULE" in primary_conflict.conflict_id:
                    suggested_offset = 1
                    if state.schedule_plan and state.schedule_plan.date_conflicts:
                        suggested_offset = state.schedule_plan.date_conflicts[0].suggested_offset_days or 1
                    revision_req = RevisionRequest(
                        target_agent="LogisticsAgent",
                        conflict_type="SCHEDULE_DATE_CLASH",
                        hard_limits={"adjust_delivery_offset_days": suggested_offset},
                        soft_relaxations={},
                        rationale=f"Schedule clash: {primary_conflict.description} Requesting Logistics delivery offset of {suggested_offset} days."
                    )
                else:
                    revision_req = RevisionRequest(
                        target_agent="HousingResearchAgent",
                        conflict_type=primary_conflict.conflict_id,
                        hard_limits={"pets_allowed_required": True},
                        soft_relaxations={},
                        rationale=primary_conflict.description
                    )


                state.active_revision_request = revision_req
                state.iteration_count += 1
                state.status = "REVISING"
                state.history.append(AgentMessage(
                    sender="DecisionSynthesisAgent",
                    recipient=revision_req.target_agent,
                    message_type="REVISION_REQUEST",
                    content=revision_req.rationale,
                    payload=revision_req.model_dump()
                ))
                return state

            else:
                # Iteration cap reached (2 iterations finished without feasible consensus)
                opt_a = EscalationOption(
                    option_id="A",
                    title="Expand Upfront Capital Allowance",
                    trade_off_summary=f"Increase upfront budget by ₹{hard_conflicts[0].delta_value or 15000:,.2f} to secure current property.",
                    upfront_cost_inr=state.budget_audit.total_upfront_outlay_inr if state.budget_audit else 0.0,
                    monthly_cost_inr=state.budget_audit.recurring_monthly_costs.total_recurring_monthly_inr if state.budget_audit else 0.0,
                    commute_mins=state.housing_proposal.commute_to_workplace_mins if state.housing_proposal else 30
                )
                opt_b = EscalationOption(
                    option_id="B",
                    title="Accept Outer Suburb & Shared Freight",
                    trade_off_summary="Expand commute radius beyond 50 minutes and accept shared-container freight (+2 transit days).",
                    upfront_cost_inr=state.profile.upfront_budget_limit_inr,
                    monthly_cost_inr=state.profile.monthly_budget_limit_inr,
                    commute_mins=55
                )

                state.synthesized_plan = SynthesizedPlan(
                    plan_status="AWAITING_USER_DECISION",
                    iteration_count=state.iteration_count,
                    recommended_housing_id=state.housing_proposal.property_id if state.housing_proposal else None,
                    recommended_housing_title=state.housing_proposal.title if state.housing_proposal else None,
                    total_upfront_outlay_inr=state.budget_audit.total_upfront_outlay_inr if state.budget_audit else 0.0,
                    total_recurring_monthly_inr=state.budget_audit.recurring_monthly_costs.total_recurring_monthly_inr if state.budget_audit else 0.0,
                    upfront_buffer_inr=state.budget_audit.upfront_variance_inr if state.budget_audit else 0.0,
                    monthly_headroom_inr=state.budget_audit.monthly_variance_inr if state.budget_audit else 0.0,
                    trade_offs_resolved=[
                        f"Attempted 2 automated revision cycles. Unresolvable budget gap of ₹{hard_conflicts[0].delta_value or 0:,.2f} requires human decision."
                    ],
                    user_advisories=advisories,
                    escalation_options=[opt_a, opt_b]
                )
                state.status = "AWAITING_USER_DECISION"
                state.history.append(AgentMessage(
                    sender="DecisionSynthesisAgent",
                    recipient="User",
                    message_type="SYNTHESIS",
                    content="Automated revisions exhausted. Plan escalated for human resolution.",
                    payload=state.synthesized_plan.model_dump()
                ))
                return state

        # 5. Consensus Reached
        if state.iteration_count > 1:
            trade_offs.append(
                f"Selected {state.housing_proposal.neighborhood} (Rent: ₹{state.housing_proposal.monthly_rent_inr:,.0f}) to eliminate upfront deficit, preserving ₹{state.budget_audit.upfront_variance_inr:,.0f} buffer."
            )
        else:
            trade_offs.append(
                f"First-pass selection optimal: {state.housing_proposal.neighborhood} fits within both upfront and monthly limits with ₹{state.budget_audit.upfront_variance_inr:,.0f} buffer."
            )

        state.synthesized_plan = SynthesizedPlan(
            plan_status="CONSENSUS_REACHED",
            iteration_count=state.iteration_count,
            recommended_housing_id=state.housing_proposal.property_id if state.housing_proposal else None,
            recommended_housing_title=state.housing_proposal.title if state.housing_proposal else None,
            total_upfront_outlay_inr=state.budget_audit.total_upfront_outlay_inr if state.budget_audit else 0.0,
            total_recurring_monthly_inr=state.budget_audit.recurring_monthly_costs.total_recurring_monthly_inr if state.budget_audit else 0.0,
            upfront_buffer_inr=state.budget_audit.upfront_variance_inr if state.budget_audit else 0.0,
            monthly_headroom_inr=state.budget_audit.monthly_variance_inr if state.budget_audit else 0.0,
            transit_pickup_date=state.logistics_estimate.recommended_pickup_date if state.logistics_estimate else None,
            transit_delivery_date=state.logistics_estimate.estimated_delivery_date if state.logistics_estimate else None,
            trade_offs_resolved=trade_offs,
            user_advisories=advisories
        )
        state.status = "CONSENSUS_REACHED"
        state.history.append(AgentMessage(
            sender="DecisionSynthesisAgent",
            recipient="ALL",
            message_type="SYNTHESIS",
            content="Consensus plan successfully synthesized across all domain agents.",
            payload=state.synthesized_plan.model_dump()
        ))
        return state
