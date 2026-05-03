import type { PreAuthSkillOutput } from '@/lib/types'
import {
  RECOMMENDATION_BG,
  RECOMMENDATION_LABEL,
  CONFIDENCE_BADGE,
} from '@/lib/utils'

interface RecommendationBannerProps {
  output: PreAuthSkillOutput
}

export function RecommendationBanner({ output }: RecommendationBannerProps) {
  return (
    <div className={`${RECOMMENDATION_BG[output.recommendation]} rounded-xl px-4 py-3 shadow-sm`}>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
        <div>
          <p className="text-white/80 text-[10px] font-medium mb-0.5">
            {output.case_id} · {output.requested_service}
          </p>
          <h1 className="text-white text-lg font-semibold tracking-tight">
            {RECOMMENDATION_LABEL[output.recommendation]}
          </h1>
        </div>
        <div className="flex flex-col items-start sm:items-end gap-1 shrink-0">
          <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium ${CONFIDENCE_BADGE[output.confidence]}`}>
            {output.confidence} Confidence
          </span>
          <span className="text-white/70 text-[10px]">
            {output.model_used}
          </span>
        </div>
      </div>
    </div>
  )
}