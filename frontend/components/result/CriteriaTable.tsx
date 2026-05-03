import type { CriterionResult } from '@/lib/types'
import { STATUS_BADGE } from '@/lib/utils'

interface CriteriaTableProps {
  criteria: CriterionResult[]
}

export function CriteriaTable({ criteria }: CriteriaTableProps) {
  return (
    <div className="premium-card p-0 overflow-hidden">
      <div className="px-3 py-2 border-b border-[var(--border)]">
        <h2 className="text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider">
          Criteria Evaluation
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="premium-table">
          <thead>
            <tr>
              <th className="w-8">#</th>
              <th>Criterion</th>
              <th className="w-20">Status</th>
              <th className="hidden sm:table-cell">Supporting Evidence</th>
              <th className="hidden md:table-cell">Gap / Risk</th>
            </tr>
          </thead>
          <tbody>
            {criteria.map(c => (
              <tr key={c.criterion_id}>
                <td className="font-mono text-[var(--muted-foreground)]">{c.criterion_id}</td>
                <td className="text-[var(--card-foreground)]">{c.criterion_name}</td>
                <td>
                  <span className={`inline-flex items-center rounded-md px-1 py-0.5 text-[10px] font-medium ${STATUS_BADGE[c.status]}`}>
                    {c.status}
                  </span>
                </td>
                <td className="text-[var(--muted-foreground)] hidden sm:table-cell">
                  {c.supporting_evidence || <span className="text-[var(--muted-foreground)]/50">—</span>}
                </td>
                <td className="hidden md:table-cell">
                  {c.gap_or_risk ? (
                    <span className="text-amber-600">{c.gap_or_risk}</span>
                  ) : (
                    <span className="text-[var(--muted-foreground)]/50">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}