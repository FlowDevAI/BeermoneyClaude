"use client"

import { useState, useCallback } from "react"
import type { HumanQueueItem } from "@/lib/supabase/types"
import { isSupabaseConfigured } from "@/lib/supabase/client"
import { mockQueueItems } from "@/lib/mock-data"

export function useQueue() {
  const [items, setItems] = useState<HumanQueueItem[]>(mockQueueItems)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!isSupabaseConfigured) return
    setLoading(true)
    // TODO: Fetch from Supabase
    setLoading(false)
  }, [])

  const markDone = useCallback((id: string, earnings: number, minutes: number) => {
    setItems((prev) =>
      prev.map((i) =>
        i.id === id
          ? { ...i, status: "done" as const, actual_earnings: earnings, actual_minutes: minutes, completed_at: new Date().toISOString() }
          : i
      )
    )
  }, [])

  const markSkipped = useCallback((id: string) => {
    setItems((prev) =>
      prev.map((i) => (i.id === id ? { ...i, status: "skipped" as const } : i))
    )
  }, [])

  const pending = items.filter((i) => i.status === "pending")
  const done = items.filter((i) => i.status === "done")
  const skipped = items.filter((i) => i.status === "skipped")

  return { items, pending, done, skipped, loading, refresh, markDone, markSkipped }
}
