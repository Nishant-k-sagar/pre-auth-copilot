import { formatMs } from '@/lib/utils'

interface ProcessingMetaFooterProps {
  totalMs: number
  step1Ms: number
  step2Ms: number
  model: string
}

export function ProcessingMetaFooter({
  totalMs,
  step1Ms,
  step2Ms,
  model,
}: ProcessingMetaFooterProps) {
  return (
    <p className="text-center text-[10px] text-[var(--muted-foreground)] py-3">
      Analyzed in {formatMs(totalMs)} (normalize: {formatMs(step1Ms)}, evaluate: {formatMs(step2Ms)}) using {model}
    </p>
  )
}