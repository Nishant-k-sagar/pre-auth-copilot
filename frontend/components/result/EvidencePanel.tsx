import type { EvidenceSnippet } from '@/lib/types'
import { getSourceColor } from '@/lib/utils'

interface EvidencePanelProps {
  evidence: EvidenceSnippet[]
}

export function EvidencePanel({ evidence }: EvidencePanelProps) {
  if (evidence.length === 0) return null

  return (
    <div className="premium-card">
      <h2 className="text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
        Supporting Evidence
      </h2>
      <div className="space-y-2">
        {evidence.map((e) => (
          <div key={`${e.source}-${e.excerpt}`} className="flex flex-col sm:flex-row gap-1.5 sm:gap-2 items-start">
            <span className={`shrink-0 rounded-md px-1.5 py-0.5 text-[10px] font-medium ${getSourceColor(e.source)}`}>
              {e.source}
            </span>
            <p className="text-[10px] text-[var(--card-foreground)] pt-0.5">{e.excerpt}</p>
          </div>
        ))}
      </div>
    </div>
  )
}