import { CopyButton } from '@/components/shared/CopyButton'

interface AppealDirectionBoxProps {
  direction: string
}

export function AppealDirectionBox({ direction }: AppealDirectionBoxProps) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2">
      <div className="flex items-center justify-between mb-1.5">
        <p className="text-[10px] font-medium text-red-900 uppercase tracking-wider">
          Appeal Direction
        </p>
        <CopyButton text={direction} label="Copy" />
      </div>
      <p className="text-[10px] text-red-800 leading-relaxed whitespace-pre-wrap">
        {direction}
      </p>
    </div>
  )
}