# Pre-Authorization Medical Necessity Copilot

This is an AI-powered system that reviews medical pre-authorization requests and provides clear, auditable recommendations. It helps healthcare teams quickly determine whether a requested service meets medical necessity criteria.

---

## What This System Does

The Pre-Authorization Copilot converts messy clinical pre-authorization packets into structured medical-necessity recommendations. You provide a clinical case packet — structured fields, free text, or an uploaded Excel workbook and the system returns:

- A recommendation label: `LIKELY_APPROVE`, `NEED_MORE_INFO`, or `LIKELY_DENY`
- Evidence citations with source attribution
- Documentation gaps that need to be filled
- Provider action items for follow-up

---

## Architecture

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14 |
| LLM | Mistral API (`mistral-devstral-2512`) (We can integrate other APIs also) | 
| Backend | Python + FastAPI |

### Three-Step Pipeline
Instead of defining a single prompt skill defining, this pipeline contains 3-steps. One for normalization of data, and then criteria evalution, finally it assembles the output generated from the LLM response

1. **Normalization** - Extract 30 fields from raw input (Mistral call #1)
2. **Criteria Evaluation** - Apply service-specific criteria with 14 reasoning rules (Mistral call #2)
3. **Assembly** - Build validated output with constraints (Python only)

**Why this design?** Each step has a single responsibility, making the system debuggable and reliable.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Mistral API key

### Setup

```bash
# Clone and enter directory
cd preauth-copilot

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env file
echo "MISTRAL_API_KEY=your_key_here" > .env
```

### Parse Workbook

```bash
cd backend
python scripts/parse_workbook.py
```

This generates JSON data files in `backend/data/`.

### Run Complex Case

```bash
cd backend
python scripts/run_complex_case.py
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

### Start API Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with API key status |
| `/api/analyze` | POST | Analyze a pre-auth case (JSON input) |
| `/api/analyze/upload` | POST | Upload Excel and analyze |
| `/api/cases` | GET | List all 10 training cases |
| `/api/cases/{case_id}` | GET | Get single case details |
| `/api/schema` | GET | Get 30-field patient data schema |
| `/api/schema/json` | GET | Get machine-readable JSON schema |
| `/api/complex-case/input` | GET | Get full complex case (PA-001) input |
| `/api/validate-all` | GET | Run all 10 cases and return accuracy |

---

## Output Labels

| Label | Meaning |
|-------|---------|
| `LIKELY_APPROVE` | Clinical necessity established and documented |
| `NEED_MORE_INFO` | Clinical necessity plausible, documentation incomplete |
| `LIKELY_DENY` | Case does not meet medical necessity under policy |

**Key insight:** PARTIAL criteria → always `NEED_MORE_INFO`, never `LIKELY_DENY`. Only true clinical absence of necessity triggers denial.

---

## Service Types Supported

The system supports 7 service types, each with its own criteria:

| Service Type | Example Services |
|--------------|------------------|
| Spine Surgery | Cervical fusion, Lumbar decompression |
| DME Home Oxygen | Home oxygen, Nocturnal oxygen |
| Biologic Therapy | Infliximab, IVIG |
| Post-Acute Rehab | Inpatient rehabilitation |
| High-Cost Imaging | PET/CT, PET scan |
| Bariatric Surgery | Gastric bypass, Sleeve gastrectomy |
| Cardiovascular Procedure | TAVR, Valve replacement |

---

## Project Structure

```
preauth-copilot/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── skill/                     # Core skill logic (3-step pipeline)
│   │   ├── pipeline.py            # Orchestration
│   │   ├── normalizer.py          # Step 1
│   │   ├── evaluator.py           # Step 2
│   │   ├── assembler.py           # Step 3
│   │   ├── criteria_registry.py   # Service-type mapping
│   │   ├── schema.py              # Pydantic models
│   │   └── prompts.py             # LLM prompt templates
│   ├── data/                      # JSON data files
│   ├── scripts/                   # CLI scripts
│   └── tests/                     # Test files
├── docs/                          # Documentation
│   ├── SKILL_DESIGN.md            # Skill design document
│   ├── WORKFLOW.md                # Development workflow
│   └── schema.json                # Machine-readable JSON schema
├── outputs/                       # Generated outputs
│   ├── complex_case_output.json
│   └── case_results/              # PA-001.json … PA-010.json
└── frontend/                      # Next.js app
```

---

## Documentation

- [SKILL_DESIGN.md](docs/SKILL_DESIGN.md) - Skill design document with architecture and key decisions
- [WORKFLOW.md](docs/WORKFLOW.md) - Development workflow and troubleshooting guide
- [schema.json](docs/schema.json) - Machine-readable JSON schema

---

## Approach

The system uses a **3-step pipeline** to transform messy clinical data into structured recommendations:

1. **Normalization (LLM Call #1)**: Extracts 30 standardized fields from raw input (structured fields, free text, or Excel uploads). This step handles missing data, resolves contradictions, and creates a clean data structure.

2. **Criteria Evaluation (LLM Call #2)**: Applies service-specific medical necessity criteria with 14 reasoning rules. The LLM evaluates each criterion (C1-C6 for spine surgery, C1-C4 for other services) and determines if it's MET, PARTIAL, or UNMET.

3. **Assembly (Python-only)**: Validates the LLM output against Pydantic schemas, builds the final response with evidence citations, and generates provider queries.

**Why this approach?** Single prompts fail when extraction errors silently corrupt reasoning. The pipeline isolates each concern, making debugging possible and ensuring reliability.

---

## Prompt/Skill Design

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline vs Single Prompt | 3-step pipeline | Extraction errors in single prompts silently corrupt reasoning; steps can be debugged independently |
| Few-shot Examples | 3 examples per step | PARTIAL vs UNMET distinction is subtle; examples teach it without fine-tuning |
| Temperature | 0.0 | Medical reasoning must be deterministic; variance is a defect |
| max_tokens | 3000 | Complex cases can reach ~2500 tokens; 2000 risks mid-JSON truncation |
| Criteria Injection | `str.replace()` | `.format()` breaks if criteria text contains curly braces |

### Prompt Structure

**Step 1 (Normalization)**:
- System prompt defines the 30-field extraction task
- Few-shot examples show how to handle missing/ambiguous data
- Output: JSON with normalized field values

**Step 2 (Evaluation)**:
- System prompt defines the 14 reasoning rules
- Criteria are injected as context
- Few-shot examples show MET/PARTIAL/UNMET distinctions
- Output: JSON with criterion verdicts and evidence

---

## Assumptions

1. **Data Quality**: Input contains sufficient clinical information to evaluate medical necessity.

2. **Service Type Detection**: The requested service field contains enough information to map to one of 7 supported service types.

3. **Policy Criteria**: Each service type has predefined criteria in the criteria registry. New services require manual criteria definition.

4. **LLM Reliability**: The Mistral model produces valid JSON and follows instructions. Temperature=0.0 minimizes variance.

5. **Source Hierarchy**: Recent specialist notes override older PCP notes when contradictions exist.

6. **PARTIAL ≠ DENY**: Partial documentation indicates need for more info, not clinical inadequacy.

---

## Limitations

1. **Service Types**: Only 7 service types supported. Adding new types requires:
   - Defining criteria in `criteria_registry.py`
   - Creating few-shot examples
   - Testing with real cases

2. **LLM Dependency**: Requires Mistral API key. No offline mode.

3. **No Learning**: System doesn't improve from feedback. Each case is evaluated independently.

4. **English Only**: Prompts and output are English-only.

5. **File Size Limits**: 10MB max for Excel uploads; 1MB max for JSON requests.

6. **No Authentication**: API uses simple key-based auth; not suitable for production without enhancement.

---

## Possible Improvements

### Medical/Clinical Improvements

1. **Evidence-Based Criteria Enhancement**:
   - Integrating the pipeline with some medical databases, citations or something for better results

2. **Clinical Guidelines Integration**:
   - Incorporating NCCN, ACC/AHA, AAOS, and other specialty society guidelines
   - guideline version tracking and update notifications can be implemented
   - Map criteria to specific guideline sections for auditability

3. **Outcome Prediction**:
   - Add success probability scoring based on similar cases
   - Integrate patient-reported outcome measures

4. **Specialty-Specific Enhancements**:
   The cases mentioned should be defined in more details for better results.

7. **Clinical Decision Support**:
   _ Although the system makes the outcome faster, yet expert terms should be kept in the loop for better handling.

### Technical Improvements

1. **Additional Service Types**:
   - Add criteria for interventional pain management
   - Add criteria for durable medical equipment (DME) beyond oxygen
   - Add criteria for genetic testing

2. **Enhanced LLM Integration**:
   - Better models can provide better results

3. **Learning from Feedback**:
   - Store provider responses to queries
   - Track which missing information items were actually provided
   - Use feedback to improve future recommendations

4. **Production Hardening**:
   - Add OAuth2/JWT authentication
   - Implement rate limiting
   - Add request/response logging for audit trails
   - Add database for case persistence

5. **UI Enhancements**:
   - Add side-by-side comparison of cases
   - Add export to PDF/Markdown
   - Add batch processing for multiple cases

6. **Testing Improvements**:
   - Add integration tests with mock LLM responses
   - Add performance benchmarks
   - Add edge case tests for malformed input

---