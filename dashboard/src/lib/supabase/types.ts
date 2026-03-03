export type Platform = {
  id: string
  slug: string
  name: string
  url: string
  login_url: string | null
  dashboard_url: string | null
  category: 'research' | 'ux_testing' | 'microtasks' | 'surveys' | 'beta' | 'search_eval'
  tier: 1 | 2 | 3 | 4
  avg_pay_min: number | null
  avg_pay_max: number | null
  currency: string
  payment_methods: string[]
  frequency: string | null
  spain_available: boolean
  plugin_status: 'planned' | 'research' | 'dev' | 'testing' | 'active' | 'broken'
  active: boolean
  check_interval_seconds: number
  last_scanned_at: string | null
  last_task_found_at: string | null
  last_login_at: string | null
  login_status: 'ok' | 'failed' | 'captcha' | 'unknown'
  notes: string | null
  created_at: string
  updated_at: string
}

export type Opportunity = {
  id: string
  platform_id: string
  source: 'scan' | 'email' | 'manual'
  external_id: string | null
  title: string | null
  description: string | null
  estimated_pay: number | null
  currency: string
  estimated_minutes: number | null
  effective_hourly_rate: number | null
  url: string | null
  priority: 'critical' | 'high' | 'medium' | 'low'
  score: number | null
  score_breakdown: Record<string, number> | null
  difficulty: 'auto' | 'semi_auto' | 'human'
  status: 'detected' | 'accepted' | 'reserved' | 'in_progress' | 'completed' | 'expired' | 'skipped' | 'failed'
  agent_action: string | null
  needs_human: boolean
  human_reason: string | null
  human_instructions: string | null
  deadline: string | null
  screenshot_path: string | null
  detected_at: string
  accepted_at: string | null
  completed_at: string | null
  created_at: string
}

export type HumanQueueItem = {
  id: string
  opportunity_id: string | null
  platform_slug: string
  task_title: string
  estimated_pay: number | null
  currency: string
  url: string | null
  reason: 'captcha' | 'voice_test' | 'opinion_survey' | 'screener_complex' | 'manual_review'
  instructions: string | null
  deadline: string | null
  urgency: 'critical' | 'high' | 'medium' | 'low'
  screenshot_path: string | null
  status: 'pending' | 'in_progress' | 'done' | 'skipped' | 'expired'
  actual_earnings: number | null
  actual_minutes: number | null
  completed_at: string | null
  created_at: string
}

export type Earning = {
  id: string
  platform_id: string
  opportunity_id: string | null
  amount: number
  currency: string
  amount_eur: number | null
  task_type: 'survey' | 'ux_test' | 'microtask' | 'interview' | 'screener' | 'bug_report' | null
  task_description: string | null
  time_spent_minutes: number | null
  effective_hourly_rate: number | null
  completed_by: 'agent' | 'human' | 'mixed'
  payment_status: 'pending' | 'processing' | 'paid'
  payment_date: string | null
  notes: string | null
  completed_at: string
  created_at: string
}

export type AgentLog = {
  id: string
  session_id: string | null
  event_type: 'start' | 'login' | 'scan' | 'accept' | 'complete' | 'captcha' | 'error' | 'queue' | 'stop'
  platform_slug: string | null
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  message: string | null
  details: Record<string, unknown> | null
  screenshot_path: string | null
  created_at: string
}

export type DailyStats = {
  id: string
  date: string
  total_earned_eur: number
  total_time_minutes: number
  effective_hourly_rate: number | null
  tasks_completed: number
  tasks_by_agent: number
  tasks_by_human: number
  opportunities_detected: number
  opportunities_accepted: number
  platforms_scanned: number
  best_platform: string | null
  best_hourly_rate: number | null
  created_at: string
}
