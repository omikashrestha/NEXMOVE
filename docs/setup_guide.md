# NEXMOVE Setup & Verification Guide

This guide describes how to set up the local development environment, verify schemas and models, run the test suite, launch the FastAPI backend, run the Next.js prototype dashboard, and import the n8n workflow for NEXMOVE.

---

## 1. Prerequisites
- **Python 3.11, 3.12, or 3.14** (Verified compatible on macOS ARM64 and Linux).
- **Node.js 18+ and npm** (Node v20+ recommended).
- **Git**.
- **n8n** (optional for local visual workflow execution; can be run via n8n desktop or `npx n8n`).

---

## 2. Local Backend Environment Setup

1. **Navigate to the project root**:
   ```bash
   cd "NEXMOVE - flexi"
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Initialize Environment Variables**:
   ```bash
   cp backend/.env.example backend/.env
   ```

5. **Start the FastAPI Backend**:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive OpenAPI docs are available at: `http://localhost:8000/docs`

---

## 3. Running the Pytest Test Suite

Execute the full test suite (51 tests across agents, API endpoints, audits, schemas, and benchmark datasets):
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -v backend/tests
```

### Test Coverage Summary:
- `test_agents.py` (14 tests): Individual agent unit tests and LangGraph state orchestration.
- `test_api.py` (10 tests): FastAPI endpoints for project creation, workflow execution, dynamic replanning, human decisions, document audits, and n8n webhooks.
- `test_audit.py` (9 tests): Revision loop bounds, constraint preservation, budget change replanning, and synthetic labels.
- `test_benchmark_data.py` (3 tests): Integrity checks for synthetic INR datasets.
- `test_db_models.py` (4 tests): SQLAlchemy ORM models, relations, and execution logs.
- `test_schemas.py` (11 tests): Pydantic v2 schemas and three-tier budget calculations.

---

## 4. Next.js Prototype Dashboard Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   npm install
   ```

3. **Build the production application** (to verify type safety and compilation):
   ```bash
   npm run build
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

### Dashboard Capabilities:
- **Interactive Relocation Wizard**: Configure origin/destination, BHK type, move date, upfront budget limit, and monthly budget limit.
- **Run Workflow**: Triggers the FastAPI `/api/projects/{id}/run` orchestration engine.
- **Three-Tier Financial Breakdown**: Live cards showing Upfront Capital Check ($C_{reloc} + C_{housing\_init} \le B_{upfront}$) and Monthly Operational Check ($C_{monthly} \le B_{monthly}$).
- **Interactive Replanning Slider**: Adjust upfront or monthly budget on the fly and trigger `/api/projects/{id}/replan` to test automatic compromise.
- **Agent War Room & Milestones**: Live logs from all 6 agents and a Gantt-style chronological schedule.
- **Human-in-the-Loop Modal**: Appears when unresolvable trade-offs occur, presenting Option A vs Option B for explicit approval.

---

## 5. n8n Workflow Integration

The end-to-end relocation workflow is located at:
`n8n/workflows/WF-E2E-Relocation-Pipeline.json`

### Workflow Topology:
1. **Webhook Intake**: Listens on `POST /webhook/relocation-request`.
2. **FastAPI Create Project**: Calls `POST http://localhost:8000/api/projects`.
3. **FastAPI Run Workflow**: Calls `POST http://localhost:8000/api/projects/{{ $json.project_id }}/run`.
4. **Status Switch Router**: Evaluates execution status (`SUCCESS`, `AWAITING_USER_DECISION`, `FAILED`).
5. **Branch A (Success)**: Formats consensus relocation summary and returns HTTP 200.
6. **Branch B (HITL Decision Required)**: Enters a Wait Node with a webhook resume token, awaiting user selection. Once resumed, calls `POST http://localhost:8000/api/webhooks/n8n/resume`.
7. **Branch C (Failure)**: Formats error diagnostics.

### Importing into n8n:
1. Open n8n (`http://localhost:5678`).
2. Go to **Workflows** -> **Import from File**.
3. Select `n8n/workflows/WF-E2E-Relocation-Pipeline.json`.
4. Activate the workflow or click **Test step** to test in webhook listen mode.

### Sample Curl Request to Trigger Webhook:
```bash
curl -X POST http://localhost:5678/webhook/relocation-request \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "rahul.sharma@example.com",
    "origin_city": "Pune",
    "destination_city": "Bengaluru",
    "bhk_type": "2BHK",
    "move_date": "2026-11-15",
    "has_pets": false,
    "tech_park": "Manyata Tech Park",
    "upfront_budget_limit_inr": 200000,
    "monthly_budget_limit_inr": 45000
  }'
```

---

## 6. Curated Benchmark Datasets (INR)
All benchmark files are located in `data/sample_benchmarks/`:
- `housing_samples_inr.json`: 20 curated synthetic rental properties across Bengaluru and Pune.
- `logistics_tariffs_inr.json`: Standard tariffs for Pune $\rightarrow$ Bengaluru (840 km), Mumbai $\rightarrow$ Bengaluru, Hyderabad $\rightarrow$ Bengaluru, and Delhi $\rightarrow$ Bengaluru.
- `sample_leases/`: Standard and red-flag lease agreements for document intelligence testing.

---

## 7. Team Feature Branches & Authentic Git Configuration

Each team member will work on their assigned feature branch:
- **Omika Shrestha**: `omikashrestha/feat-decision-langgraph`
- **Pritika Kurup**: `pritikakurup/feat-housing-docintel`
- **Neel Khule**: `wyvern10101/feat-budget-schedule-n8n`
- **Tanmay Salunkhe**: `tanmays23/feat-logistics-db-ui`

Each member must configure their verified local git identity prior to making commits:
```bash
git config user.name "<Full Name>"
git config user.email "<verified-github-email>"
```
