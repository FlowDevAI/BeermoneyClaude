"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { format, parseISO } from "date-fns"
import { mockDailyStats } from "@/lib/mock-data"

const chartData = mockDailyStats.map((d) => ({
  date: format(parseISO(d.date), "EEE"),
  earnings: d.total_earned_eur,
  fullDate: d.date,
}))

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ value: number; payload: { fullDate: string } }> }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm shadow-lg">
      <p className="text-zinc-400">{payload[0].payload.fullDate}</p>
      <p className="font-medium text-emerald-500">{payload[0].value.toFixed(2)}&euro;</p>
    </div>
  )
}

export function EarningsChart() {
  const total = mockDailyStats.reduce((sum, d) => sum + d.total_earned_eur, 0)

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base font-medium text-zinc-200">
            <TrendingUp className="h-4 w-4 text-zinc-400" />
            Last 7 Days
          </CardTitle>
          <span className="text-sm font-medium text-emerald-500">{total.toFixed(2)}&euro; total</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: -20 }}>
              <XAxis
                dataKey="date"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#71717a", fontSize: 12 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#71717a", fontSize: 12 }}
                tickFormatter={(v: number) => `${v}\u20AC`}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
              <Bar dataKey="earnings" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
