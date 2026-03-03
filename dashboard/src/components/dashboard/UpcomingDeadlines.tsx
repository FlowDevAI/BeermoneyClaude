"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock, ExternalLink } from "lucide-react"
import { formatDistanceToNow, isPast } from "date-fns"
import { mockQueueItems } from "@/lib/mock-data"
import { URGENCY_COLORS, TIER_COLORS } from "@/lib/constants"
import { mockPlatforms } from "@/lib/mock-data"

const deadlineItems = mockQueueItems
  .filter((q) => q.status === "pending" && q.deadline)
  .sort((a, b) => new Date(a.deadline!).getTime() - new Date(b.deadline!).getTime())
  .slice(0, 5)

function getPlatformTier(slug: string) {
  return mockPlatforms.find((p) => p.slug === slug)?.tier ?? 4
}

export function UpcomingDeadlines() {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base font-medium text-zinc-200">
          <Clock className="h-4 w-4 text-zinc-400" />
          Upcoming Deadlines
        </CardTitle>
      </CardHeader>
      <CardContent>
        {deadlineItems.length === 0 ? (
          <p className="text-sm text-zinc-500">No upcoming deadlines</p>
        ) : (
          <div className="flex flex-col gap-3">
            {deadlineItems.map((item) => {
              const expired = isPast(new Date(item.deadline!))
              const tier = getPlatformTier(item.platform_slug)
              return (
                <div key={item.id} className="flex items-center gap-3 rounded-lg p-2 hover:bg-zinc-800/50 transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${TIER_COLORS[tier]}`}>
                        {item.platform_slug}
                      </Badge>
                      <span className="text-sm font-medium text-zinc-200 truncate">
                        {item.task_title}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs">
                      <span className="text-zinc-400">
                        {item.currency} {item.estimated_pay?.toFixed(2)}
                      </span>
                      <span className={expired ? "font-medium text-red-500" : "text-amber-500"}>
                        {expired ? "EXPIRED" : `expires ${formatDistanceToNow(new Date(item.deadline!), { addSuffix: true })}`}
                      </span>
                    </div>
                  </div>
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-zinc-300 transition-colors">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
