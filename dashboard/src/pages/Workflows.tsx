import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workflowsApi, Workflow } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { formatRelativeTime } from '../services/utils'

export function WorkflowsPage() {
  const queryClient = useQueryClient()

  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await workflowsApi.list()
      return response.data.data
    },
  })

  const triggerMutation = useMutation({
    mutationFn: (id: string) => workflowsApi.trigger(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      workflowsApi.update(id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workflows'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : workflows && workflows.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2">
          {workflows.map((workflow: Workflow) => (
            <Card key={workflow.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{workflow.name}</CardTitle>
                  <Badge variant={workflow.enabled ? 'success' : 'default'}>
                    {workflow.enabled ? 'Active' : 'Disabled'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-4">{workflow.description}</p>

                <div className="flex flex-wrap gap-2 mb-4">
                  {workflow.triggers.map((trigger) => (
                    <Badge key={trigger} variant="info">
                      {trigger}
                    </Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <span>Runs: {workflow.run_count}</span>
                  {workflow.last_run_at && (
                    <span>Last run: {formatRelativeTime(workflow.last_run_at)}</span>
                  )}
                </div>

                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleMutation.mutate({ id: workflow.id, enabled: !workflow.enabled })}
                    isLoading={toggleMutation.isPending}
                  >
                    {workflow.enabled ? 'Disable' : 'Enable'}
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => triggerMutation.mutate(workflow.id)}
                    isLoading={triggerMutation.isPending}
                    disabled={!workflow.enabled}
                  >
                    Run Now
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center text-gray-500">
            No workflows configured
          </CardContent>
        </Card>
      )}
    </div>
  )
}
