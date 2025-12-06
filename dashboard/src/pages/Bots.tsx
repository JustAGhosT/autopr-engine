import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { botsApi, BotExclusion, BotComment } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatRelativeTime } from '../services/utils'

export function BotsPage() {
  const [newBot, setNewBot] = useState('')
  const [reason, setReason] = useState('')
  const queryClient = useQueryClient()

  const { data: exclusions, isLoading: exclusionsLoading } = useQuery({
    queryKey: ['bots', 'exclusions'],
    queryFn: async () => {
      const response = await botsApi.listExclusions()
      return response.data.data
    },
  })

  const { data: comments, isLoading: commentsLoading } = useQuery({
    queryKey: ['bots', 'comments'],
    queryFn: async () => {
      const response = await botsApi.listComments(1, true)
      return response.data.data
    },
  })

  const addMutation = useMutation({
    mutationFn: ({ username, reason }: { username: string; reason?: string }) =>
      botsApi.addExclusion(username, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bots', 'exclusions'] })
      setNewBot('')
      setReason('')
    },
  })

  const removeMutation = useMutation({
    mutationFn: (username: string) => botsApi.removeExclusion(username),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['bots', 'exclusions'] }),
  })

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault()
    if (newBot.trim()) {
      addMutation.mutate({ username: newBot.trim(), reason: reason.trim() || undefined })
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Bot Exclusions</h1>

      {/* Add Exclusion Form */}
      <Card>
        <CardHeader>
          <CardTitle>Add Bot to Exclusion List</CardTitle>
          <CardDescription>
            Exclude bots from triggering AutoPR comment responses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="flex flex-col space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0">
            <input
              type="text"
              value={newBot}
              onChange={(e) => setNewBot(e.target.value)}
              placeholder="Bot username (e.g., coderabbitai[bot])"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Reason (optional)"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <Button type="submit" isLoading={addMutation.isPending}>
              Add Exclusion
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Current Exclusions */}
      <Card>
        <CardHeader>
          <CardTitle>Current Exclusions</CardTitle>
        </CardHeader>
        <CardContent>
          {exclusionsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : exclusions && exclusions.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {exclusions.map((exclusion: BotExclusion) => (
                <li key={exclusion.id} className="flex items-center justify-between py-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">🤖</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{exclusion.username}</p>
                      {exclusion.reason && (
                        <p className="text-xs text-gray-500">{exclusion.reason}</p>
                      )}
                    </div>
                    <Badge variant={exclusion.source === 'builtin' ? 'info' : 'default'}>
                      {exclusion.source}
                    </Badge>
                  </div>
                  {exclusion.source === 'user' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeMutation.mutate(exclusion.username)}
                      isLoading={removeMutation.isPending}
                    >
                      Remove
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-center text-gray-500 py-8">No exclusions configured</p>
          )}
        </CardContent>
      </Card>

      {/* Recent Bot Comments */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Filtered Comments</CardTitle>
          <CardDescription>Bot comments that were excluded from processing</CardDescription>
        </CardHeader>
        <CardContent>
          {commentsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : comments && comments.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {comments.map((comment: BotComment) => (
                <li key={comment.id} className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">🤖</span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{comment.bot_username}</p>
                        <p className="text-xs text-gray-500">
                          PR #{comment.pr_number} • {formatRelativeTime(comment.created_at)}
                        </p>
                      </div>
                    </div>
                    {comment.exclusion_reason && (
                      <Badge variant="info">{comment.exclusion_reason}</Badge>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-gray-600 line-clamp-2">{comment.body}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-center text-gray-500 py-8">No filtered comments</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
