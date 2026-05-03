// ============================================================
// All TypeScript interfaces mirroring backend Pydantic models.
// Written before any component — every other file imports from here.
// ============================================================

// ── Sub-model ─────────────────────────────────────────────
// Mirrors skill/schema.py SourcedField
// Used for functional_impairment_adls, objective_neurologic_deficits, imaging_findings
export interface SourcedField {
  value?: string | null
  source?: string | null
  source_date?: string | null
}

// ── Enums ─────────────────────────────────────────────────
export type Recommendation = 'LIKELY_APPROVE' | 'NEED_MORE_INFO' | 'LIKELY_DENY'
export type Confidence = 'HIGH' | 'MEDIUM' | 'LOW'
export type CriterionStatus = 'MET' | 'PARTIAL' | 'UNMET' | 'N/A'

// ── Input model ────────────────────────────────────────────
// Mirrors PreAuthCaseInput (35 fields: 30 workbook + 5 additional)
// medication_contraindications covers allergies per workbook field 19
export interface PreAuthCaseInput {
  case_id?: string

  // Coverage
  payer_plan?: string
  requested_service: string            // REQUIRED
  site_of_care?: string
  requested_los?: string
  payer_policy_version?: string
  payer_policy_excerpt?: string

  // Demographics
  age?: number
  sex?: string

  // Diagnosis
  primary_diagnosis: string            // REQUIRED
  secondary_diagnoses?: string[]

  // Clinical Severity
  symptom_duration?: string
  pain_severity?: string
  functional_impairment_adls?: SourcedField     // SourcedField — PA-001 C4
  objective_neurologic_deficits?: SourcedField  // SourcedField — PA-001 C2 contradiction
  vital_signs?: string
  mental_status?: string

  // History
  prior_conservative_treatment?: string[]
  response_to_prior_treatment?: string
  prior_surgeries_procedures?: string

  // Medication (field 19 covers allergies + intolerances)
  current_medications?: string[]
  medication_contraindications?: string

  // Diagnostics
  imaging_findings?: SourcedField      // SourcedField — single authoritative source
  lab_results?: string
  pathology_biopsy?: string
  specialized_tests?: string

  // Utilization
  prior_hospitalizations_ed?: string
  complications_red_flags?: string

  // Administrative
  ordering_provider_specialty?: string
  required_prerequisites?: string
  missing_records?: string
  contradictory_flags?: string
  known_exclusions_present?: string

  // Additional (Problem Statement input packet list)
  utilization_review_note?: string
  raw_clinical_notes?: string
}

// ── Output sub-models ─────────────────────────────────────
export interface CriterionResult {
  criterion_id: string
  criterion_name: string
  status: CriterionStatus
  supporting_evidence: string | null
  gap_or_risk: string | null
}

export interface EvidenceSnippet {
  source: string
  excerpt: string
}

// ── Output model ───────────────────────────────────────────
// Mirrors PreAuthSkillOutput (11 Suggested_Output fields + flip_condition + criteria_results + metadata)
export interface PreAuthSkillOutput {
  case_id: string
  requested_service: string
  recommendation: Recommendation
  confidence: Confidence
  clinical_summary: string
  criteria_results: CriterionResult[]
  criteria_met: string[]
  criteria_partial_or_unmet: string[]
  supporting_evidence: EvidenceSnippet[]
  missing_information: string[]
  provider_query: string
  appeal_direction: string | null      // null for NEED_MORE_INFO and LIKELY_APPROVE
  flip_condition: string | null        // null for LIKELY_APPROVE

  // Pipeline metadata
  processing_time_ms: number
  step1_time_ms: number
  step2_time_ms: number
  model_used: string
}

// ── Training case (from GET /api/cases) ───────────────────
export interface TrainingCase {
  case_id: string
  requested_service: string
  clinical_scenario: string
  key_supporting_evidence: string
  key_gaps_or_risks: string
  expected_outcome: Recommendation
  why: string
  if_additional_documentation_arrives: string | null
  complexity_notes: string
  has_full_packet?: boolean            // true for PA-001 only
}

// ── Schema field (from GET /api/schema) ───────────────────
export interface SchemaField {
  id: number
  category: string
  aspect: string
  description: string
  typical_type: string
  example_value: string
  why_it_matters: string
}

// ── Validation (from GET /api/validate-all) ───────────────
export interface ValidationCaseResult {
  case_id: string
  requested_service?: string
  expected: Recommendation
  actual: Recommendation | 'ERROR'
  match: boolean
  confidence?: Confidence
  complexity_notes?: string
  note?: string | null
  error?: string
}

export interface ValidationSummary {
  total: number
  correct: number
  accuracy: number
  results: ValidationCaseResult[]
}

// ── Progress Event (from GET /api/validate-all/stream) ───────
export interface ValidationProgressEvent {
  type: 'progress' | 'complete'
  current: number
  total: number
  case_id?: string | null
  result?: ValidationCaseResult | ValidationSummary | null
}

// ── API Error ─────────────────────────────────────────────
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public rawResponse?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}