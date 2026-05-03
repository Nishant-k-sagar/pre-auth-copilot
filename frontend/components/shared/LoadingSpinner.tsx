'use client'

interface LoadingSpinnerProps {
  step?: string
}

export function LoadingSpinner({ step }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
      <p className="text-sm text-[var(--muted-foreground)] min-h-[1.25rem]">
        {step || 'Processing...'}
      </p>
    </div>
  )
}