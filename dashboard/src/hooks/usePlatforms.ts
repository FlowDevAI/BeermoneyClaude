"use client"

import { useState } from "react"
import type { Platform } from "@/lib/supabase/types"
import { mockPlatforms } from "@/lib/mock-data"

export function usePlatforms() {
  const [platforms] = useState<Platform[]>(mockPlatforms)
  const [loading] = useState(false)

  const active = platforms.filter((p) => p.active)

  return { platforms, active, loading }
}
