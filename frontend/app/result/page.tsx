'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAnalyze, readStoredResult } from '@/hooks/useAnalyze'
import type { PreAuthSkillOutput } from '@/lib/types'
import { RecommendationBanner } from '@/components/result/RecommendationBanner'
import { ClinicalSummaryCard } from '@/components/result/ClinicalSummaryCard'
import { CriteriaTable } from '@/components/result/CriteriaTable'
import { EvidencePanel } from '@/components/result/EvidencePanel'
import { MissingInfoPanel } from '@/components/result/MissingInfoPanel'
import { ProviderQueryBox } from '@/components/result/ProviderQueryBox'
import { FlipConditionBox } from '@/components/result/FlipConditionBox'
import { AppealDirectionBox } from '@/components/result/AppealDirectionBox'
import { ProcessingMetaFooter } from '@/components/result/ProcessingMetaFooter'
import { CopyButton } from '@/components/shared/CopyButton'
import { exportJson, buildMarkdownReport } from '@/lib/utils'

export default function ResultPage() {
  const router = useRouter()
  const { result, clearResult } = useAnalyze()

  // Try to get result from hook state first, then from sessionStorage
  const [pageResult, setPageResult] = useState<PreAuthSkillOutput | null>(result)

  useEffect(() => {
    // If we don't have result from hook, try sessionStorage
    if (!result) {
      const stored = readStoredResult()
      if (stored) {
        setPageResult(stored)
      } else {
        // No stored result, redirect to home
        router.push('/')
      }
    }
  }, [result, router])

  if (!pageResult) {
    return null
  }

  // At this point, pageResult is guaranteed to be non-null
  const currentResult = pageResult

  function handleExportJson() {
    exportJson(currentResult, `preauth-result-${currentResult.case_id}.json`)
  }

  function handleNewCase() {
    clearResult()
    router.push('/')
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <h1 className="text-sm font-semibold text-[var(--foreground)]">
          Analysis Result
        </h1>
        <div className="flex flex-wrap gap-1.5">
          <CopyButton text={buildMarkdownReport(currentResult)} label="Copy Report" />
          <button
            onClick={handleExportJson}
            className="premium-button-secondary text-[10px] px-2.5 py-0.5"
          >
            Export JSON
          </button>
          <button
            onClick={handleNewCase}
            className="premium-button-primary text-[10px] px-2.5 py-0.5"
          >
            New Case
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <RecommendationBanner output={currentResult} />

        <ClinicalSummaryCard summary={currentResult.clinical_summary} />

        <CriteriaTable criteria={currentResult.criteria_results} />

        <EvidencePanel evidence={currentResult.supporting_evidence} />

        <MissingInfoPanel items={currentResult.missing_information} />

        <ProviderQueryBox query={currentResult.provider_query} />

        {currentResult.flip_condition && <FlipConditionBox condition={currentResult.flip_condition} />}

        {currentResult.appeal_direction && <AppealDirectionBox direction={currentResult.appeal_direction} />}

        <ProcessingMetaFooter
          totalMs={currentResult.processing_time_ms}
          step1Ms={currentResult.step1_time_ms}
          step2Ms={currentResult.step2_time_ms}
          model={currentResult.model_used}
        />
      </div>
    </div>
  )
}