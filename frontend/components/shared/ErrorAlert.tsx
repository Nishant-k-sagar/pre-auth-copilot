'use client'

interface ErrorAlertProps {
  message: string
  onRetry?: () => void
}

export function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3">
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 text-red-500 text-xs font-bold">[!]</span>
        <div className="flex-1">
          <p className="text-xs font-medium text-red-800">Analysis Failed</p>
          <p className="mt-0.5 text-xs text-red-700">{message}</p>
        </div>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 text-xs font-medium text-red-700 underline hover:text-red-900"
        >
          Try Again
        </button>
      )}
    </div>
  )
}