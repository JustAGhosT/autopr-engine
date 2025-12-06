import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../services/api'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import { useToast } from '../components/Toast'
import { formatDateTime } from '../services/utils'

interface ApiKey {
  id: string
  name: string
  prefix: string
  scopes: string[]
  created_at: string
  last_used_at: string | null
}

interface UserSettings {
  notifications_email: boolean
  notifications_pr_activity: boolean
  notifications_workflow_failures: boolean
  default_quality_mode: string
  auto_create_issues: boolean
}

export function SettingsPage() {
  const [newKeyName, setNewKeyName] = useState('')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [revokingKeyId, setRevokingKeyId] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  // Fetch user settings
  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const response = await settingsApi.get()
      return response.data.data as UserSettings
    },
  })

  // Fetch API keys
  const { data: apiKeys, isLoading: keysLoading } = useQuery({
    queryKey: ['settings', 'api-keys'],
    queryFn: async () => {
      const response = await settingsApi.listApiKeys()
      return response.data.data as ApiKey[]
    },
  })

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (data: Partial<UserSettings>) => settingsApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      addToast('Settings updated', 'success')
    },
    onError: () => addToast('Failed to update settings', 'error'),
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => settingsApi.createApiKey(name, ['read', 'write']),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'api-keys'] })
      setNewKeyName('')
      setCreatedKey(response.data.data.key)
      addToast('API key created', 'success')
    },
    onError: () => addToast('Failed to create API key', 'error'),
  })

  const revokeMutation = useMutation({
    mutationFn: (id: string) => {
      setRevokingKeyId(id)
      return settingsApi.revokeApiKey(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'api-keys'] })
      setRevokingKeyId(null)
      addToast('API key revoked', 'success')
    },
    onError: () => {
      setRevokingKeyId(null)
      addToast('Failed to revoke API key', 'error')
    },
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (newKeyName.trim()) {
      createMutation.mutate(newKeyName.trim())
    }
  }

  const handleCopyKey = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey)
      addToast('API key copied to clipboard', 'success')
    }
  }

  const handleSettingChange = (key: keyof UserSettings, value: boolean) => {
    updateSettingsMutation.mutate({ [key]: value })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* API Keys Section */}
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Manage API keys for programmatic access to AutoPR
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Create New Key Form */}
          <form onSubmit={handleCreate} className="flex space-x-4 mb-6">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g., CI/CD Pipeline)"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Key
            </Button>
          </form>

          {/* Newly Created Key Display */}
          {createdKey && (
            <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
              <p className="text-sm font-medium text-green-800 mb-2">
                Your new API key (copy it now, it won't be shown again):
              </p>
              <code className="block bg-white rounded border border-green-200 p-2 text-sm font-mono">
                {createdKey}
              </code>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2"
                onClick={handleCopyKey}
              >
                Copy to Clipboard
              </Button>
            </div>
          )}

          {/* Existing Keys List */}
          {keysLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : apiKeys && apiKeys.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {apiKeys.map((key) => (
                <li key={key.id} className="flex items-center justify-between py-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{key.name}</p>
                    <p className="text-xs text-gray-500">
                      {key.prefix}••••••••  •  Created {formatDateTime(key.created_at)}
                      {key.last_used_at && ` • Last used ${formatDateTime(key.last_used_at)}`}
                    </p>
                  </div>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => revokeMutation.mutate(key.id)}
                    isLoading={revokingKeyId === key.id}
                    disabled={revokeMutation.isPending}
                  >
                    Revoke
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-center text-gray-500 py-8">No API keys created</p>
          )}
        </CardContent>
      </Card>

      {/* Notifications Section */}
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Configure how you receive notifications</CardDescription>
        </CardHeader>
        <CardContent>
          {settingsLoading ? (
            <div className="flex justify-center py-4">
              <LoadingSpinner size="sm" />
            </div>
          ) : (
            <div className="space-y-4">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings?.notifications_pr_activity ?? false}
                  onChange={(e) => handleSettingChange('notifications_pr_activity', e.target.checked)}
                  disabled={updateSettingsMutation.isPending}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Email notifications for PR activity</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings?.notifications_workflow_failures ?? false}
                  onChange={(e) => handleSettingChange('notifications_workflow_failures', e.target.checked)}
                  disabled={updateSettingsMutation.isPending}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Email notifications for workflow failures</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings?.notifications_email ?? false}
                  onChange={(e) => handleSettingChange('notifications_email', e.target.checked)}
                  disabled={updateSettingsMutation.isPending}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Email digest notifications</span>
              </label>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
