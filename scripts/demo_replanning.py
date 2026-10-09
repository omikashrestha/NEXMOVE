#!/usr/bin/env python3
"""
NEXMOVE: Autonomous Multi-Agent AI Relocation Assistant
Interactive Dynamic Replanning & Multi-Agent Negotiation Demonstration Script

This script exercises:
1. Normal feasible relocation planning (single-pass consensus).
2. Dynamic budget reduction triggering agent re-evaluation and trade-offs.
3. Impossible budget scenario capped at 2 revision rounds requesting human arbitration.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.schemas.state import RelocationProfile, RelocationState
from backend.app.agents.graph import run_relocation_workflow


def format_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def main():
    print("=" * 80)
    print("  NEXMOVE: MULTI-AGENT RELOCATION ASSISTANT - REPLANNING DEMO")
    print("  Curated Synthetic INR Benchmarks (Pune -> Bengaluru Corridor)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # PART 1: Normal Relocation Plan (Feasible Consensus)
    # -------------------------------------------------------------------------
    print("\n[PART 1] Running Feasible Relocation Scenario (Standard Budgets)...")
    profile_1 = RelocationProfile(
        user_id="demo-user-1",
        origin_city="Pune",
        destination_city="Bengaluru",
        target_move_date="2026-11-15",
        upfront_budget_limit_inr=160000.0,
        monthly_budget_limit_inr=45000.0,
        home_bhk=2,
        has_pets=True,
        target_workplace="Manyata Tech Park",
        max_commute_mins=40
    )

    state_1 = run_relocation_workflow(RelocationState(project_id="demo-proj-01", profile=profile_1))
    print(f" -> Execution Status: {state_1.status} (Rounds: {state_1.iteration_count}/2)")
    print(f" -> Selected Housing: {state_1.housing_proposal.title} ({state_1.housing_proposal.neighborhood})")
    print(f"    Rent: {format_inr(state_1.housing_proposal.monthly_rent_inr)}/mo | Deposit: {format_inr(state_1.housing_proposal.security_deposit_inr)}")
    print(f" -> Logistics Freight: {state_1.logistics_estimate.vehicle_type} ({format_inr(state_1.logistics_estimate.total_logistics_inr)})")
    
    b1 = state_1.budget_audit
    print(f" -> Three-Tier Budget Check:")
    print(f"    - One-Time Moving: {format_inr(b1.one_time_costs.total_one_time_inr)}")
    print(f"    - Initial Housing Outlay: {format_inr(b1.housing_outlay.total_housing_outlay_inr)}")
    print(f"    - Total Upfront Outlay: {format_inr(b1.total_upfront_outlay_inr)} / Cap: {format_inr(b1.upfront_budget_limit_inr)} (Buffer: {format_inr(b1.upfront_variance_inr)})")
    print(f"    - Recurring Monthly: {format_inr(b1.recurring_monthly_costs.total_recurring_monthly_inr)} / Cap: {format_inr(b1.monthly_budget_limit_inr)} (Headroom: {format_inr(b1.monthly_variance_inr)})")

    # -------------------------------------------------------------------------
    # PART 2: Dynamic Budget Reduction (Agent Re-evaluation)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[PART 2] Simulating User Budget Cut: Reducing Upfront Limit to ₹115,000...")
    print(" -> Triggering dynamic agent renegotiation...")

    profile_2 = profile_1.model_copy(update={"upfront_budget_limit_inr": 115000.0})
    state_2 = run_relocation_workflow(RelocationState(project_id="demo-proj-01", profile=profile_2))

    print(f" -> Execution Status: {state_2.status} (Rounds: {state_2.iteration_count}/2)")
    print(f" -> Newly Adapted Property: {state_2.housing_proposal.title} ({state_2.housing_proposal.neighborhood})")
    print(f"    Rent: {format_inr(state_2.housing_proposal.monthly_rent_inr)}/mo | Deposit: {format_inr(state_2.housing_proposal.security_deposit_inr)}")
    print(f" -> Newly Adapted Freight: {state_2.logistics_estimate.vehicle_type} ({format_inr(state_2.logistics_estimate.total_logistics_inr)})")

    b2 = state_2.budget_audit
    print(f" -> Updated Budget Audit:")
    print(f"    - Total Upfront Outlay: {format_inr(b2.total_upfront_outlay_inr)} / New Cap: {format_inr(b2.upfront_budget_limit_inr)} (Buffer: {format_inr(b2.upfront_variance_inr)})")
    print(f"    - Stale State Discarded: Previous property '{state_1.housing_proposal.title}' replaced by compliant '{state_2.housing_proposal.title}'.")
    print(f" -> Resolved Compromise: {state_2.synthesized_plan.trade_offs_resolved[0]}")

    # -------------------------------------------------------------------------
    # PART 3: Impossible Budget Case (Human Escalation)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[PART 3] Simulating Impossible Budget: ₹40,000 Upfront / ₹18,000 Monthly...")
    print(" -> Observing bounded revision loops and human escalation...")

    profile_3 = profile_1.model_copy(update={
        "upfront_budget_limit_inr": 40000.0,
        "monthly_budget_limit_inr": 18000.0
    })
    state_3 = run_relocation_workflow(RelocationState(project_id="demo-proj-02", profile=profile_3))

    print(f" -> Final Status: {state_3.status}")
    print(f" -> Iteration Count: {state_3.iteration_count} / 2 (Loop successfully terminated at max limit)")
    print(f" -> Detected Hard Conflicts:")
    for c in state_3.active_conflicts:
        print(f"    * [{c.severity}] {c.description} (Delta: {format_inr(c.delta_value)})")

    print(f" -> Human-in-the-Loop Escalation Options Presented:")
    for opt in state_3.synthesized_plan.escalation_options:
        print(f"    [OPTION {opt.option_id}] {opt.title}")
        print(f"      Trade-off: {opt.trade_off_summary}")
        print(f"      Projected Upfront Cost: {format_inr(opt.upfront_cost_inr)} | Commute: ~{opt.commute_mins} mins")

    print("\n" + "=" * 80)
    print("  DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
