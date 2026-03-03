export const TIER_COLORS: Record<number, string> = {
  1: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/30',
  2: 'text-blue-500 bg-blue-500/10 border-blue-500/30',
  3: 'text-amber-500 bg-amber-500/10 border-amber-500/30',
  4: 'text-zinc-400 bg-zinc-500/10 border-zinc-500/30',
}

export const TIER_DOT: Record<number, string> = {
  1: 'bg-emerald-500',
  2: 'bg-blue-500',
  3: 'bg-amber-500',
  4: 'bg-zinc-500',
}

export const URGENCY_COLORS: Record<string, string> = {
  critical: 'text-red-500 bg-red-500/10 border-red-500/30',
  high: 'text-orange-500 bg-orange-500/10 border-orange-500/30',
  medium: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30',
  low: 'text-zinc-400 bg-zinc-500/10 border-zinc-500/30',
}

export const URGENCY_BORDER: Record<string, string> = {
  critical: 'border-l-red-500',
  high: 'border-l-orange-500',
  medium: 'border-l-yellow-500',
  low: 'border-l-zinc-600',
}

export const STATUS_COLORS: Record<string, string> = {
  ok: 'text-emerald-500',
  active: 'text-emerald-500',
  testing: 'text-blue-500',
  failed: 'text-red-500',
  broken: 'text-red-500',
  captcha: 'text-amber-500',
  warning: 'text-amber-500',
  pending: 'text-blue-500',
  planned: 'text-zinc-500',
  unknown: 'text-zinc-500',
}

export const LOG_LEVEL_COLORS: Record<string, string> = {
  info: 'text-emerald-500',
  warning: 'text-amber-500',
  error: 'text-red-500',
  critical: 'text-red-500',
  debug: 'text-zinc-500',
}

export const REASON_LABELS: Record<string, string> = {
  captcha: 'CAPTCHA',
  voice_test: 'Voice Test',
  opinion_survey: 'Opinion Survey',
  screener_complex: 'Complex Screener',
  manual_review: 'Manual Review',
}
