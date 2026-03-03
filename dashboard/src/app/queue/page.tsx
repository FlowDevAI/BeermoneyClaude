import { Badge } from "@/components/ui/badge"
import { ClipboardList } from "lucide-react"
import { QueueList } from "@/components/queue/QueueList"
import { mockQueueItems } from "@/lib/mock-data"

const pendingCount = mockQueueItems.filter((q) => q.status === "pending").length

export default function QueuePage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <ClipboardList className="h-6 w-6 text-zinc-400" />
        <h1 className="text-2xl font-semibold text-zinc-50">Human Queue</h1>
        {pendingCount > 0 && (
          <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/30">
            {pendingCount} pending
          </Badge>
        )}
      </div>

      <QueueList />
    </div>
  )
}
