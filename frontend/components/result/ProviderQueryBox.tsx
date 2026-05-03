import { CopyButton } from '@/components/shared/CopyButton'

interface ProviderQueryBoxProps {
  query: string
}

export function ProviderQueryBox({ query }: ProviderQueryBoxProps) {
  if (!query) return null

  return (
    <div className="premium-card">
      <div className="flex items-center justify-between mb-1.5">
        <h2 className="text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wider">
          Provider Query
        </h2>
        <CopyButton text={query} label="Copy" />
      </div>
      <p className="text-[10px] text-[var(--card-foreground)] whitespace-pre-wrap leading-relaxed">
        {query}
      </p>
    </div>
  )
}