'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface FormSectionProps {
  title: string
  fieldCount: number
  defaultOpen?: boolean
  children: React.ReactNode
}

export function FormSection({
  title,
  fieldCount,
  defaultOpen = false,
  children,
}: FormSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="form-section">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-left mb-3"
      >
        <span className="flex items-center gap-2">
          {open ? (
            <ChevronDown className="h-3.5 w-3.5 text-[var(--muted-foreground)]" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 text-[var(--muted-foreground)]" />
          )}
          <span className="text-xs font-medium text-[var(--foreground)]">{title}</span>
          <span className="text-[10px] text-[var(--muted-foreground)]">({fieldCount})</span>
        </span>
      </button>
      {open && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {children}
        </div>
      )}
    </div>
  )
}