import { StatsCards } from "@/components/dashboard/StatsCards"
import { RecentActivity } from "@/components/dashboard/RecentActivity"
import { EarningsChart } from "@/components/dashboard/EarningsChart"
import { UpcomingDeadlines } from "@/components/dashboard/UpcomingDeadlines"

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-zinc-50">Dashboard</h1>

      <StatsCards />

      <div className="grid gap-6 lg:grid-cols-2">
        <RecentActivity />
        <EarningsChart />
      </div>

      <UpcomingDeadlines />
    </div>
  )
}
