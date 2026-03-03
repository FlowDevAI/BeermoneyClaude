"use client"

import { Card, CardContent } from "@/components/ui/card"
import { DollarSign, Clock, TrendingUp, ClipboardList } from "lucide-react"
import { mockDailyStats, mockQueueItems } from "@/lib/mock-data"

const today = mockDailyStats[mockDailyStats.length - 1]
const yesterday = mockDailyStats[mockDailyStats.length - 2]
const pendingCount = mockQueueItems.filter(q => q.status === "pending").length

const stats = [
  {
    label: "Earned Today",
    value: `${today?.total_earned_eur.toFixed(2) ?? "0.00"}\u20AC`,
    icon: DollarSign,
    diff: today && yesterday ? today.total_earned_eur - yesterday.total_earned_eur : 0,
    diffLabel: "vs yesterday",
    iconColor: "text-emerald-500",
  },
  {
    label: "Time Today",
    value: `${((today?.total_time_minutes ?? 0) / 60).toFixed(1)}h`,
    icon: Clock,
    diff: today && yesterday ? today.total_time_minutes - yesterday.total_time_minutes : 0,
    diffLabel: "min vs yesterday",
    iconColor: "text-blue-500",
  },
  {
    label: "Rate \u20AC/h",
    value: `${today?.effective_hourly_rate?.toFixed(2) ?? "0.00"}\u20AC/h`,
    icon: TrendingUp,
    diff: today?.effective_hourly_rate && yesterday?.effective_hourly_rate
      ? today.effective_hourly_rate - yesterday.effective_hourly_rate
      : 0,
    diffLabel: "vs yesterday",
    iconColor: "text-amber-500",
  },
  {
    label: "In Queue",
    value: `${pendingCount}`,
    icon: ClipboardList,
    diff: 0,
    diffLabel: "pending tasks",
    iconColor: "text-violet-500",
  },
]

export function StatsCards() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <stat.icon className={`h-4 w-4 ${stat.iconColor}`} />
              {stat.label}
            </div>
            <p className="mt-2 text-2xl font-semibold text-zinc-50">{stat.value}</p>
            {stat.diff !== 0 ? (
              <p className={`mt-1 text-xs ${stat.diff > 0 ? "text-emerald-500" : "text-red-400"}`}>
                {stat.diff > 0 ? "+" : ""}
                {typeof stat.diff === "number" && stat.diffLabel.includes("min")
                  ? `${stat.diff}` : stat.diff.toFixed(2)}
                {" "}{stat.diffLabel}
              </p>
            ) : (
              <p className="mt-1 text-xs text-zinc-500">{stat.diffLabel}</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
