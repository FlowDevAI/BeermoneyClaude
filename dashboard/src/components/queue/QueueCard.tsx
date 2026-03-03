"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Check, SkipForward } from "lucide-react"
import { formatDistanceToNow, isPast } from "date-fns"
import type { HumanQueueItem } from "@/lib/supabase/types"
import { URGENCY_BORDER, URGENCY_COLORS, TIER_COLORS, REASON_LABELS } from "@/lib/constants"
import { mockPlatforms } from "@/lib/mock-data"

function getPlatformTier(slug: string) {
  return mockPlatforms.find((p) => p.slug === slug)?.tier ?? 4
}

interface QueueCardProps {
  item: HumanQueueItem
  onComplete: (item: HumanQueueItem) => void
  onSkip: (item: HumanQueueItem) => void
}

export function QueueCard({ item, onComplete, onSkip }: QueueCardProps) {
  const tier = getPlatformTier(item.platform_slug)
  const expired = item.deadline ? isPast(new Date(item.deadline)) : false

  return (
    <Card className={`bg-zinc-900 border-zinc-800 border-l-4 ${URGENCY_BORDER[item.urgency]} transition-all hover:bg-zinc-900/80`}>
      <CardContent className="p-4">
        <div className="flex flex-col gap-3">
          {/* Top row: platform badge + urgency + deadline */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className={`text-xs ${TIER_COLORS[tier]}`}>
              {item.platform_slug}
            </Badge>
            <Badge variant="outline" className={`text-xs ${URGENCY_COLORS[item.urgency]} ${item.urgency === "critical" ? "animate-pulse" : ""}`}>
              {item.urgency}
            </Badge>
            <Badge variant="outline" className="text-xs border-zinc-700 text-zinc-400">
              {REASON_LABELS[item.reason] ?? item.reason}
            </Badge>
            {item.deadline && (
              <span className={`ml-auto text-xs ${expired ? "font-medium text-red-500" : "text-zinc-500"}`}>
                {expired ? "EXPIRED" : `${formatDistanceToNow(new Date(item.deadline))} left`}
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="text-base font-medium text-zinc-100">{item.task_title}</h3>

          {/* Pay */}
          {item.estimated_pay != null && (
            <p className="text-lg font-semibold text-emerald-500">
              {item.currency} {item.estimated_pay.toFixed(2)}
            </p>
          )}

          {/* Instructions */}
          {item.instructions && (
            <p className="text-sm text-zinc-400 leading-relaxed">{item.instructions}</p>
          )}

          {/* Done info */}
          {item.status === "done" && item.actual_earnings != null && (
            <div className="flex items-center gap-3 text-sm text-zinc-400">
              <span>Earned: <span className="text-emerald-500 font-medium">{item.currency} {item.actual_earnings.toFixed(2)}</span></span>
              {item.actual_minutes != null && <span>Time: {item.actual_minutes}min</span>}
            </div>
          )}

          {/* Actions */}
          {item.status === "pending" && (
            <div className="flex items-center gap-2 pt-1">
              {item.url && (
                <Button variant="outline" size="sm" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800" asChild>
                  <a href={item.url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                    Open
                  </a>
                </Button>
              )}
              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white" onClick={() => onComplete(item)}>
                <Check className="mr-1.5 h-3.5 w-3.5" />
                Completed
              </Button>
              <Button variant="ghost" size="sm" className="text-zinc-500 hover:text-zinc-300" onClick={() => onSkip(item)}>
                <SkipForward className="mr-1.5 h-3.5 w-3.5" />
                Skip
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
