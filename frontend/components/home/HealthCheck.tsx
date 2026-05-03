'use client'

import { useEffect, useState } from 'react'
import { fetchHealth } from '@/lib/api'

export function HealthCheck() {
  const [status, setStatus] = useState<'checking' | 'ok' | 'error'>('checking')
  const [model, setModel] = useState<string>('')

  useEffect(() => {
    fetchHealth()
      .then(data => {
        setStatus('ok')
        setModel(data.model)
      })
      .catch(() => setStatus('error'))
  }, [])

  if (status === 'checking') {
    return (
      <div className="rounded-md border border-[var(--border)] bg-[var(--card)]/50 px-2.5 py-1.5">
        <div className="flex items-center gap-1.5 text-[10px] text-[var(--muted-foreground)]">
          <div className="h-1 w-1 rounded-full bg-[var(--muted-foreground)] animate-pulse" />
          Checking backend...
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="rounded-md border border-red-200 bg-red-50/50 px-2.5 py-1.5">
        <div className="flex items-center gap-1.5 text-[10px] text-red-700">
          <div className="h-1 w-1 rounded-full bg-red-500" />
          Backend unavailable
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-green-200 bg-white px-2.5 py-1.5">
      <div className="flex items-center gap-1.5 text-[10px] text-green-800">
        <div className="h-1 w-1 rounded-full bg-green-500" />
        Backend connected {model && `(${model})`}
      </div>
    </div>
  )
}