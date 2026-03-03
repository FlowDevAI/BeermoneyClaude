"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Activity } from "lucide-react"
import { format } from "date-fns"
import { mockAgentLogs } from "@/lib/mock-data"
import { LOG_LEVEL_COLORS } from "@/lib/constants"

const recentLogs = [...mockAgentLogs].reverse().slice(0, 12)

export function RecentActivity() {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-medium text-zinc-200">
          <Activity className="h-4 w-4 text-zinc-400" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[340px] px-4 pb-4">
          <div className="flex flex-col gap-2">
            {recentLogs.map((log) => (
              <div key={log.id} className="flex items-start gap-3 rounded-lg p-2 hover:bg-zinc-800/50 transition-colors">
                <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
                  log.level === "info" ? "bg-emerald-500" :
                  log.level === "warning" ? "bg-amber-500" :
                  log.level === "error" || log.level === "critical" ? "bg-red-500" :
                  "bg-zinc-500"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-500">
                      {format(new Date(log.created_at), "HH:mm")}
                    </span>
                    {log.platform_slug && (
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-zinc-700 text-zinc-400">
                        {log.platform_slug}
                      </Badge>
                    )}
                  </div>
                  <p className={`text-sm mt-0.5 ${LOG_LEVEL_COLORS[log.level] ?? "text-zinc-300"}`}>
                    {log.message}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
