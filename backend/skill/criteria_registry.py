"""
Service-type to criteria set mapping.

7 service-type criteria sets + default.
C1-C6 from the complex case apply to spine surgery only.
The registry makes the skill reusable across all 10 training case types.

Keyword matching uses an ordered list of tuples, not a dict, so first match wins.
"""

from typing import List, Dict, Tuple, TypedDict

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

class Criterion(TypedDict):
    """Type definition for a single criterion entry."""
    criterion_id: str
    criterion_name: str
    description: str

# ---------------------------------------------------------------------------
# Criteria definitions
# ---------------------------------------------------------------------------

SPINE_SURGERY_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Imaging correlates with symptoms",
        "description": "MRI/CT shows stenosis, herniation, or other pathology at the level matching the patient's neurological deficits or pain distribution.",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Objective neurologic deficit documented",
        "description": "Motor weakness, sensory loss, reflex changes, or gait disturbance documented on physical exam by a qualified provider.",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Failure of adequate conservative treatment",
        "description": "At least 6-12 weeks of appropriate conservative care (physical therapy, medications, injections) with documented lack of improvement or intolerance.",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Functional impairment documented",
        "description": "Objective impact on activities of daily living (ADLs), work, or mobility that is clearly described and linked to the condition.",
    },
    {
        "criterion_id": "C5",
        "criterion_name": "Inpatient site-of-care justification",
        "description": "Medical necessity for inpatient (vs. outpatient/ASC) based on comorbidities, risk factors, or post-op monitoring needs.",
    },
    {
        "criterion_id": "C6",
        "criterion_name": "No policy prerequisites missing",
        "description": "All required prerequisites (e.g., specific conservative treatments, diagnostic tests, specialist consultations) are documented as completed or not applicable.",
    },
]

DME_HOME_OXYGEN_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Chronic hypoxemia documented",
        "description": "PaO2 ≤55 mmHg or ≤57 mmHg with evidence of right-sided heart failure or polycythemia (Hct >55%).",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Daytime oxygen saturation",
        "description": "SpO2 ≤88% for ≥15 minutes during daytime while awake and breathing room air.",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Nocturnal desaturation",
        "description": "SpO2 ≤88% for ≥3 hours during sleep, or ≤89% for ≥4 hours during sleep.",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Alternative causes ruled out",
        "description": "Documented evaluation for and exclusion of other causes of hypoxemia (e.g., pneumonia, PE, heart failure exacerbation).",
    },
]

BIOLOGIC_THERAPY_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Confirmed diagnosis",
        "description": "Definitive diagnosis of the condition for which biologic therapy is being requested, with supporting lab/imaging evidence.",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Failed conventional therapy",
        "description": "Documented inadequate response or intolerance to standard conventional treatments (e.g., corticosteroids, immunomodulators).",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Severity criteria met",
        "description": "Evidence of moderate to severe disease activity (e.g., endoscopic assessment, biomarker levels, clinical scores).",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Prerequisite treatments completed",
        "description": "All required step therapy and prerequisite treatments have been tried and failed or are contraindicated.",
    },
]

POST_ACUTE_REHAB_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Medical stability",
        "description": "Acute medical issues are stabilized; patient is medically ready for intensive rehabilitation.",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Rehabilitation potential",
        "description": "Patient has reasonable potential to improve functional abilities with intensive rehabilitation (3+ hours/day).",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Need for multidisciplinary care",
        "description": "Requires coordinated care from multiple disciplines (PT, OT, speech, psychology) not available in less intensive settings.",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Site-of-care appropriateness",
        "description": "Inpatient rehabilitation is more appropriate than skilled nursing facility or home health based on needs and progress.",
    },
]

HIGH_COST_IMAGING_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Established diagnosis",
        "description": "Clinical question is specific and the diagnosis is already established; imaging is for staging, restaging, or monitoring.",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Expected impact on management",
        "description": "Results will directly change treatment decisions (e.g., modify therapy, detect recurrence, guide biopsy).",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Appropriate timing",
        "description": "Imaging is not too early (disease not detectable) or too late (clinical course already evident); follows appropriate intervals.",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Prior imaging reviewed",
        "description": "Previous imaging studies have been reviewed and comparison is provided or not needed.",
    },
]

BARIATRIC_SURGERY_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "BMI threshold",
        "description": "BMI ≥40, or ≥35 with at least one obesity-related comorbidity (e.g., diabetes, hypertension, sleep apnea).",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Failed non-surgical weight loss",
        "description": "Documented participation in supervised weight loss program with minimal or no sustained weight loss.",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Medical evaluation completed",
        "description": "Comprehensive medical, nutritional, and psychological evaluations completed per program requirements.",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Informed consent obtained",
        "description": "Patient understands risks, benefits, and lifestyle changes required after surgery.",
    },
]

CARDIOVASCULAR_PROCEDURE_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Severe valve disease",
        "description": "Evidence of severe stenosis or regurgitation on echocardiogram with hemodynamic consequences.",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Symptoms consistent with severity",
        "description": "Symptoms (angina, dyspnea, syncope) correlate with the degree of valve dysfunction.",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "High or prohibitive surgical risk",
        "description": "STS score or clinical factors indicate high or prohibitive risk for open surgical repair.",
    },
    {
        "criterion_id": "C4",
        "criterion_name": "Anatomical suitability",
        "description": "Vascular anatomy is suitable for transcatheter approach (e.g., access vessels, landing zones).",
    },
]

# Default criteria for unrecognized service types
DEFAULT_CRITERIA: List[Criterion] = [
    {
        "criterion_id": "C1",
        "criterion_name": "Clinical indication established",
        "description": "The requested service is medically necessary for the stated condition.",
    },
    {
        "criterion_id": "C2",
        "criterion_name": "Appropriate prior treatment",
        "description": "Conservative or standard treatments have been tried or are contraindicated.",
    },
    {
        "criterion_id": "C3",
        "criterion_name": "Documentation complete",
        "description": "All required clinical information and supporting documentation are provided.",
    },
]

# ---------------------------------------------------------------------------
# Service type mapping — ordered list of tuples for first-match-wins
# ---------------------------------------------------------------------------

SERVICE_TYPE_MAP: List[Tuple[str, str]] = [
    ("cervical",         "spine_surgery"),
    ("lumbar",           "spine_surgery"),
    ("fusion",           "spine_surgery"),
    ("decompression",    "spine_surgery"),
    ("home oxygen",      "dme_home_oxygen"),
    ("nocturnal",        "dme_home_oxygen"),
    ("biologic",         "biologic_therapy"),
    ("ivig",             "biologic_therapy"),
    ("rehabilitation",   "post_acute_rehab"),
    ("pet/ct",           "high_cost_imaging"),
    ("pet scan",         "high_cost_imaging"),
    ("bariatric",        "bariatric_surgery"),
    ("tavr",             "cardiovascular_procedure"),
    ("valve",            "cardiovascular_procedure"),
]

# ---------------------------------------------------------------------------
# Registry lookup function
# ---------------------------------------------------------------------------

_CRITERIA_REGISTRY: Dict[str, List[Criterion]] = {
    "spine_surgery": SPINE_SURGERY_CRITERIA,
    "dme_home_oxygen": DME_HOME_OXYGEN_CRITERIA,
    "biologic_therapy": BIOLOGIC_THERAPY_CRITERIA,
    "post_acute_rehab": POST_ACUTE_REHAB_CRITERIA,
    "high_cost_imaging": HIGH_COST_IMAGING_CRITERIA,
    "bariatric_surgery": BARIATRIC_SURGERY_CRITERIA,
    "cardiovascular_procedure": CARDIOVASCULAR_PROCEDURE_CRITERIA,
    "default": DEFAULT_CRITERIA,
}


def get_criteria(requested_service: str) -> List[Criterion]:
    """
    Return the appropriate criteria set for the requested service.

    Uses first-match-wins keyword matching on the service name.
    Returns default criteria if no match is found.
    """
    if not requested_service:
        return _CRITERIA_REGISTRY["default"]

    service_lower = requested_service.lower()
    for keyword, service_type in SERVICE_TYPE_MAP:
        if keyword in service_lower:
            return _CRITERIA_REGISTRY.get(service_type, _CRITERIA_REGISTRY["default"])

    return _CRITERIA_REGISTRY["default"]


def format_criteria_for_prompt(criteria: List[Criterion]) -> str:
    """
    Format criteria list as a readable block for str.replace() injection into prompt.
    
    Escapes potential JSON-like delimiters in descriptions to prevent confusion
    if criteria are ever user-configurable. Current descriptions are safe, but
    this provides defense-in-depth.
    """
    lines: List[str] = []
    for c in criteria:
        # Escape potential JSON-like delimiters in the description
        description = c.get('description', '')
        # Replace curly braces that could be confused with JSON placeholders
        description = description.replace('{', '{{').replace('}', '}}')
        lines.append(f"{c['criterion_id']}: {c['criterion_name']}")
        lines.append(f"    Description: {description}")
        lines.append("")
    return "\n".join(lines)
