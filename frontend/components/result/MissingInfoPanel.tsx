interface MissingInfoPanelProps {
  items: string[]
}

export function MissingInfoPanel({ items }: MissingInfoPanelProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 px-3 py-2">
        <p className="text-[10px] font-medium text-green-800">
          No documentation gaps identified
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
      <p className="text-[10px] font-medium text-amber-900 mb-1.5">
        Documentation Gaps ({items.length})
      </p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-1.5 text-[10px] text-amber-800">
            <span className="shrink-0 font-bold">{i + 1}.</span>
            <span className="line-clamp-2">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}