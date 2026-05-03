'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronDown, FileText, Upload, Sparkles, Check } from 'lucide-react'
import type { TrainingCase, PreAuthCaseInput } from '@/lib/types'
import { RECOMMENDATION_LABEL, RECOMMENDATION_TEXT_COLOR } from '@/lib/utils'
import { useAnalyze } from '@/hooks/useAnalyze'
import { fetchComplexCaseInput } from '@/lib/api'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorAlert } from '@/components/shared/ErrorAlert'

interface CaseSelectorProps {
  cases: TrainingCase[]
}

export function CaseSelector({ cases }: CaseSelectorProps) {
  const router = useRouter()
  const { analyze, analyzeFile, isLoading, error, loadingStep } = useAnalyze()
  const [selectedId, setSelectedId] = useState<string>('')
  const [preview, setPreview] = useState<TrainingCase | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Order: complex case first, then PA-001 through PA-010
    const COMPLEX_OPTION_ID = 'PA-001-COMPLEX'
    const options = [
      { id: COMPLEX_OPTION_ID, label: 'PA-001 — Complex Case', fullLabel: 'PA-001 — Complex Case (Full 19-Row Packet)' },
      ...cases.map(c => ({
        id: c.case_id,
        label: `${c.case_id} — ${c.requested_service.slice(0, 50)}`,
        fullLabel: `${c.case_id} — ${c.requested_service.slice(0, 50)}`,
      })),
    ]

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function handleSelect(id: string) {
    setSelectedId(id)
    setIsOpen(false)
    if (id === COMPLEX_OPTION_ID) {
      const pa001 = cases.find(c => c.case_id === 'PA-001')
      if (pa001) setPreview({ ...pa001, has_full_packet: true })
    } else {
      const found = cases.find(c => c.case_id === id) || null
      setPreview(found)
    }
  }

  async function handleAnalyze() {
    if (!selectedId) return

    let caseData
    if (selectedId === COMPLEX_OPTION_ID) {
       caseData = await fetchComplexCaseInput()
     } else {
      const tc = cases.find(c => c.case_id === selectedId)
      if (!tc) return
      const MAX_RAW_NOTES = 20000
      const rawNotes = (
        `Clinical scenario: ${tc.clinical_scenario}\n` +
        `Supporting evidence: ${tc.key_supporting_evidence}\n` +
        `Gaps or risks: ${tc.key_gaps_or_risks}`
      ).slice(0, MAX_RAW_NOTES)
      caseData = {
        case_id: tc.case_id,
        requested_service: tc.requested_service,
        primary_diagnosis: tc.clinical_scenario,
        raw_clinical_notes: rawNotes,
      }
    }

    const output = await analyze(caseData)
    if (output) {
      router.push('/result')
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const output = await analyzeFile(file)
    if (output) {
      router.push('/result')
    }
  }

  const selectedOption = options.find(opt => opt.id === selectedId)

  if (isLoading) {
    return <LoadingSpinner step={loadingStep} />
  }

  return (
    <div className="premium-card">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4 text-[var(--primary)]" />
        <h2 className="text-sm font-medium text-[var(--foreground)]">
          Select a Pre-Auth Case
        </h2>
      </div>

      {/* Custom Dropdown - Fully Responsive */}
      <div className="relative mb-3" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--card)] px-3 py-2.5 pr-10 text-xs text-[var(--card-foreground)] hover:bg-[var(--muted)] focus:border-[var(--ring)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]/20 transition-all cursor-pointer"
        >
          <span className={selectedId ? 'text-[var(--card-foreground)]' : 'text-[var(--muted-foreground)]'}>
            {selectedOption ? selectedOption.label : '— Select a case —'}
          </span>
          <ChevronDown className={`h-3.5 w-3.5 text-[var(--muted-foreground)] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 max-h-60 overflow-y-auto rounded-lg border border-[var(--border)] bg-[var(--card)] py-1 shadow-lg z-50">
            {options.map(opt => (
              <button
                key={opt.id}
                type="button"
                onClick={() => handleSelect(opt.id)}
                className="w-full px-3 py-2 text-left text-xs text-[var(--card-foreground)] hover:bg-[var(--muted)] transition-colors flex items-center justify-between gap-2"
                title={opt.fullLabel}
              >
                <span className="truncate">{opt.label}</span>
                {selectedId === opt.id && <Check className="h-3 w-3 text-[var(--primary)] flex-shrink-0" />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Preview card */}
      {preview && (
        <div className="mb-3 rounded-lg bg-[var(--muted)]/50 p-3 border border-[var(--border)]">
          <p className="text-xs font-medium text-[var(--muted-foreground)] mb-1">Clinical Scenario</p>
          <p className="text-xs text-[var(--card-foreground)] mb-2 line-clamp-3 leading-relaxed">{preview.clinical_scenario}</p>
          <div className="flex flex-wrap items-center gap-1.5">
            <span
              className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${RECOMMENDATION_TEXT_COLOR[preview.expected_outcome]} border-current`}
            >
              Expected: {RECOMMENDATION_LABEL[preview.expected_outcome]}
            </span>
            {preview.has_full_packet && (
              <span className="text-[10px] bg-[var(--primary)]/10 text-[var(--primary)] px-2 py-0.5 rounded-full font-medium">
                Full Packet
              </span>
            )}
          </div>
          {preview.complexity_notes && (
            <p className="mt-2 text-[10px] text-[var(--muted-foreground)] italic line-clamp-2">
              {preview.complexity_notes}
            </p>
          )}
        </div>
      )}

      {/* Error */}
      {error && <div className="mb-3"><ErrorAlert message={error} /></div>}

      {/* Action buttons */}
      <div className="flex flex-col gap-2">
        <button
          onClick={handleAnalyze}
          disabled={!selectedId || isLoading}
          className="w-full premium-button-primary py-2 text-xs"
        >
          Analyze This Case
        </button>

        <label className="w-full cursor-pointer rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-medium text-[var(--muted-foreground)] hover:bg-[var(--muted)] transition-all text-center flex items-center justify-center gap-1.5">
          <Upload className="h-3.5 w-3.5" />
          Upload Excel Workbook
          <input
            type="file"
            accept=".xlsx"
            onChange={handleFileUpload}
            className="hidden"
          />
        </label>

        <a
          href="/analyze"
          className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-medium text-[var(--muted-foreground)] hover:bg-[var(--muted)] transition-all text-center flex items-center justify-center gap-1.5"
        >
          <FileText className="h-3.5 w-3.5" />
          Enter Case Manually
        </a>
      </div>
    </div>
  )
}