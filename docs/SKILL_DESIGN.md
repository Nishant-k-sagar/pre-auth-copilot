# Pre-Authorization Copilot — Skill Design Document

## What This System Does

The Pre-Authorization Copilot is an AI-powered system that reviews medical pre-authorization requests and provides clear, auditable recommendations. It helps healthcare teams quickly determine whether a requested service meets medical necessity criteria.

**For the reader:** This document explains how the system works, why it's built this way, and what you need to know to use or extend it.

---

## How It Works: The 3-Step Pipeline

```
User uploads or selects case
          │
          ▼
FastAPI Backend
          │
          ├── STEP 1: NORMALIZATION (Mistral call #1)
          │     Input:  raw PreAuthCaseInput (structured fields + free text)
          │     Output: clean 30-field normalized dict
          │
          ├── STEP 2: CRITERIA EVALUATION (Mistral call #2)
          │     Input:  normalized dict + service-specific criteria
          │     Output: C1–CN verdicts + recommendation JSON
          │
          └── STEP 3: ASSEMBLY (Python only — no LLM)
                Input:  raw evaluation JSON
                Output: validated PreAuthSkillOutput
          │
          ▼
Next.js Frontend renders result
```

**Why this design?** Each step has a single responsibility, making the system debuggable and reliable. If something goes wrong, you can check each step independently.

---

## Key Design Decisions

| Decision | Choice | Why This Matters |
|----------|--------|------------------|
| Single prompt vs pipeline | 3-step pipeline | Extraction errors silently corrupt reasoning in a single prompt; steps can be debugged independently |
| Few-shot vs zero-shot | 3 few-shot examples | PARTIAL vs UNMET distinction is subtle; examples teach it without fine-tuning |
| Criteria set | Service-type-aware registry | C1–C6 from complex case apply to spine surgery only; other services need different criteria |
| Temperature | 0.0 | Medical reasoning must be deterministic; variance is a defect |
| max_tokens | 3000 | Complex cases can reach ~2500 tokens output; 2000 risks mid-JSON truncation |
| appeal_direction | Only for LIKELY_DENY | Showing appeal direction for NEED_MORE_INFO implies the case is already denied, which is wrong |
| Mistral client init | Lazy singleton | Module-level init with empty key causes silent auth failures; lazy init gives clear error |
| Criteria injection | str.replace() not .format() | .format() breaks if criteria text contains curly braces |
| AssemblyError | Custom exception, not HTTPException | Skill layer must not know about the web framework |
| Script imports | skill/parser_utils.py | scripts/ without __init__.py causes ModuleNotFoundError on upload route |
| Field count | 30 fields from workbook | allergies is absorbed by workbook field 19; no separate field needed |

---

## Understanding the Labels

| Label | What It Means | When You'll See It |
|-------|---------------|-------------------|
| `LIKELY_APPROVE` | Clinical necessity established and documented | All core criteria MET, no UNMET, packet complete |
| `NEED_MORE_INFO` | Clinical necessity plausible, documentation incomplete | Any criterion PARTIAL; clinical need real but packet has gaps |
| `LIKELY_DENY` | Case does not meet medical necessity under policy | Any core criterion genuinely UNMET (not merely underdocumented) |

**Key insight:** PARTIAL criteria → always `NEED_MORE_INFO`, never `LIKELY_DENY`. Only true clinical absence of necessity triggers denial.

---

## Input Schema

The input schema contains 35 fields:
- 30 fields from the workbook Patient_Data_Aspects sheet
- 5 additional fields: case_id, payer_policy_excerpt, utilization_review_note, known_exclusions_present, raw_clinical_notes

**For developers:** See [`backend/skill/schema.py`](backend/skill/schema.py) for the complete Pydantic model.

---

## Output Schema

The output schema contains:

| Field | Type | Description |
|-------|------|-------------|
| recommendation | enum | LIKELY_APPROVE, NEED_MORE_INFO, or LIKELY_DENY |
| confidence | enum | HIGH, MEDIUM, or LOW |
| criteria_met | string[] | List of criterion IDs that are fully met |
| criteria_partial_or_unmet | string[] | List of criterion IDs that are partial or unmet |
| criteria_results | array | Detailed per-criterion results with status and evidence |
| supporting_evidence | array | Evidence snippets with source attribution |
| missing_information | string[] | Documentation gaps that need to be filled |
| provider_query | string | Numbered questions for the provider |
| appeal_direction | string or null | Only populated for LIKELY_DENY cases |
| flip_condition | string or null | What additional documentation would improve outcome |
| processing_time_ms | int | Total pipeline time |
| step1_time_ms | int | Normalization step time |
| step2_time_ms | int | Evaluation step time |
| model_used | string | The Mistral model used |

**For developers:** See [`backend/skill/schema.py`](backend/skill/schema.py) for the complete Pydantic model.

---

## Error Handling

| Error Type | When It Occurs | How It's Handled |
|------------|----------------|------------------|
| `AssemblyError` | Validation failures in Step 3 | Caught in main.py, converted to HTTP 422 with debug info |
| `PipelineStepError` | Failures in Step 1 or 2 | Caught in main.py, converted to HTTP 422 with step info |
| `RuntimeError` | Missing MISTRAL_API_KEY | Raised immediately with clear message |

---

## Service Types and Criteria

The system supports 7 service types, each with its own criteria:

| Service Type | Criteria Count | Example Services |
|--------------|----------------|------------------|
| Spine Surgery | 6 | Cervical fusion, Lumbar decompression |
| DME Home Oxygen | 4 | Home oxygen, Nocturnal oxygen |
| Biologic Therapy | 4 | Infliximab, IVIG |
| Post-Acute Rehab | 4 | Inpatient rehabilitation |
| High-Cost Imaging | 4 | PET/CT, PET scan |
| Bariatric Surgery | 4 | Gastric bypass, Sleeve gastrectomy |
| Cardiovascular Procedure | 4 | TAVR, Valve replacement |

**For developers:** See [`backend/skill/criteria_registry.py`](backend/skill/criteria_registry.py) to add new service types.

---

## Security Considerations

- **Prompt injection protection:** All text inputs are sanitized to prevent manipulation of LLM behavior
- **API key protection:** MISTRAL_API_KEY is loaded via dotenv, never logged or exposed
- **Request size limits:** Maximum 1MB request body to prevent resource exhaustion
- **File upload limits:** Maximum 10MB for Excel uploads

---

## Getting Started

1. **Run the pipeline:** See [WORKFLOW.md](WORKFLOW.md) for step-by-step instructions
2. **Understand errors:** See [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md) for common failure patterns
3. **Add new service types:** Modify [`backend/skill/criteria_registry.py`](backend/skill/criteria_registry.py)