import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { Recommendation, Confidence, CriterionStatus } from './types'
import type { PreAuthSkillOutput } from './types'

// ── Tailwind class merger ──────────────────────────────────
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ── Recommendation → colors ───────────────────────────────
// Note: 'ERROR' is included for validation results that failed to process
export type RecommendationWithStatus = Recommendation | 'ERROR'

export const RECOMMENDATION_BG: Record<Recommendation, string> = {
  LIKELY_APPROVE: 'bg-green-600',
  NEED_MORE_INFO: 'bg-amber-500',
  LIKELY_DENY:    'bg-red-600',
}

export const RECOMMENDATION_BORDER: Record<Recommendation, string> = {
  LIKELY_APPROVE: 'border-green-600',
  NEED_MORE_INFO: 'border-amber-500',
  LIKELY_DENY:    'border-red-600',
}

export const RECOMMENDATION_TEXT_COLOR: Record<Recommendation, string> = {
  LIKELY_APPROVE: 'text-green-700',
  NEED_MORE_INFO: 'text-amber-700',
  LIKELY_DENY:    'text-red-700',
}

export const RECOMMENDATION_LABEL: Record<Recommendation, string> = {
  LIKELY_APPROVE: 'Likely Approve',
  NEED_MORE_INFO: 'Needs More Information',
  LIKELY_DENY:    'Likely Deny',
}

// Helper to safely get label for validation results that may include 'ERROR'
export function getRecommendationLabel(value: Recommendation | 'ERROR'): string {
  if (value === 'ERROR') return 'Error'
  return RECOMMENDATION_LABEL[value]
}

// Helper to safely get text color for validation results that may include 'ERROR'
export function getRecommendationTextColor(value: Recommendation | 'ERROR'): string {
  if (value === 'ERROR') return 'text-[var(--muted-foreground)]'
  return RECOMMENDATION_TEXT_COLOR[value]
}

// ── Confidence → colors ───────────────────────────────────
export const CONFIDENCE_BADGE: Record<Confidence, string> = {
  HIGH:   'bg-green-100 text-green-800 border border-green-300',
  MEDIUM: 'bg-amber-100 text-amber-800 border border-amber-300',
  LOW:    'bg-red-100   text-red-800   border border-red-300',
}

// ── Criterion status → colors ─────────────────────────────
export const STATUS_BADGE: Record<CriterionStatus, string> = {
  MET:     'bg-green-100 text-green-800',
  PARTIAL: 'bg-amber-100 text-amber-800',
  UNMET:   'bg-red-100   text-red-800',
  'N/A':   'bg-gray-100  text-gray-600',
}

// ── Source → consistent pill color ───────────────────────
// Same source always gets same color for visual traceability.
// Uses deterministic hash-based color assignment to avoid SSR/client hydration mismatches.
const SOURCE_COLORS = [
  'bg-blue-100 text-blue-800',
  'bg-purple-100 text-purple-800',
  'bg-teal-100 text-teal-800',
  'bg-orange-100 text-orange-800',
  'bg-pink-100 text-pink-800',
  'bg-indigo-100 text-indigo-800',
]

/**
 * Deterministically map a string to a color index using a simple hash.
 * This ensures consistent colors across server and client renders.
 */
function _hashStringToIndex(str: string, max: number): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash) % max
}

export function getSourceColor(source: string): string {
  const key = source.toLowerCase().split('(')[0].trim() // normalize
  const colorIndex = _hashStringToIndex(key, SOURCE_COLORS.length)
  return SOURCE_COLORS[colorIndex]
}

// ── Time formatters ───────────────────────────────────────
export function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

// ── File export ───────────────────────────────────────────
export function exportJson(data: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Markdown report generator (for Copy Report button) ───
export function buildMarkdownReport(output: PreAuthSkillOutput): string {
  const lines: string[] = [
    `# Pre-Authorization Review — ${output.case_id}`,
    `**Service:** ${output.requested_service}`,
    `**Recommendation:** ${RECOMMENDATION_LABEL[output.recommendation]}`,
    `**Confidence:** ${output.confidence}`,
    '',
    '## Clinical Summary',
    output.clinical_summary,
    '',
    '## Criteria Evaluation',
  ]

  for (const c of output.criteria_results) {
    lines.push(`### ${c.criterion_id}: ${c.criterion_name} — ${c.status}`)
    if (c.supporting_evidence) lines.push(`**Evidence:** ${c.supporting_evidence}`)
    if (c.gap_or_risk) lines.push(`**Gap/Risk:** ${c.gap_or_risk}`)
    lines.push('')
  }

  if (output.missing_information.length > 0) {
    lines.push('## Missing Information')
    for (const item of output.missing_information) {
      lines.push(`- ${item}`)
    }
    lines.push('')
  }

  if (output.provider_query) {
    lines.push('## Provider Query')
    lines.push(output.provider_query)
    lines.push('')
  }

  if (output.flip_condition) {
    lines.push('## What Would Flip This to Approval')
    lines.push(output.flip_condition)
    lines.push('')
  }

  if (output.appeal_direction) {
    lines.push('## Appeal Direction')
    lines.push(output.appeal_direction)
    lines.push('')
  }

  lines.push(`---`)
  lines.push(`*Analyzed in ${formatMs(output.processing_time_ms)} using ${output.model_used}*`)

  return lines.join('\n')
}