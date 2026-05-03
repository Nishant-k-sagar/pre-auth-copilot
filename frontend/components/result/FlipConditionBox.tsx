interface FlipConditionBoxProps {
  condition: string
}

export function FlipConditionBox({ condition }: FlipConditionBoxProps) {
  return (
    <div className="rounded-xl border border-teal-200 bg-teal-50 px-3 py-2">
      <p className="text-[10px] font-medium text-teal-900 mb-1 uppercase tracking-wider">
        What Would Flip This to Approval?
      </p>
      <p className="text-[10px] text-teal-800 leading-relaxed">{condition}</p>
    </div>
  )
}