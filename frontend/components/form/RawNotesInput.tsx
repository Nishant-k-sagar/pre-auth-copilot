interface RawNotesInputProps {
  value: string
  onChange: (v: string) => void
}

export function RawNotesInput({ value, onChange }: RawNotesInputProps) {
  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card)] p-4">
      <label className="block text-xs font-medium text-[var(--foreground)] mb-1">
        Raw Clinical Notes
        <span className="ml-1.5 text-[10px] font-normal text-[var(--muted-foreground)]">
          (optional — paste unstructured notes here)
        </span>
      </label>
      <p className="text-[10px] text-[var(--muted-foreground)] mb-2">
        The system will extract relevant facts automatically. Useful for pasting H&P, progress notes, or prior authorization letters.
      </p>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        rows={5}
        className="w-full rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2 text-xs text-[var(--card-foreground)] focus:border-[var(--ring)] focus:outline-none focus:ring-1 focus:ring-[var(--ring)] font-mono"
        placeholder="Paste clinical notes, H&P, imaging reports, or any unstructured case text here..."
      />
    </div>
  )
}