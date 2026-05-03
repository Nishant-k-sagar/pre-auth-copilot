'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import type { TrainingCase, ValidationSummary, ValidationProgressEvent } from '@/lib/types'
import { getRecommendationLabel, getRecommendationTextColor } from '@/lib/utils'
import { runValidation, runValidationStream } from '@/lib/api'
import { useAnalyze } from '@/hooks/useAnalyze'

interface TrainingCasesTableProps {
  cases: TrainingCase[]
}

export function TrainingCasesTable({ cases }: TrainingCasesTableProps) {
  const router = useRouter()
  const { analyze, isLoading } = useAnalyze()
  const [validation, setValidation] = useState<ValidationSummary | null>(null)
  const [validating, setValidating] = useState(false)
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null)
  const [analyzingId, setAnalyzingId] = useState<string | null>(null)

  async function handleRunValidation() {
    setValidating(true)
    setProgress(null)
    try {
      for await (const event of runValidationStream()) {
        if (event.type === 'progress') {
          setProgress({ current: event.current, total: event.total })
        } else if (event.type === 'complete' && event.result) {
          setValidation(event.result as ValidationSummary)
        }
      }
    } finally {
      setValidating(false)
      setProgress(null)
    }
  }

  async function handleAnalyzeCase(tc: TrainingCase) {
    setAnalyzingId(tc.case_id)
    const output = await analyze({
      case_id: tc.case_id,
      requested_service: tc.requested_service,
      primary_diagnosis: tc.clinical_scenario,
      raw_clinical_notes:
        `Clinical scenario: ${tc.clinical_scenario}\n` +
        `Supporting evidence: ${tc.key_supporting_evidence}\n` +
        `Gaps or risks: ${tc.key_gaps_or_risks}`,
    })
    setAnalyzingId(null)
    if (output) router.push('/result')
  }

  function getValidationResult(caseId: string) {
    return validation?.results.find(r => r.case_id === caseId)
  }

  return (
    <div className="premium-card p-0 overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 px-3 py-2 border-b border-[var(--border)]">
        <h2 className="text-xs font-medium text-[var(--muted-foreground)] uppercase tracking-wider">
          Training Cases
        </h2>
        <button
          onClick={handleRunValidation}
          disabled={validating}
          className="rounded-md border border-[var(--border)] px-2.5 py-0.5 text-xs font-medium text-[var(--muted-foreground)] hover:bg-[var(--muted)] disabled:opacity-50 transition-all"
        >
          {validating ? 'Running...' : 'Run Accuracy Check'}
        </button>
      </div>

      {progress && (
        <div className="px-3 py-1.5 bg-[var(--muted)]/30 border-b border-[var(--border)]">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-[var(--muted-foreground)]">
              Processing case {progress.current} of {progress.total}
            </span>
            <div className="flex-1 h-1 bg-[var(--border)] rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--primary)] transition-all duration-300"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {validation && (
        <div className="px-3 py-1.5 bg-[var(--muted)]/30 border-b border-[var(--border)] text-xs">
          <span className="font-medium text-[var(--foreground)]">
            Accuracy: {validation.correct}/{validation.total}
          </span>
          <span className="ml-1 text-[var(--muted-foreground)]">
            ({Math.round(validation.accuracy * 100)}%)
          </span>
        </div>
      )}

      {/* Table with horizontal scroll on small screens */}
      <div className="overflow-x-auto">
        <table className="premium-table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Service</th>
              <th>Expected</th>
              {validation && (
                <th>Actual</th>
              )}
              <th>Complexity</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {cases.map(tc => {
              const vr = getValidationResult(tc.case_id)
              return (
                <tr key={tc.case_id}>
                  <td className="font-mono text-xs text-[var(--muted-foreground)]">{tc.case_id}</td>
                  <td className="text-xs text-[var(--card-foreground)] max-w-[150px] truncate" title={tc.requested_service}>
                    {tc.requested_service}
                  </td>
                  <td className="text-xs">
                    <span className={`font-medium ${getRecommendationTextColor(tc.expected_outcome)}`}>
                      {getRecommendationLabel(tc.expected_outcome)}
                    </span>
                  </td>
                  {validation && (
                    <td className="text-xs">
                      {vr && (
                        <span className="flex items-center gap-1">
                          <span className={vr.match ? 'text-green-600' : 'text-red-600'}>
                            {vr.match ? 'Yes' : 'No'}
                          </span>
                          <span className={`font-medium ${getRecommendationTextColor(vr.actual)}`}>
                            {getRecommendationLabel(vr.actual)}
                          </span>
                        </span>
                      )}
                    </td>
                  )}
                  <td className="text-xs text-[var(--muted-foreground)] max-w-[120px] truncate" title={tc.complexity_notes}>
                    {tc.complexity_notes}
                  </td>
                  <td className="text-right">
                    <button
                      onClick={() => handleAnalyzeCase(tc)}
                      disabled={isLoading && analyzingId === tc.case_id}
                      className="rounded-md bg-[var(--primary)]/10 px-2 py-0.5 font-medium text-[var(--primary)] hover:bg-[var(--primary)]/20 disabled:opacity-50 transition-all text-xs mr-8"
                    >
                      {isLoading && analyzingId === tc.case_id ? 'Running...' : 'Analyze'}
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}