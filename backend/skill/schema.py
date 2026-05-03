"""
All Pydantic models for the pre-auth skill.

Field count note:
    Input model has 30 workbook fields + 5 additional fields = 35 total.
    The 30 workbook fields match Patient_Data_Aspects exactly (IDs 1-30).
    Field 19 (medication_contraindications) already covers allergies per its
    workbook description: "Allergy, side effect, inability to use standard therapy."
    No separate 'allergies' field is added.
    The normalization prompt instructs extraction of drug/substance allergies
    into medication_contraindications formatted as "Allergies: [X]; Intolerances: [Y]".

SourcedField usage:
    Used on 3 fields where source attribution directly determines criterion status:
    - functional_impairment_adls:      ADL data in PT note, absent from surgeon consult (PA-001 C4)
    - objective_neurologic_deficits:   PCP note contradicts specialist (PA-001 C2)
    - imaging_findings:                Single authoritative source requiring explicit citation (PA-001 C1)

appeal_direction:
    Optional[str] = None
    Populated ONLY for LIKELY_DENY.
    Assembler enforces null for NEED_MORE_INFO and LIKELY_APPROVE.
    Showing appeal direction before a denial would mislead the reviewer.

flip_condition:
    Optional[str] = None
    Answers Part 3 requirement: "additional documentation that could improve the outcome"
    Sourced from 'if_additional_documentation_arrives' (training cases)
    and 'what would likely flip to approve?' (complex case outcome).
"""

import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated

from .constants import (
    MAX_PRIMARY_DIAGNOSIS_LENGTH,
    MAX_RAW_CLINICAL_NOTES_LENGTH,
    MAX_REQUESTED_SERVICE_LENGTH,
)


def _sanitize_text(text: Optional[str]) -> Optional[str]:
    """
    Sanitize text input to prevent prompt injection attacks.
    
    Removes or escapes potentially dangerous patterns that could be used
    to manipulate LLM behavior. This is a defense-in-depth measure; the
    LLM system prompt also instructs the model to extract facts only.
    """
    if text is None:
        return None
    
    # Remove null bytes and other control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Limit consecutive special characters that could be used for injection
    text = re.sub(r'[`*_]{20,}', lambda m: m.group(0)[:10], text)
    
    # Remove common prompt injection patterns
    injection_patterns = [
        r'ignore\s+previous\s+instructions',
        r'disregard\s+the\s+above',
        r'new\s+instructions:',
        r'<\s*ignore\s*>',
        r'<\s*system\s*>',
        r'<\s*assistant\s*>',
    ]
    for pattern in injection_patterns:
        text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
    
    return text


# ---------------------------------------------------------------------------
# SourcedField — tracks which document a fact came from
# ---------------------------------------------------------------------------

class SourcedField(BaseModel):
    value: Optional[str] = None
    source: Optional[str] = None        # e.g. "PT note (discharge)", "Neurology consult"
    source_date: Optional[str] = None   # e.g. "3 months prior", "recent"


# ---------------------------------------------------------------------------
# Input model — 35 fields total
# ---------------------------------------------------------------------------

class PreAuthCaseInput(BaseModel):

    # --- Identity (1 field) ---
    case_id: Optional[str] = None

    # --- Coverage — workbook fields 3-6 + 2 additional (6 total) ---
    payer_plan: Optional[str] = None
    requested_service: Annotated[
        str,
        Field(
            min_length=1,
            max_length=MAX_REQUESTED_SERVICE_LENGTH,
        ),
    ]  # REQUIRED - drives criteria selection
    site_of_care: Optional[str] = None               # Inpatient/ASC/Outpatient/Home/IRF/SNF
    requested_los: Optional[str] = None
    payer_policy_version: Optional[str] = None
    payer_policy_excerpt: Optional[str] = None       # Policy text if supplied with the case

    # --- Demographics — workbook fields 1-2 (2 total) ---
    age: Optional[int] = None
    sex: Optional[str] = None

    # --- Diagnosis — workbook fields 7-8 (2 total) ---
    primary_diagnosis: Annotated[
        str,
        Field(
            min_length=1,
            max_length=MAX_PRIMARY_DIAGNOSIS_LENGTH,
        ),
    ]  # REQUIRED
    secondary_diagnoses: Optional[List[str]] = None

    # --- Clinical Severity — workbook fields 9-14 (6 total) ---
    symptom_duration: Optional[str] = None
    pain_severity: Optional[str] = None
    functional_impairment_adls: Optional[SourcedField] = None    # Sourced: PA-001 C4
    objective_neurologic_deficits: Optional[SourcedField] = None # Sourced: PA-001 C2 contradiction
    vital_signs: Optional[str] = None
    mental_status: Optional[str] = None

    # --- History — workbook fields 15-17 (3 total) ---
    prior_conservative_treatment: Optional[List[str]] = None
    response_to_prior_treatment: Optional[str] = None
    prior_surgeries_procedures: Optional[str] = None

    # --- Medication — workbook fields 18-19 (2 total) ---
    current_medications: Optional[List[str]] = None
    medication_contraindications: Optional[str] = None
    # ^ Covers drug/substance allergies AND side effects AND intolerances.
    #   The normalization prompt formats as: "Allergies: [X]; Intolerances: [Y]"
    #   No separate 'allergies' field — workbook field 19 already covers this.

    # --- Diagnostics — workbook fields 20-23 (4 total) ---
    imaging_findings: Optional[SourcedField] = None  # Sourced: single authoritative anchor
    lab_results: Optional[str] = None
    pathology_biopsy: Optional[str] = None
    specialized_tests: Optional[str] = None           # EMG, PFT, oximetry, polysomnography

    # --- Utilization — workbook fields 24-25 (2 total) ---
    prior_hospitalizations_ed: Optional[str] = None
    complications_red_flags: Optional[str] = None

    # --- Administrative — workbook fields 26-30 (5 total) ---
    ordering_provider_specialty: Optional[str] = None
    required_prerequisites: Optional[str] = None
    missing_records: Optional[str] = None
    contradictory_flags: Optional[str] = None
    known_exclusions_present: Optional[str] = None   # e.g. "BMI elevated; not excluded by policy"

    # --- Additional fields from Problem Statement input packet list (2 total) ---
    utilization_review_note: Optional[str] = None    # Prior UR assessment / denial reasons
    raw_clinical_notes: Annotated[
        Optional[str],
        Field(max_length=MAX_RAW_CLINICAL_NOTES_LENGTH),
    ] = None         # Unstructured fallback; normalizer extracts from it

    @field_validator('raw_clinical_notes', mode='before')
    @classmethod
    def sanitize_raw_clinical_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize raw_clinical_notes to prevent prompt injection attacks."""
        return _sanitize_text(v)


# ---------------------------------------------------------------------------
# Output sub-models
# ---------------------------------------------------------------------------

class CriterionResult(BaseModel):
    criterion_id: str                                # "C1" through "C6" (or more for other service types)
    criterion_name: str
    status: Literal["MET", "PARTIAL", "UNMET", "N/A"]
    supporting_evidence: Optional[str] = None        # Source-anchored fact(s)
    gap_or_risk: Optional[str] = None               # What is missing or contradictory


class EvidenceSnippet(BaseModel):
    source: str    # document type + author role + approximate date
    excerpt: str   # the specific fact extracted


# ---------------------------------------------------------------------------
# Output model — 11 Suggested_Output fields + flip_condition + criteria_results + metadata
# ---------------------------------------------------------------------------

class PreAuthSkillOutput(BaseModel):
    # Core 11 fields — match Suggested_Output sheet exactly
    case_id: str
    requested_service: str
    recommendation: Literal["LIKELY_APPROVE", "NEED_MORE_INFO", "LIKELY_DENY"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    clinical_summary: str
    criteria_results: List[CriterionResult]
    criteria_met: List[str]
    criteria_partial_or_unmet: List[str]
    supporting_evidence: List[EvidenceSnippet]
    missing_information: List[str]
    provider_query: str
    appeal_direction: Optional[str] = None   # ONLY for LIKELY_DENY; assembler enforces null otherwise
    flip_condition: Optional[str] = None     # Answers "what doc would improve outcome"

    # Pipeline metadata
    processing_time_ms: int
    step1_time_ms: int
    step2_time_ms: int
    model_used: str