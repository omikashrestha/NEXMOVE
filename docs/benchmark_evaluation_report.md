# NEXMOVE: Comprehensive Benchmark Evaluation Report (Milestone 4)

This report details the execution and results of the **10 Reproducible Benchmark Evaluation Scenarios** designed to stress-test the NEXMOVE multi-agent cognitive architecture, bounded revision loops, three-tier financial audit rules, and schedule conflict resolution.

All benchmark runs use curated **synthetic INR datasets** for the Pune $\rightarrow$ Bengaluru relocation corridor.

---

## 1. Benchmark Evaluation Test Matrix

| # | Scenario Name | Test Objective | Execution Command | Result |
| :-: | :--- | :--- | :--- | :-: |
| **1** | **Feasible Relocation** | Verify single-pass consensus in Round 1 with healthy budget limits. | `pytest backend/tests/test_benchmarks.py::test_scenario_1_feasible_relocation` | **PASSED** |
| **2** | **Upfront Budget Overrun** | Verify inter-agent renegotiation and compromise resolution in Round 2. | `pytest backend/tests/test_benchmarks.py::test_scenario_2_upfront_budget_overrun_resolution` | **PASSED** |
| **3** | **Monthly Budget Overrun** | Verify monthly ceiling enforcement and selection of lower-rent properties. | `pytest backend/tests/test_benchmarks.py::test_scenario_3_monthly_budget_overrun_resolution` | **PASSED** |
| **4** | **Impossible Budget Escalation** | Verify bounded revision capping at 2 rounds and escalation to human decision. | `pytest backend/tests/test_benchmarks.py::test_scenario_4_impossible_budget_escalation` | **PASSED** |
| **5** | **Pet Restriction Preservation** | Verify hard constraint (pets allowed) is never silently discarded under revision. | `pytest backend/tests/test_benchmarks.py::test_scenario_5_pet_restriction_preservation` | **PASSED** |
| **6** | **Lease & Delivery Conflict** | Verify date clash detection (delivery before lease start) and schedule offset calculation. | `pytest backend/tests/test_benchmarks.py::test_scenario_6_lease_start_and_delivery_date_conflict` | **PASSED** |
| **7** | **Red-Flag Lease Audit** | Verify Document Intelligence clause extraction, risk flagging, and legal disclaimer. | `pytest backend/tests/test_benchmarks.py::test_scenario_7_red_flag_lease_clauses_audit` | **PASSED** |
| **8** | **Budget Cut Replanning** | Verify dynamic replanning recomputes state and purges stale budget/housing items. | `pytest backend/tests/test_benchmarks.py::test_scenario_8_budget_reduction_and_dynamic_replanning` | **PASSED** |
| **9** | **Move Date Shift Replanning** | Verify changing target move date recalculates all milestones and transit dates. | `pytest backend/tests/test_benchmarks.py::test_scenario_9_move_date_change_and_schedule_replanning` | **PASSED** |
| **10** | **Corrupted / Missing Inputs** | Verify graceful error handling for missing lease files and invalid inputs. | `pytest backend/tests/test_benchmarks.py::test_scenario_10_missing_or_corrupted_inputs_graceful_handling` | **PASSED** |

---

## 2. Detailed Per-Scenario Analysis

### Scenario 1: Feasible Relocation (Single-Pass Consensus)
- **Input**:
  - Origin: Pune, Destination: Bengaluru, Move Date: `2026-11-15`, BHK: 2, Pets: `True`, Workplace: Manyata Tech Park.
  - Upfront Budget Limit: ₹1,80,000 | Monthly Budget Limit: ₹50,000.
- **Expected Behavior**: Single-pass consensus reached in iteration 1 without revision requests; zero active conflicts.
- **Actual Output**:
  - Status: `CONSENSUS_REACHED` (Round 1/2).
  - Housing: `Ring Road Vista 2BHK` (HBR Layout 3rd Block, ₹25,500/mo, deposit ₹51,000, 12 min commute).
  - Logistics: Dedicated 14ft Container (₹48,000, 3 transit days).
  - Upfront Outlay: ₹1,33,000 $\le$ ₹1,80,000 (Buffer: +₹47,000).
  - Recurring Monthly: ₹32,500 $\le$ ₹50,000 (Headroom: +₹17,500).
  - Schedule: Feasible, 0 conflicts.
- **Outcome**: **PASSED**

---

### Scenario 2: Upfront Budget Overrun (Resolved in Round 2)
- **Input**:
  - Origin: Pune, Destination: Bengaluru, Move Date: `2026-11-05`, BHK: 2, Pets: `True`.
  - Upfront Budget Limit: ₹1,20,000 (below initial 2BHK ₹133,000 outlay) | Monthly: ₹45,000.
- **Expected Behavior**: Round 1 triggers `AUDIT_FAIL` from Budget Analyst. Decision Agent issues rent/deposit cap revision request. Agents adapt and achieve consensus in Round 2.
- **Actual Output**:
  - Status: `CONSENSUS_REACHED` (Round 2/2).
  - Housing adapted to: `TechNest Studio 1BHK` (Nagavara Ring Road, ₹18,000/mo, deposit ₹36,000).
  - Logistics adapted to: Shared Economy Transit (₹41,160, 5 transit days).
  - Final Upfront Outlay: ₹1,03,660 $\le$ ₹1,20,000 (Buffer: +₹16,340).
- **Outcome**: **PASSED**

---

### Scenario 3: Monthly Budget Overrun (Resolved in Revision)
- **Input**:
  - Origin: Pune, Destination: Bengaluru, Move Date: `2026-11-05`, BHK: 1, Pets: `False`.
  - Upfront Budget Limit: ₹1,80,000 | Monthly Budget Limit: ₹26,000 (strict monthly cap).
- **Expected Behavior**: Budget Analyst detects monthly overrun if recurring costs exceed ₹26,000; Decision Agent caps monthly rent at ₹22,000; Housing agent selects a compliant lower-rent listing.
- **Actual Output**:
  - Status: `CONSENSUS_REACHED` (Round 2/2).
  - Selected Property: Rent ₹18,000/mo $\le$ ₹22,000.
  - Final Monthly Living Total: ₹24,600/mo $\le$ ₹26,000 limit.
- **Outcome**: **PASSED**

---

### Scenario 4: Impossible Budget & Escalation (Capped at Round 2)
- **Input**:
  - Origin: Pune, Destination: Bengaluru, Move Date: `2026-11-05`, BHK: 2, Pets: `True`.
  - Upfront Budget Limit: ₹40,000 | Monthly Budget Limit: ₹18,000 (impossible for interstate move).
- **Expected Behavior**: Automated revision loop terminates strictly at 2 rounds without entering infinite looping; status marks `AWAITING_USER_DECISION`; outputs Option A and Option B with trade-off summaries.
- **Actual Output**:
  - Status: `AWAITING_USER_DECISION` (Round 2/2).
  - Active Conflicts: `CONF-UPFRONT-BUDGET` (deficit: ₹63,660), `CONF-MONTHLY-BUDGET` (deficit: ₹6,600).
  - Escalation Options:
    - *Option A*: Increase upfront budget by ₹63,660 to secure current unit.
    - *Option B*: Expand commute radius to 55 minutes and accept shared freight.
- **Outcome**: **PASSED**

---

### Scenario 5: Pet Restrictions (Hard Constraint Preserved)
- **Input**:
  - Origin: Pune, Destination: Bengaluru, Move Date: `2026-11-05`, Pets: `True`.
  - Upfront Budget: ₹1,30,000 | Monthly: ₹45,000.
- **Expected Behavior**: The pet restriction is treated as an immutable hard constraint. Non-pet-friendly listings must never be recommended, even under budgetary pressure.
- **Actual Output**:
  - Selected property has `pet_friendly == True`.
  - Cheaper listings with `pet_friendly == False` (e.g. `BLR-KOR-205`) were strictly filtered out during candidate ranking.
- **Outcome**: **PASSED**

---

### Scenario 6: Lease-Start and Delivery-Date Conflict
- **Input**:
  - Target Delivery Date: `2026-11-05`.
  - Apartment Lease Available Date: `2026-11-08` (3 days after movers arrive).
- **Expected Behavior**: Schedule Optimization Agent identifies the chronology clash, creates a `DateConflict` object with `suggested_offset_days = 3`, and flags the schedule as not feasible without date alignment.
- **Actual Output**:
  - `is_feasible`: `False`.
  - Conflict Type: `DELIVERY_BEFORE_LEASE_START`.
  - Description: "Movers arrive on 2026-11-05, but apartment lease is not accessible until 2026-11-08."
  - Suggested Offset: `3 days`.
- **Outcome**: **PASSED**

---

### Scenario 7: Red-Flag Lease Clauses Document Audit
- **Input**: `data/sample_benchmarks/sample_leases/lease_redflag_inr.txt`.
- **Expected Behavior**: Document Intelligence Agent parses text, extracts rent and deposit, identifies non-standard penalty clauses, and outputs the legal disclaimer.
- **Actual Output**:
  - `parse_status`: `SUCCESS`.
  - Extracted Rent: ₹38,000 | Deposit: ₹76,000 | Notice: 30 Days.
  - Flagged Clauses:
    1. *Mandatory Painting / Exit Deduction* (`MEDIUM RISK`) – Non-refundable deduction.
    2. *Strict Pet Prohibition & Forfeiture Risk* (`HIGH RISK`) – Deposit forfeiture penalty.
    3. *Restricted Move-In / Elevator Access Hours* (`MEDIUM RISK`) – Truck unloading limited to 2:00 PM – 4:30 PM.
  - Legal Disclaimer: `"Automated extraction for informational user review only. Does not constitute formal legal counsel."`
- **Outcome**: **PASSED**

---

### Scenario 8: Budget Reduction & Dynamic Replanning
- **Input**:
  - Initial Plan: Upfront budget ₹1,60,000 (Plan selected: `Ring Road Vista 2BHK`, outlay ₹1,33,000).
  - Dynamic Change: Upfront budget cut to ₹1,15,000.
- **Expected Behavior**: Dynamic replanning purges stale line items, recomputes through agents, and returns a new plan within ₹1,15,000.
- **Actual Output**:
  - Previous proposal discarded.
  - New Housing: `TechNest Studio 1BHK` (rent ₹18,000, deposit ₹36,000).
  - New Upfront Outlay: ₹1,03,660 $\le$ ₹1,15,000 (Buffer: ₹11,340).
  - Zero stale attributes retained.
- **Outcome**: **PASSED**

---

### Scenario 9: Move Date Shift & Schedule Replanning
- **Input**:
  - Initial Move Date: `2026-11-05`.
  - Modified Move Date: `2026-12-25`.
- **Expected Behavior**: Delivery date, pickup date, and all 6 critical-path milestones dynamically shift to December with zero stale November dates.
- **Actual Output**:
  - Delivery date shifted from `2026-11-05` to `2026-12-25`.
  - Pickup date shifted from `2026-11-02` to `2026-12-22`.
  - Milestones shifted: Lease Signing (`2026-12-18`), Goods Dispatch (`2026-12-22`), Key Handover (`2026-12-25`), Workplace Start (`2026-12-27`).
- **Outcome**: **PASSED**

---

### Scenario 10: Missing or Corrupted Inputs Graceful Handling
- **Input**:
  - Non-existent document path: `sample_leases/non_existent_file.txt`.
  - Malformed profile with negative budget (`-₹5,000`).
- **Expected Behavior**: Graceful error handling without application crashes; document agent returns `parse_status == "FAILED"`, and Pydantic raises `ValidationError`.
- **Actual Output**:
  - Document parse returned `FAILED` status with 0 clauses and explanatory error note.
  - Pydantic raised `ValidationError: upfront_budget_limit_inr must be greater than 0`.
- **Outcome**: **PASSED**

---

## 3. Automated Benchmark Test Suite Execution

The 10 benchmark scenarios are permanently codified in [`backend/tests/test_benchmarks.py`](file:///Users/omikashrestha/Desktop/NEXMOVE%20-%20flexi/backend/tests/test_benchmarks.py) and executed via:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -v backend/tests/test_benchmarks.py
```
**Result**: 10 passed in 0.19s (100% pass rate).
