"use client"

import { useState } from "react"
import type { AgentLog } from "@/lib/supabase/types"
import { mockAgentLogs } from "@/lib/mock-data"

export function useAgentLogs() {
  const [logs] = useState<AgentLog[]>(mockAgentLogs)
  const [loading] = useState(false)

  const recent = [...logs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 15)

  return { logs, recent, loading }
}
