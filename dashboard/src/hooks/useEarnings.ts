"use client"

import { useState } from "react"
import type { Earning, DailyStats } from "@/lib/supabase/types"
import { mockEarnings, mockDailyStats } from "@/lib/mock-data"

export function useEarnings() {
  const [earnings] = useState<Earning[]>(mockEarnings)
  const [dailyStats] = useState<DailyStats[]>(mockDailyStats)
  const [loading] = useState(false)

  const todayStats = dailyStats[dailyStats.length - 1] ?? null
  const yesterdayStats = dailyStats[dailyStats.length - 2] ?? null
  const weekTotal = dailyStats.reduce((sum, d) => sum + d.total_earned_eur, 0)

  return { earnings, dailyStats, todayStats, yesterdayStats, weekTotal, loading }
}
