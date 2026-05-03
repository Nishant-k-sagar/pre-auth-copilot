# Pre-Authorization Copilot — Workflow Guide

This guide walks you through running, testing, and extending the Pre-Authorization Copilot. Follow the steps in order, and refer to the troubleshooting section if you encounter issues.

---

## Quick Start: Running Your First Analysis

### Prerequisites

1. Python 3.10+ installed
2. Node.js 18+ installed
3. MISTRAL_API_KEY environment variable set
4. The project dependencies installed:
   ```bash
   cd backend && pip install -r requirements.txt
   cd frontend && npm install
   ```

### Step 1: Start the Backend

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`.

### Step 2: Start the Frontend

```bash
cd frontend
npm run dev
```

The web interface will be available at `http://localhost:3000`.

### Step 3: Run Your First Analysis

1. Open `http://localhost:3000` in your browser
2. Select a training case from the dropdown (e.g., PA-003)
3. Click "Analyze Case"
4. View the results in the result panel

---

## Development Workflow

### Step 1: Data Parsing

Run the workbook parser to generate JSON data files:

```bash
cd backend
python scripts/parse_workbook.py
```

**Expected output:**
- `data/training_cases.json` — 10 training cases
- `data/patient_data_schema.json` — 30 fields with descriptions
- `data/complex_case.json` — 19 rows of complex case data
- `data/expected_outcome.json` — gold standard outcomes

**For developers:** The parser reads from `data/preauth_workbook.xlsx` and outputs JSON files for the API to serve.

### Step 2: Backend Schema & Pipeline

The backend is organized as a 3-step pipeline:

| File | Purpose |
|------|---------|
| `skill/schema.py` | Pydantic models for input/output validation |
| `skill/criteria_registry.py` | Service-type to criteria mapping |
| `skill/prompts.py` | LLM prompt templates |
| `skill/normalizer.py` | Step 1: Extract and normalize case data |
| `skill/evaluator.py` | Step 2: Evaluate against criteria |
| `skill/assembler.py` | Step 3: Validate and assemble output |
| `skill/pipeline.py` | Orchestrates the 3 steps |
| `main.py` | FastAPI application and routes |

**For developers:** Each step is independent. You can test them individually:

```python
# Test normalization
from skill.normalizer import normalize
# Test evaluation
from skill.evaluator import evaluate
# Test assembly
from skill.assembler import assemble
```

### Step 3: Complex Case Execution & Validation

Run the complex case script:

```bash
cd backend
python scripts/run_complex_case.py
```

This produces `outputs/complex_case_output.json` with the full analysis.

Run the test suite:

```bash
cd backend
pytest tests/test_complex_case.py -v
pytest tests/test_pipeline.py -v
```

### Step 4: Frontend Development

The frontend is a Next.js 14 application:

| Directory | Purpose |
|-----------|---------|
| `app/` | Pages and layouts |
| `components/` | Reusable UI components |
| `lib/` | API client and types |
| `hooks/` | React hooks for data fetching |

**For developers:** The frontend uses TypeScript types that mirror the backend Pydantic models. See [`frontend/lib/types.ts`](frontend/lib/types.ts).

### Step 5: Integration Testing

Run all 10 training cases through the pipeline:

```bash
curl -X GET http://localhost:8000/api/validate-all
```

Or use the frontend's "Run All Cases" button.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with API key status |
| `/api/analyze` | POST | Analyze a pre-auth case (JSON input) |
| `/api/analyze/upload` | POST | Upload Excel and analyze |
| `/api/cases` | GET | List all training cases |
| `/api/cases/{case_id}` | GET | Get single case details |
| `/api/schema` | GET | Get 30-field patient data schema |
| `/api/schema/json` | GET | Get machine-readable JSON schema |
| `/api/complex-case/input` | GET | Get the complex case input |
| `/api/validate-all` | GET | Run all 10 cases and return accuracy |

**For developers:** All endpoints return JSON. The `/api/analyze` endpoint accepts a `PreAuthCaseInput` object and returns a `PreAuthSkillOutput` object.

---

## File Structure

```
preauth-copilot/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── skill/
│   │   ├── pipeline.py            # Orchestration
│   │   ├── normalizer.py          # Step 1
│   │   ├── evaluator.py           # Step 2
│   │   ├── assembler.py           # Step 3
│   │   ├── criteria_registry.py   # Service-type mapping
│   │   ├── parser_utils.py        # Shared parsing
│   │   ├── prompts.py             # Prompt templates
│   │   ├── schema.py              # Pydantic models
│   │   └── errors.py              # Custom exceptions
│   ├── data/
│   │   ├── training_cases.json
│   │   ├── patient_data_schema.json
│   │   ├── complex_case.json
│   │   └── expected_outcome.json
│   ├── scripts/
│   │   ├── parse_workbook.py
│   │   └── run_complex_case.py
│   └── tests/
│       ├── conftest.py
│       ├── test_complex_case.py
│       └── test_pipeline.py
├── docs/
│   ├── SKILL_DESIGN.md
│   ├── WORKFLOW.md
│   ├── ERROR_ANALYSIS.md
│   └── schema.json
├── outputs/
│   ├── complex_case_output.json
│   └── case_results/
│       └── PA-001.json … PA-010.json
├── frontend/
│   └── ... (Next.js app)
├── .gitignore
└── README.md
```

---

## Troubleshooting

### "MISTRAL_API_KEY is not set"

**Problem:** The pipeline fails with a RuntimeError about missing API key.

**Solution:** Set the environment variable before starting the backend:
```bash
export MISTRAL_API_KEY=your_key_here
python main.py
```

### "ModuleNotFoundError: No module named 'skill'"

**Problem:** Python can't find the skill module.

**Solution:** Run from the `backend/` directory, not the project root:
```bash
cd backend
python main.py
```

### "422 Unprocessable Entity" on /api/analyze

**Problem:** The input JSON doesn't match the expected schema.

**Solution:** Check that your input has all required fields:
- `requested_service` (required)
- `primary_diagnosis` (required)
- All other fields are optional

### Tests failing with "AssertionError"

**Problem:** A test case isn't producing the expected output.

**Solution:** 
1. Check the test file to see what's being validated
2. Run the case manually through the API
3. Compare the actual output with expected output
4. See [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md) for common failure patterns

---

## Adding New Service Types

1. Add criteria to `backend/skill/criteria_registry.py`
2. Add keyword mapping in `SERVICE_TYPE_MAP`
3. Test with a new training case
4. Update the frontend if needed

**For developers:** The criteria format is:
```python
{
    "criterion_id": "C1",
    "criterion_name": "Criterion Name",
    "description": "What this criterion requires"
}