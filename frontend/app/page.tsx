import { fetchTrainingCases } from '@/lib/api'
import type { TrainingCase } from '@/lib/types'
import { CaseSelector } from '@/components/home/CaseSelector'
import { TrainingCasesTable } from '@/components/home/TrainingCasesTable'
import { HealthCheck } from '@/components/home/HealthCheck'

export default async function HomePage() {
  let cases: TrainingCase[] = []
  try {
    cases = await fetchTrainingCases()
  } catch {
    // Backend not running — show empty state; client-side error will handle it
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-0.5">
        <h1 className="text-xl font-semibold text-[var(--foreground)] tracking-tight">
          Pre-Auth Copilot
        </h1>
        <p className="text-xs text-[var(--muted-foreground)]">
          Select a case or upload a workbook for medical-necessity recommendation.
        </p>
      </div>
      
      <HealthCheck />

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left — selector */}
        <div className="lg:col-span-1">
          <CaseSelector cases={cases} />
        </div>

        {/* Right — info */}
        <div className="lg:col-span-2 space-y-3">
          <div className="premium-card">
            <h3 className="text-xs font-medium text-[var(--foreground)] mb-2">How It Works</h3>
            <ol className="space-y-1.5">
              {[
                'Select a training case or upload your own Excel workbook',
                'The system normalizes the clinical packet (Mistral call 1)',
                'It evaluates against payer policy criteria (Mistral call 2)',
                'You receive a structured recommendation with full audit trail'
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-[var(--muted-foreground)]">
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[var(--primary)]/10 text-[10px] font-medium text-[var(--primary)]">
                    {i + 1}
                  </span>
                  <span className="text-xs">{step}</span>
                </li>
              ))}
            </ol>
          </div>
          
          <div className="grid grid-cols-3 gap-1.5">
            {[
              { label: 'LIKELY_APPROVE', count: cases.filter(c => c.expected_outcome === 'LIKELY_APPROVE').length },
              { label: 'NEED_MORE_INFO', count: cases.filter(c => c.expected_outcome === 'NEED_MORE_INFO').length },
              { label: 'LIKELY_DENY', count: cases.filter(c => c.expected_outcome === 'LIKELY_DENY').length },
            ].map(({ label, count }) => (
              <div key={label} className="premium-card py-2 text-center">
                <div className={`text-[10px] font-medium mb-0.5 ${
                  label === 'LIKELY_APPROVE' ? 'text-green-600' :
                  label === 'NEED_MORE_INFO' ? 'text-amber-600' : 'text-red-600'
                }`}>
                  {label === 'LIKELY_APPROVE' ? 'Approve' :
                   label === 'NEED_MORE_INFO' ? 'More Info' : 'Deny'}
                </div>
                <div className="text-sm font-semibold text-[var(--foreground)]">
                  {count}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Training cases table */}
      <TrainingCasesTable cases={cases} />
    </div>
  )
}
