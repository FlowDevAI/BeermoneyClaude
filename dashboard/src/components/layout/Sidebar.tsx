"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Home,
  ClipboardList,
  DollarSign,
  Plug,
  BarChart3,
  Bot,
  Settings,
  Moon,
} from "lucide-react"
import { mockQueueItems } from "@/lib/mock-data"

const pendingCount = mockQueueItems.filter(q => q.status === "pending").length

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/queue", label: "Queue", icon: ClipboardList, badge: pendingCount },
  { href: "/earnings", label: "Earnings", icon: DollarSign },
  { href: "/platforms", label: "Platforms", icon: Plug },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/agent", label: "Agent", icon: Bot },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex h-screen w-64 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex items-center gap-2 px-6 py-5">
        <Bot className="h-6 w-6 text-emerald-500" />
        <span className="text-lg font-semibold text-zinc-50">BeermoneyClaude</span>
      </div>

      <Separator className="bg-zinc-800" />

      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-zinc-800 text-zinc-50"
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
                {item.badge !== undefined && item.badge > 0 && (
                  <Badge variant="secondary" className="ml-auto bg-emerald-500/10 text-emerald-500 text-xs">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            )
          })}
        </nav>

        <Separator className="my-4 bg-zinc-800" />

        <Link
          href="/settings"
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
            pathname === "/settings"
              ? "bg-zinc-800 text-zinc-50"
              : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
          )}
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
      </ScrollArea>

      <Separator className="bg-zinc-800" />

      <div className="flex items-center gap-2 px-6 py-4 text-sm text-zinc-500">
        <Moon className="h-4 w-4 text-emerald-500" />
        <span>Night Mode</span>
        <span className="ml-auto h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
      </div>
    </aside>
  )
}
