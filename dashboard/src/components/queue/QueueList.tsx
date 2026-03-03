"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { PartyPopper } from "lucide-react"
import type { HumanQueueItem } from "@/lib/supabase/types"
import { mockQueueItems } from "@/lib/mock-data"
import { QueueCard } from "./QueueCard"
import { CompleteTaskDialog } from "./CompleteTaskDialog"

const URGENCY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }

function sortQueue(items: HumanQueueItem[]) {
  return [...items].sort((a, b) => {
    const urgDiff = (URGENCY_ORDER[a.urgency] ?? 9) - (URGENCY_ORDER[b.urgency] ?? 9)
    if (urgDiff !== 0) return urgDiff
    if (a.deadline && b.deadline) return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
    if (a.deadline) return -1
    if (b.deadline) return 1
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })
}

export function QueueList() {
  const [items, setItems] = useState<HumanQueueItem[]>(mockQueueItems)
  const [completingItem, setCompletingItem] = useState<HumanQueueItem | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [platformFilter, setPlatformFilter] = useState<string>("all")

  const pending = sortQueue(items.filter((i) => i.status === "pending"))
  const done = items.filter((i) => i.status === "done")
  const skipped = items.filter((i) => i.status === "skipped")
  const expired = items.filter((i) => i.status === "expired")

  const platforms = Array.from(new Set(items.map((i) => i.platform_slug)))

  function filterByPlatform(list: HumanQueueItem[]) {
    if (platformFilter === "all") return list
    return list.filter((i) => i.platform_slug === platformFilter)
  }

  function handleComplete(item: HumanQueueItem) {
    setCompletingItem(item)
    setDialogOpen(true)
  }

  function handleSkip(item: HumanQueueItem) {
    setItems((prev) =>
      prev.map((i) => (i.id === item.id ? { ...i, status: "skipped" as const } : i))
    )
  }

  function handleSaveComplete(data: { earnings: number; currency: string; minutes: number }) {
    if (!completingItem) return
    setItems((prev) =>
      prev.map((i) =>
        i.id === completingItem.id
          ? {
              ...i,
              status: "done" as const,
              actual_earnings: data.earnings,
              actual_minutes: data.minutes,
              completed_at: new Date().toISOString(),
            }
          : i
      )
    )
    setDialogOpen(false)
    setCompletingItem(null)
  }

  function renderList(list: HumanQueueItem[]) {
    const filtered = filterByPlatform(list)
    if (filtered.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
          <PartyPopper className="h-10 w-10 mb-3 text-zinc-600" />
          <p className="text-sm">No tasks here!</p>
          <p className="text-xs mt-1">Check back after the next agent run.</p>
        </div>
      )
    }
    return (
      <div className="flex flex-col gap-3">
        {filtered.map((item) => (
          <QueueCard key={item.id} item={item} onComplete={handleComplete} onSkip={handleSkip} />
        ))}
      </div>
    )
  }

  return (
    <>
      {/* Platform filter */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <Badge
          variant="outline"
          className={`cursor-pointer text-xs transition-colors ${platformFilter === "all" ? "bg-zinc-800 text-zinc-100 border-zinc-600" : "border-zinc-700 text-zinc-500 hover:text-zinc-300"}`}
          onClick={() => setPlatformFilter("all")}
        >
          All
        </Badge>
        {platforms.map((p) => (
          <Badge
            key={p}
            variant="outline"
            className={`cursor-pointer text-xs transition-colors ${platformFilter === p ? "bg-zinc-800 text-zinc-100 border-zinc-600" : "border-zinc-700 text-zinc-500 hover:text-zinc-300"}`}
            onClick={() => setPlatformFilter(p)}
          >
            {p}
          </Badge>
        ))}
      </div>

      <Tabs defaultValue="pending">
        <TabsList className="bg-zinc-800/50 border border-zinc-800">
          <TabsTrigger value="pending" className="data-[state=active]:bg-zinc-700 text-zinc-400 data-[state=active]:text-zinc-100">
            Pending <Badge variant="secondary" className="ml-1.5 bg-emerald-500/10 text-emerald-500 text-xs">{pending.length}</Badge>
          </TabsTrigger>
          <TabsTrigger value="done" className="data-[state=active]:bg-zinc-700 text-zinc-400 data-[state=active]:text-zinc-100">
            Done <Badge variant="secondary" className="ml-1.5 bg-zinc-600/30 text-zinc-400 text-xs">{done.length}</Badge>
          </TabsTrigger>
          <TabsTrigger value="skipped" className="data-[state=active]:bg-zinc-700 text-zinc-400 data-[state=active]:text-zinc-100">
            Skipped <Badge variant="secondary" className="ml-1.5 bg-zinc-600/30 text-zinc-400 text-xs">{skipped.length}</Badge>
          </TabsTrigger>
          <TabsTrigger value="expired" className="data-[state=active]:bg-zinc-700 text-zinc-400 data-[state=active]:text-zinc-100">
            Expired <Badge variant="secondary" className="ml-1.5 bg-red-500/10 text-red-400 text-xs">{expired.length}</Badge>
          </TabsTrigger>
        </TabsList>

        <div className="mt-4">
          <TabsContent value="pending">{renderList(pending)}</TabsContent>
          <TabsContent value="done">{renderList(done)}</TabsContent>
          <TabsContent value="skipped">{renderList(skipped)}</TabsContent>
          <TabsContent value="expired">{renderList(expired)}</TabsContent>
        </div>
      </Tabs>

      <CompleteTaskDialog
        item={completingItem}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSave={handleSaveComplete}
      />
    </>
  )
}
