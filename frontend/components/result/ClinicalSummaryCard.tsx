interface ClinicalSummaryCardProps {
  summary: string
}

export function ClinicalSummaryCard({ summary }: ClinicalSummaryCardProps) {
  return (
    <div className="premium-card">
      <h2 className="text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider mb-1.5">
        Clinical Summary
      </h2>
      <p className="text-[10px] text-[var(--card-foreground)] leading-relaxed">{summary}</p>
    </div>
  )
}