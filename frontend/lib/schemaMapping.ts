/**
 * Schema field mapping for the manual entry form.
 * Maps frontend form field keys to backend schema field IDs.
 * This provides a stable, explicit mapping instead of fuzzy string matching.
 */

// Map of form field keys to schema field IDs (from patient_data_schema.json)
// Note: Each form field should map to a unique schema ID. If multiple fields
// legitimately map to the same schema field, use getSchemaFieldById with
// the specific field name to retrieve the correct tooltip.
export const FORM_FIELD_TO_SCHEMA_ID: Record<string, number> = {
  // Coverage
  payer_plan: 3,
  requested_service: 4,
  site_of_care: 5,
  requested_los: 6,
  payer_policy_version: 27,
  payer_policy_excerpt: 27, // Shares ID 27 with payer_policy_version

  // Demographics
  age: 1,
  sex: 2,

  // Diagnosis
  primary_diagnosis: 7,
  secondary_diagnoses: 8,

  // Clinical Severity
  symptom_duration: 9,
  pain_severity: 10,
  adl_value: 11,
  adl_source: 11, // Shares ID 11 with adl_value
  neuro_value: 12,
  neuro_source: 12, // Shares ID 12 with neuro_value
  vital_signs: 13,
  mental_status: 14,

  // History
  prior_conservative_treatment: 15,
  response_to_prior_treatment: 16,
  prior_surgeries_procedures: 17,

  // Medication
  current_medications: 18,
  medication_contraindications: 19,

  // Diagnostics
  imaging_value: 20,
  imaging_source: 20, // Shares ID 20 with imaging_value
  lab_results: 21,
  pathology_biopsy: 22,
  specialized_tests: 23,

  // Utilization
  prior_hospitalizations_ed: 24,
  complications_red_flags: 25,

  // Administrative
  ordering_provider_specialty: 26,
  required_prerequisites: 28,
  missing_records: 29,
  contradictory_flags: 30, // Shares ID 30 with known_exclusions_present
  known_exclusions_present: 30,
  utilization_review_note: 28, // Shares ID 28 with required_prerequisites
}

/**
 * Schema field information for tooltip display.
 * Used to resolve the correct tooltip when multiple form fields share the same schema ID.
 */
const FIELD_TOOLTIP_OVERRIDES: Record<string, { id: number; aspect: string; why_it_matters: string }> = {
  payer_policy_excerpt: {
    id: 27,
    aspect: 'Payer Policy Excerpt',
    why_it_matters: 'Document the specific policy language that supports or denies the request.',
  },
  adl_source: {
    id: 11,
    aspect: 'ADL Source',
    why_it_matters: 'Identify where the ADL impairment documentation originates (e.g., surgeon note, PT eval).',
  },
  neuro_source: {
    id: 12,
    aspect: 'Neurologic Deficits Source',
    why_it_matters: 'Document the source of neurologic assessment findings.',
  },
  imaging_source: {
    id: 20,
    aspect: 'Imaging Source',
    why_it_matters: 'Identify the imaging study and date to verify current findings.',
  },
  contradictory_flags: {
    id: 30,
    aspect: 'Contradictory Flags',
    why_it_matters: 'Note any conflicting information in the packet that needs resolution.',
  },
  utilization_review_note: {
    id: 28,
    aspect: 'Utilization Review Note',
    why_it_matters: 'Document any prior UR determinations or recommendations.',
  },
}

/**
 * Get the schema field for a form field key.
 * Uses explicit ID mapping with tooltip overrides for fields that share schema IDs.
 */
export function getSchemaFieldById(
  schema: Array<{ id: number; aspect: string; why_it_matters: string }>,
  formKey: string
): { id: number; aspect: string; why_it_matters: string } | undefined {
  // Check for field-specific tooltip override first
  const override = FIELD_TOOLTIP_OVERRIDES[formKey]
  if (override) {
    return override
  }

  const schemaId = FORM_FIELD_TO_SCHEMA_ID[formKey]
  if (schemaId === undefined) return undefined
  return schema.find(f => f.id === schemaId)
}

/**
 * Get tooltip text for a form field using explicit ID mapping.
 * Falls back to fuzzy matching if no explicit mapping exists.
 */
export function getTooltipForField(
  schema: Array<{ id: number; aspect: string; why_it_matters: string }>,
  formKey: string
): string {
  // Try explicit mapping first
  const explicit = getSchemaFieldById(schema, formKey)
  if (explicit) return explicit.why_it_matters

  // Fall back to fuzzy matching for unmapped fields
  const match = schema.find(
    f => f.aspect.toLowerCase().includes(formKey.toLowerCase())
  )
  return match?.why_it_matters || ''
}