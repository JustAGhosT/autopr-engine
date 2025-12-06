import { useQuery } from '@tanstack/react-query'
import { dashboardApi, DashboardStats, ActivityItem } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatRelativeTime } from '../services/utils'

export function DashboardPage() {
  const { data: statsData, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const response = await dashboardApi.getStats()
      return response.data.data
    },
  })

  const { data: activityData, isLoading: activityLoading } = useQuery({
    queryKey: ['dashboard', 'activity'],
    queryFn: async () => {
      const response = await dashboardApi.getActivity(10)
      return response.data.data
    },
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="PRs Processed"
          value={statsData?.total_prs_processed}
          isLoading={statsLoading}
        />
        <StatCard
          title="Issues Created"
          value={statsData?.issues_created}
          isLoading={statsLoading}
        />
        <StatCard
          title="Bots Filtered"
          value={statsData?.bots_filtered}
          isLoading={statsLoading}
        />
        <StatCard
          title="Active Repos"
          value={statsData?.active_repos}
          isLoading={statsLoading}
        />
      </div>

      {/* Health Status */}
      {statsData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              System Health
              <HealthBadge status={statsData.health_status} />
            </CardTitle>
          </CardHeader>
        </Card>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {activityLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : activityData && activityData.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {activityData.map((item: ActivityItem) => (
                <ActivityRow key={item.id} item={item} />
              ))}
            </ul>
          ) : (
            <p className="text-center text-gray-500 py-8">No recent activity</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({ title, value, isLoading }: { title: string; value?: number; isLoading: boolean }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {isLoading ? (
          <LoadingSpinner size="sm" className="mt-2" />
        ) : (
          <p className="mt-2 text-3xl font-bold text-gray-900">{value?.toLocaleString() ?? 0}</p>
        )}
      </CardContent>
    </Card>
  )
}

function HealthBadge({ status }: { status: DashboardStats['health_status'] }) {
  const variants = {
    healthy: 'success',
    degraded: 'warning',
    unhealthy: 'danger',
  } as const

  return (
    <Badge variant={variants[status]}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  )
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const typeIcons = {
    pr_analyzed: '📝',
    issue_created: '🎫',
    bot_filtered: '🤖',
    workflow_run: '⚡',
  }

  return (
    <li className="flex items-center justify-between py-3">
      <div className="flex items-center space-x-3">
        <span className="text-xl">{typeIcons[item.type]}</span>
        <div>
          <p className="text-sm font-medium text-gray-900">{item.message}</p>
          <p className="text-xs text-gray-500">{item.repo}</p>
        </div>
      </div>
      <span className="text-xs text-gray-500">{formatRelativeTime(item.created_at)}</span>
    </li>
  )
}
