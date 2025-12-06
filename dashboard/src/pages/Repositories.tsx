import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reposApi, Repository } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { useToast } from '../components/Toast'
import { formatRelativeTime } from '../services/utils'

// Cooldown period for sync button (30 seconds)
const SYNC_COOLDOWN_MS = 30000

export function RepositoriesPage() {
  const [page, setPage] = useState(1)
  const [syncCooldown, setSyncCooldown] = useState(0)
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  // Countdown timer for sync cooldown
  useEffect(() => {
    if (syncCooldown <= 0) return
    const timer = setInterval(() => {
      setSyncCooldown((prev) => Math.max(0, prev - 1000))
    }, 1000)
    return () => clearInterval(timer)
  }, [syncCooldown])

  const { data, isLoading } = useQuery({
    queryKey: ['repos', page],
    queryFn: async () => {
      const response = await reposApi.list(page)
      return response.data
    },
  })

  const enableMutation = useMutation({
    mutationFn: ({ owner, name }: { owner: string; name: string }) => reposApi.enable(owner, name),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['repos'] })
      addToast(`Enabled ${variables.owner}/${variables.name}`, 'success')
    },
    onError: () => addToast('Failed to enable repository', 'error'),
  })

  const disableMutation = useMutation({
    mutationFn: ({ owner, name }: { owner: string; name: string }) => reposApi.disable(owner, name),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['repos'] })
      addToast(`Disabled ${variables.owner}/${variables.name}`, 'success')
    },
    onError: () => addToast('Failed to disable repository', 'error'),
  })

  const syncMutation = useMutation({
    mutationFn: () => reposApi.sync(),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['repos'] })
      setSyncCooldown(SYNC_COOLDOWN_MS)
      const synced = response.data?.synced ?? 0
      addToast(`Synced ${synced} repositories from GitHub`, 'success')
    },
    onError: () => addToast('Failed to sync repositories', 'error'),
  })

  const handleSync = useCallback(() => {
    if (syncCooldown > 0 || syncMutation.isPending) return
    syncMutation.mutate()
  }, [syncCooldown, syncMutation])

  const toggleRepo = (repo: Repository) => {
    if (repo.enabled) {
      disableMutation.mutate({ owner: repo.owner, name: repo.name })
    } else {
      enableMutation.mutate({ owner: repo.owner, name: repo.name })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
        <Button
          variant="secondary"
          onClick={handleSync}
          isLoading={syncMutation.isPending}
          disabled={syncCooldown > 0}
        >
          {syncCooldown > 0
            ? `Sync (${Math.ceil(syncCooldown / 1000)}s)`
            : 'Sync from GitHub'}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Repositories</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : data?.data && data.data.length > 0 ? (
            <>
              <ul className="divide-y divide-gray-200">
                {data.data.map((repo: Repository) => (
                  <li key={repo.id} className="flex items-center justify-between py-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <p className="text-sm font-medium text-gray-900">{repo.full_name}</p>
                        <Badge variant={repo.enabled ? 'success' : 'default'}>
                          {repo.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        Updated {formatRelativeTime(repo.updated_at)}
                      </p>
                    </div>
                    <Button
                      variant={repo.enabled ? 'outline' : 'primary'}
                      size="sm"
                      onClick={() => toggleRepo(repo)}
                      isLoading={enableMutation.isPending || disableMutation.isPending}
                    >
                      {repo.enabled ? 'Disable' : 'Enable'}
                    </Button>
                  </li>
                ))}
              </ul>

              {/* Pagination */}
              {data.meta && data.meta.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between border-t border-gray-200 pt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-500">
                    Page {page} of {data.meta.total_pages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= data.meta.total_pages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          ) : (
            <p className="text-center text-gray-500 py-8">No repositories found</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
