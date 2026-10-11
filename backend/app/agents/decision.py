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

        # 0. Check for Missing Housing in Destination City
        if not state.housing_proposal:
            conflicts.append(ConflictRecord(
                conflict_id="CONF-NO-HOUSING-FOUND",
                source_agent="HousingResearchAgent",
                constraint_category="HARD_CONSTRAINT",
                metric_name="destination_city",
                description=f"No suitable properties found in {state.profile.destination_city} matching your criteria (BHK: {state.profile.home_bhk}, Pets: {state.profile.has_pets}).",
                severity="CRITICAL"
            ))
            state.active_conflicts = conflicts
            state.status = "NO_HOUSING_AVAILABLE"
            state.synthesized_plan = SynthesizedPlan(
                plan_status="NO_HOUSING_AVAILABLE",
                iteration_count=state.iteration_count,
                recommended_housing_id=None,
                recommended_housing_title=None,
                total_upfront_outlay_inr=state.logistics_estimate.total_logistics_inr if state.logistics_estimate else 0.0,
                total_recurring_monthly_inr=0.0,
                upfront_buffer_inr=0.0,
                monthly_headroom_inr=0.0,
                transit_pickup_date=state.logistics_estimate.recommended_pickup_date if state.logistics_estimate else None,
                transit_delivery_date=state.logistics_estimate.estimated_delivery_date if state.logistics_estimate else None,
                trade_offs_resolved=[
                    f"No properties available in {state.profile.destination_city} in the synthetic benchmark dataset."
                ],
                user_advisories=[
                    f"Please choose another destination city or adjust your bedroom/pet requirements."
                ],
                escalation_options=[]
            )
            state.history.append(AgentMessage(
                sender="DecisionSynthesisAgent",
                recipient="User",
                message_type="SYNTHESIS",
                content=f"No housing inventory available in {state.profile.destination_city}.",
                payload=state.synthesized_plan.model_dump()
            ))
            return state

        # 1. Inspect Budget Conflicts
        if state.budget_audit:
            if state.budget_audit.upfront_violation:
                deficit = abs(state.budget_audit.upfront_variance_inr)
                conflicts.append(ConflictRecord(
                    conflict_id="CONF-UPFRONT-BUDGET",
                    source_agent="BudgetAnalystAgent",
                    constraint_category="HARD_CONSTRAINT",
                    metric_name="upfront_budget_limit_inr",
                    description=f"Initial upfront costs exceed budget limit of ₹{state.profile.upfront_budget_limit_inr:,.0f} by ₹{deficit:,.2f}.",
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
                    description=f"Recurring monthly costs exceed monthly ceiling of ₹{state.profile.monthly_budget_limit_inr:,.0f} by ₹{deficit:,.2f}.",
                    severity="CRITICAL",
                    delta_value=deficit
                ))

        # 2. Inspect Housing Hard Constraints (Pet Accommodations)
        if state.profile.has_pets and not state.housing_proposal.pet_friendly:
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
                
                if "UPFRONT-BUDGET" in primary_conflict.conflict_id:
                    current_rent = state.housing_proposal.monthly_rent_inr
                    deficit = primary_conflict.delta_value or 10000.0
                    target_rent_cap = max(12000.0, round(current_rent - (deficit / 3.0), -2))
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
                elif "MONTHLY-BUDGET" in primary_conflict.conflict_id:
                    deficit = primary_conflict.delta_value or 5000.0
                    target_rent_cap = max(10000.0, round(state.housing_proposal.monthly_rent_inr - deficit, -2))
                    revision_req = RevisionRequest(
                        target_agent="HousingResearchAgent",
                        conflict_type="MONTHLY_BUDGET_OVERRUN",
                        hard_limits={"max_monthly_rent": target_rent_cap},
                        soft_relaxations={"allow_commute_increase_mins": 15},
                        rationale=f"Monthly deficit of ₹{deficit:,.2f} requires monthly rent capped at ₹{target_rent_cap:,.2f}."
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
                # Build real alternatives that honestly reflect the constraint violation
                primary_conflict = hard_conflicts[0]
                upfront_outlay = state.budget_audit.total_upfront_outlay_inr if state.budget_audit else 0.0
                monthly_outlay = state.budget_audit.recurring_monthly_costs.total_recurring_monthly_inr if state.budget_audit else 0.0
                commute_val = state.housing_proposal.commute_to_workplace_mins if state.housing_proposal else 30

                if "MONTHLY-BUDGET" in primary_conflict.conflict_id:
                    deficit = primary_conflict.delta_value or 5000.0
                    opt_a = EscalationOption(
                        option_id="A",
                        title="Increase Monthly Living Budget",
                        trade_off_summary=f"Increase monthly budget by ₹{deficit:,.0f} (to ₹{monthly_outlay:,.0f}/mo) to secure {state.housing_proposal.title} in {state.housing_proposal.neighborhood}.",
                        upfront_cost_inr=upfront_outlay,
                        monthly_cost_inr=monthly_outlay,
                        commute_mins=commute_val
                    )
                    opt_b = EscalationOption(
                        option_id="B",
                        title="Accept Smaller Apartment or Distant Suburb",
                        trade_off_summary=f"Keep monthly budget at ₹{state.profile.monthly_budget_limit_inr:,.0f}/mo by expanding commute beyond {commute_val + 20} mins.",
                        upfront_cost_inr=upfront_outlay,
                        monthly_cost_inr=state.profile.monthly_budget_limit_inr,
                        commute_mins=commute_val + 20
                    )
                else:
                    deficit = primary_conflict.delta_value or 15000.0
                    econ_freight_savings = round((state.logistics_estimate.base_packers_movers_quote_inr * 0.18), -2) if state.logistics_estimate else 5000.0
                    opt_b_upfront = max(state.profile.upfront_budget_limit_inr, round(upfront_outlay - econ_freight_savings, -2))

                    opt_a = EscalationOption(
                        option_id="A",
                        title="Expand Upfront Moving Budget",
                        trade_off_summary=f"Increase upfront budget by ₹{deficit:,.0f} (to ₹{upfront_outlay:,.0f}) to secure {state.housing_proposal.title} with dedicated freight.",
                        upfront_cost_inr=upfront_outlay,
                        monthly_cost_inr=monthly_outlay,
                        commute_mins=commute_val
                    )
                    opt_b = EscalationOption(
                        option_id="B",
                        title="Shared Economy Freight & Extended Commute",
                        trade_off_summary=f"Switch to shared-container freight (saving ~₹{econ_freight_savings:,.0f}) and accept higher commute ({commute_val + 15} mins). Upfront cost: ₹{opt_b_upfront:,.0f}.",
                        upfront_cost_inr=opt_b_upfront,
                        monthly_cost_inr=monthly_outlay,
                        commute_mins=commute_val + 15
                    )

                state.synthesized_plan = SynthesizedPlan(
                    plan_status="AWAITING_USER_DECISION",
                    iteration_count=state.iteration_count,
                    recommended_housing_id=state.housing_proposal.property_id,
                    recommended_housing_title=state.housing_proposal.title,
                    total_upfront_outlay_inr=upfront_outlay,
                    total_recurring_monthly_inr=monthly_outlay,
                    upfront_buffer_inr=state.budget_audit.upfront_variance_inr if state.budget_audit else 0.0,
                    monthly_headroom_inr=state.budget_audit.monthly_variance_inr if state.budget_audit else 0.0,
                    trade_offs_resolved=[
                        f"Attempted 2 automated revision cycles. Unresolvable constraint: {primary_conflict.description} Requires user decision."
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
                f"Selected {state.housing_proposal.neighborhood} in {state.housing_proposal.city} (Rent: ₹{state.housing_proposal.monthly_rent_inr:,.0f}) to eliminate deficit, preserving ₹{state.budget_audit.upfront_variance_inr:,.0f} buffer."
            )
        else:
            trade_offs.append(
                f"First-pass selection optimal: {state.housing_proposal.neighborhood} in {state.housing_proposal.city} fits within both upfront and monthly limits with ₹{state.budget_audit.upfront_variance_inr:,.0f} upfront buffer and ₹{state.budget_audit.monthly_variance_inr:,.0f}/mo headroom."
            )

        state.synthesized_plan = SynthesizedPlan(
            plan_status="CONSENSUS_REACHED",
            iteration_count=state.iteration_count,
            recommended_housing_id=state.housing_proposal.property_id,
            recommended_housing_title=state.housing_proposal.title,
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
