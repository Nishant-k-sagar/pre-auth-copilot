'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import type { PreAuthCaseInput, SchemaField } from '@/lib/types'
import { fetchInputSchema } from '@/lib/api'
import { useAnalyze } from '@/hooks/useAnalyze'
import { FormSection } from '@/components/form/FormSection'
import { FieldTooltip } from '@/components/form/FieldTooltip'
import { RawNotesInput } from '@/components/form/RawNotesInput'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorAlert } from '@/components/shared/ErrorAlert'
import { getTooltipForField } from '@/lib/schemaMapping'

// ── Helper sub-component for standard text fields ──────────
function Field({
  label,
  tooltip,
  value,
  onChange,
  required,
  placeholder,
  type = 'text',
}: {
  label: string
  tooltip?: string
  value: string
  onChange: (v: string) => void
  required?: boolean
  placeholder?: string
  type?: string
}) {
  return (
    <div>
      <label className="flex items-center text-xs font-medium text-[var(--foreground)] mb-1">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
        {tooltip && <FieldTooltip text={tooltip} />}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        className="premium-input"
      />
    </div>
  )
}

// ── SourcedField sub-component ─────────────────────────────
function SourcedFieldInput({
  label,
  tooltip,
  value,
  source,
  onValueChange,
  onSourceChange,
}: {
  label: string
  tooltip?: string
  value: string
  source: string
  onValueChange: (v: string) => void
  onSourceChange: (v: string) => void
}) {
  return (
    <div className="md:col-span-2">
      <label className="flex items-center text-xs font-medium text-[var(--foreground)] mb-1">
        {label}
        {tooltip && <FieldTooltip text={tooltip} />}
      </label>
      <textarea
        value={value}
        onChange={e => onValueChange(e.target.value)}
        rows={2}
        placeholder="Clinical finding or value..."
        className="premium-textarea"
      />
      <input
        type="text"
        value={source}
        onChange={e => onSourceChange(e.target.value)}
        placeholder="Source (e.g. PT note, Neurology consult, MRI report)..."
        className="premium-input mt-2"
      />
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────
export default function AnalyzePage() {
  const router = useRouter()
  const { analyze, isLoading, error, loadingStep } = useAnalyze()
  const [schema, setSchema] = useState<SchemaField[]>([])
  const [schemaError, setSchemaError] = useState<string | null>(null)
  const [validationError, setValidationError] = useState('')

  // Form state — all fields
  const [form, setForm] = useState({
    // Coverage
    payer_plan: '', requested_service: '', site_of_care: '',
    requested_los: '', payer_policy_version: '', payer_policy_excerpt: '',
    // Demographics
    age: '', sex: '',
    // Diagnosis
    primary_diagnosis: '', secondary_diagnoses: '',
    // Clinical Severity
    symptom_duration: '', pain_severity: '',
    adl_value: '', adl_source: '',
    neuro_value: '', neuro_source: '',
    vital_signs: '', mental_status: '',
    // History & Medication
    prior_conservative_treatment: '', response_to_prior_treatment: '',
    prior_surgeries_procedures: '', current_medications: '',
    medication_contraindications: '',
    // Diagnostics
    imaging_value: '', imaging_source: '',
    lab_results: '', pathology_biopsy: '', specialized_tests: '',
    // Utilization & Admin
    prior_hospitalizations_ed: '', complications_red_flags: '',
    ordering_provider_specialty: '', required_prerequisites: '',
    missing_records: '', contradictory_flags: '', known_exclusions_present: '',
    utilization_review_note: '',
    // Raw notes
    raw_clinical_notes: '',
  })

  useEffect(() => {
    fetchInputSchema()
      .then(setSchema)
      .catch(err => {
        setSchemaError('Failed to load schema. Tooltips may be limited.')
        console.error('Schema load error:', err)
      })
  }, [])

  function getTooltip(fieldName: string): string {
    return getTooltipForField(schema, fieldName)
  }

  function set(key: keyof typeof form) {
    return (v: string) => setForm(prev => ({ ...prev, [key]: v }))
  }

  function handleReset() {
    setForm(Object.fromEntries(Object.keys(form).map(k => [k, ''])) as typeof form)
    setValidationError('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setValidationError('')

    if (!form.requested_service.trim()) {
      setValidationError('Requested Service is required.')
      return
    }
    if (!form.primary_diagnosis.trim()) {
      setValidationError('Primary Diagnosis is required.')
      return
    }

    const input: PreAuthCaseInput = {
      payer_plan: form.payer_plan || undefined,
      requested_service: form.requested_service,
      site_of_care: form.site_of_care || undefined,
      requested_los: form.requested_los || undefined,
      payer_policy_version: form.payer_policy_version || undefined,
      payer_policy_excerpt: form.payer_policy_excerpt || undefined,
      age: form.age ? parseInt(form.age) : undefined,
      sex: form.sex || undefined,
      primary_diagnosis: form.primary_diagnosis,
      secondary_diagnoses: form.secondary_diagnoses ? form.secondary_diagnoses.split(';').map(s => s.trim()).filter(Boolean) : undefined,
      symptom_duration: form.symptom_duration || undefined,
      pain_severity: form.pain_severity || undefined,
      functional_impairment_adls: form.adl_value ? { value: form.adl_value, source: form.adl_source || undefined } : undefined,
      objective_neurologic_deficits: form.neuro_value ? { value: form.neuro_value, source: form.neuro_source || undefined } : undefined,
      vital_signs: form.vital_signs || undefined,
      mental_status: form.mental_status || undefined,
      prior_conservative_treatment: form.prior_conservative_treatment ? form.prior_conservative_treatment.split(';').map(s => s.trim()).filter(Boolean) : undefined,
      response_to_prior_treatment: form.response_to_prior_treatment || undefined,
      prior_surgeries_procedures: form.prior_surgeries_procedures || undefined,
      current_medications: form.current_medications ? form.current_medications.split(';').map(s => s.trim()).filter(Boolean) : undefined,
      medication_contraindications: form.medication_contraindications || undefined,
      imaging_findings: form.imaging_value ? { value: form.imaging_value, source: form.imaging_source || undefined } : undefined,
      lab_results: form.lab_results || undefined,
      pathology_biopsy: form.pathology_biopsy || undefined,
      specialized_tests: form.specialized_tests || undefined,
      prior_hospitalizations_ed: form.prior_hospitalizations_ed || undefined,
      complications_red_flags: form.complications_red_flags || undefined,
      ordering_provider_specialty: form.ordering_provider_specialty || undefined,
      required_prerequisites: form.required_prerequisites || undefined,
      missing_records: form.missing_records || undefined,
      contradictory_flags: form.contradictory_flags || undefined,
      known_exclusions_present: form.known_exclusions_present || undefined,
      utilization_review_note: form.utilization_review_note || undefined,
      raw_clinical_notes: form.raw_clinical_notes || undefined,
    }

    const output = await analyze(input)
    if (output) router.push('/result')
  }

  if (isLoading) return <LoadingSpinner step={loadingStep} />

  return (
    <div className="responsive-container">
      <div className="page-header mb-4">
        <h1 className="text-sm font-semibold text-[var(--foreground)]">
          Manual Case Entry
        </h1>
        <p className="text-[10px] text-[var(--muted-foreground)]">
          Fields marked <span className="text-red-500">*</span> are required.
        </p>
      </div>

      {validationError && (
        <div className="mb-4">
          <ErrorAlert message={validationError} />
        </div>
      )}
      {schemaError && (
        <div className="mb-4">
          <ErrorAlert message={schemaError} />
        </div>
      )}
      {error && (
        <div className="mb-4">
          <ErrorAlert message={error} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Section 1 — Administrative */}
        <FormSection title="Coverage & Administrative" fieldCount={6} defaultOpen={true}>
          <Field label="Payer / Plan" tooltip={getTooltip('payer')} value={form.payer_plan} onChange={set('payer_plan')} placeholder="e.g. Commercial PPO" />
          <Field label="Requested Service" tooltip={getTooltip('requested service')} value={form.requested_service} onChange={set('requested_service')} required placeholder="e.g. C5-C6 cervical decompression/fusion" />
          <Field label="Site of Care" tooltip={getTooltip('site of care')} value={form.site_of_care} onChange={set('site_of_care')} placeholder="Inpatient / Outpatient / ASC" />
          <Field label="Requested Length of Stay" tooltip={getTooltip('length of stay')} value={form.requested_los} onChange={set('requested_los')} placeholder="e.g. 2 midnights" />
          <Field label="Payer Policy Version" tooltip={getTooltip('payer policy')} value={form.payer_policy_version} onChange={set('payer_policy_version')} placeholder="e.g. Commercial Spine Surgery Policy v2026.1" />
          <div className="md:col-span-2">
            <label className="flex items-center text-xs font-medium text-[var(--foreground)] mb-1">
              Payer Policy Excerpt
              <FieldTooltip text="Paste relevant policy text if available. The system will extract approval criteria." />
            </label>
            <textarea value={form.payer_policy_excerpt} onChange={e => set('payer_policy_excerpt')(e.target.value)} rows={2} className="premium-textarea" placeholder="Paste policy text..." />
          </div>
        </FormSection>

        {/* Section 2 — Demographics */}
        <FormSection title="Demographics" fieldCount={2}>
          <Field label="Age" tooltip={getTooltip('age')} value={form.age} onChange={set('age')} type="number" placeholder="58" />
          <Field label="Sex" tooltip={getTooltip('sex')} value={form.sex} onChange={set('sex')} placeholder="Male / Female" />
        </FormSection>

        {/* Section 3 — Diagnosis */}
        <FormSection title="Diagnosis" fieldCount={2} defaultOpen={true}>
          <Field label="Primary Diagnosis" tooltip={getTooltip('primary diagnosis')} value={form.primary_diagnosis} onChange={set('primary_diagnosis')} required placeholder="e.g. Cervical spondylotic myelopathy" />
          <Field label="Secondary Diagnoses / Comorbidities" tooltip={getTooltip('secondary')} value={form.secondary_diagnoses} onChange={set('secondary_diagnoses')} placeholder="Separate with semicolons: Type 2 diabetes; OSA" />
        </FormSection>

        {/* Section 4 — Clinical Severity */}
        <FormSection title="Clinical Severity" fieldCount={6}>
          <Field label="Symptom Duration" tooltip={getTooltip('symptom duration')} value={form.symptom_duration} onChange={set('symptom_duration')} placeholder="e.g. 8 months" />
          <Field label="Pain Severity" tooltip={getTooltip('pain severity')} value={form.pain_severity} onChange={set('pain_severity')} placeholder="e.g. 8/10, worse with extension" />
          <SourcedFieldInput
            label="Functional Impairment / ADLs"
            tooltip={getTooltip('functional impairment')}
            value={form.adl_value}
            source={form.adl_source}
            onValueChange={set('adl_value')}
            onSourceChange={set('adl_source')}
          />
          <SourcedFieldInput
            label="Objective Neurologic Deficits"
            tooltip={getTooltip('neurologic')}
            value={form.neuro_value}
            source={form.neuro_source}
            onValueChange={set('neuro_value')}
            onSourceChange={set('neuro_source')}
          />
          <Field label="Vital Signs" tooltip={getTooltip('vital signs')} value={form.vital_signs} onChange={set('vital_signs')} placeholder="e.g. Fever 38.7C; HR 118" />
          <Field label="Mental Status / Cognition" tooltip={getTooltip('mental status')} value={form.mental_status} onChange={set('mental_status')} placeholder="e.g. Mild aphasia, follows commands" />
        </FormSection>

        {/* Section 5 — History & Medication */}
        <FormSection title="History & Medication" fieldCount={5}>
          <Field label="Prior Conservative Treatment" tooltip={getTooltip('conservative')} value={form.prior_conservative_treatment} onChange={set('prior_conservative_treatment')} placeholder="Separate with semicolons: PT; NSAIDs; ESI" />
          <Field label="Response to Prior Treatment" tooltip={getTooltip('response')} value={form.response_to_prior_treatment} onChange={set('response_to_prior_treatment')} placeholder="e.g. Transient relief from ESI" />
          <Field label="Prior Surgeries / Procedures" tooltip={getTooltip('surgeries')} value={form.prior_surgeries_procedures} onChange={set('prior_surgeries_procedures')} placeholder="e.g. No prior cervical surgery" />
          <Field label="Current Medications" tooltip={getTooltip('medication')} value={form.current_medications} onChange={set('current_medications')} placeholder="Separate with semicolons: Metformin; gabapentin" />
          <Field label="Medication Contraindications / Allergies" tooltip={getTooltip('contraindication')} value={form.medication_contraindications} onChange={set('medication_contraindications')} placeholder="e.g. Allergies: NSAIDs" />
        </FormSection>

        {/* Section 6 — Diagnostics */}
        <FormSection title="Diagnostics" fieldCount={4}>
          <SourcedFieldInput
            label="Imaging Findings"
            tooltip={getTooltip('imaging')}
            value={form.imaging_value}
            source={form.imaging_source}
            onValueChange={set('imaging_value')}
            onSourceChange={set('imaging_source')}
          />
          <Field label="Lab Results and Trends" tooltip={getTooltip('lab')} value={form.lab_results} onChange={set('lab_results')} placeholder="e.g. HbA1c 8.1%; CRP 24" />
          <Field label="Pathology / Biopsy / Culture" tooltip={getTooltip('pathology')} value={form.pathology_biopsy} onChange={set('pathology_biopsy')} placeholder="e.g. Biopsy-confirmed malignancy" />
          <Field label="Specialized Tests" tooltip={getTooltip('specialized')} value={form.specialized_tests} onChange={set('specialized_tests')} placeholder="e.g. EMG supports CIDP" />
        </FormSection>

        {/* Section 7 — Utilization & Quality */}
        <FormSection title="Utilization & Quality" fieldCount={9}>
          <Field label="Prior Hospitalizations / ED Visits" tooltip={getTooltip('hospitalization')} value={form.prior_hospitalizations_ed} onChange={set('prior_hospitalizations_ed')} placeholder="e.g. 2 ED visits in past month" />
          <Field label="Complications / Red Flags" tooltip={getTooltip('complications')} value={form.complications_red_flags} onChange={set('complications_red_flags')} placeholder="e.g. Progressive gait imbalance" />
          <Field label="Ordering Provider Specialty" tooltip={getTooltip('specialty')} value={form.ordering_provider_specialty} onChange={set('ordering_provider_specialty')} placeholder="e.g. Orthopedic spine surgeon" />
          <Field label="Required Prerequisites Completed" tooltip={getTooltip('prerequisites')} value={form.required_prerequisites} onChange={set('required_prerequisites')} placeholder="e.g. TB/HBV pending" />
          <Field label="Missing Records" tooltip={getTooltip('missing')} value={form.missing_records} onChange={set('missing_records')} placeholder="e.g. No recent ADL statement" />
          <Field label="Contradictory Documentation Flags" tooltip={getTooltip('contradict')} value={form.contradictory_flags} onChange={set('contradictory_flags')} placeholder="e.g. One note says no weakness" />
          <Field label="Known Exclusions Present" value={form.known_exclusions_present} onChange={set('known_exclusions_present')} placeholder="e.g. BMI elevated; not excluded" />
          <div className="md:col-span-2">
            <label className="text-xs font-medium text-[var(--foreground)] mb-1 block">
              Utilization Review Note
              <FieldTooltip text="Paste any prior UR assessment, denial letter, or pend conditions here." />
            </label>
            <textarea value={form.utilization_review_note} onChange={e => set('utilization_review_note')(e.target.value)} rows={2} className="premium-textarea" placeholder="Prior denial reasons or pend conditions..." />
          </div>
        </FormSection>

        {/* Raw clinical notes — always visible */}
        <RawNotesInput
          value={form.raw_clinical_notes}
          onChange={set('raw_clinical_notes')}
        />

        {/* Action buttons */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 premium-button-primary"
          >
            Analyze Case
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="premium-button-secondary"
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  )
}