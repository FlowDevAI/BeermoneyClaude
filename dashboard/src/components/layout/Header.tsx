"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Menu,
  Home,
  ClipboardList,
  DollarSign,
  Plug,
  BarChart3,
  Bot,
  Settings,
  Moon,
} from "lucide-react"
import { mockQueueItems, mockDailyStats } from "@/lib/mock-data"

const pendingCount = mockQueueItems.filter(q => q.status === "pending").length
const todayEarnings = mockDailyStats[mockDailyStats.length - 1]?.total_earned_eur ?? 0

const navItems = [
  { href: "/", label: "Home", icon: Home },
  { href: "/queue", label: "Queue", icon: ClipboardList, badge: pendingCount },
  { href: "/earnings", label: "Earnings", icon: DollarSign },
  { href: "/platforms", label: "Platforms", icon: Plug },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/agent", label: "Agent", icon: Bot },
]

export function Header() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b border-zinc-800 bg-zinc-950/80 px-4 backdrop-blur-sm md:px-6">
      {/* Mobile menu */}
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden text-zinc-400">
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 border-zinc-800 bg-zinc-950 p-0">
          <div className="flex items-center gap-2 px-6 py-5">
            <Bot className="h-6 w-6 text-emerald-500" />
            <span className="text-lg font-semibold text-zinc-50">BeermoneyClaude</span>
          </div>
          <Separator className="bg-zinc-800" />
          <nav className="flex flex-col gap-1 px-3 py-4">
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
            <Separator className="my-2 bg-zinc-800" />
            <Link href="/settings" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200">
              <Settings className="h-4 w-4" /> Settings
            </Link>
          </nav>
          <div className="absolute bottom-4 left-6 flex items-center gap-2 text-sm text-zinc-500">
            <Moon className="h-4 w-4 text-emerald-500" />
            Night Mode
            <span className="ml-2 h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        </SheetContent>
      </Sheet>

      {/* Desktop info */}
      <div className="flex flex-1 items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="hidden sm:inline">Agent running</span>
        </div>
        <div className="ml-auto flex items-center gap-4 text-sm">
          <span className="text-zinc-400">
            Today: <span className="font-medium text-emerald-500">{todayEarnings.toFixed(2)}&euro;</span>
          </span>
          <Link href="/queue" className="text-zinc-400 hover:text-zinc-200 transition-colors">
            Queue: <span className="font-medium text-zinc-200">{pendingCount} pending</span>
          </Link>
        </div>
      </div>
    </header>
  )
}
