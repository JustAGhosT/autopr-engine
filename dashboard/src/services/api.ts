import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if not authenticated
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API Types
export interface User {
  id: string
  github_login: string
  email: string | null
  avatar_url: string | null
}

export interface Repository {
  id: string
  github_id: number
  owner: string
  name: string
  full_name: string
  enabled: boolean
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface BotExclusion {
  id: string
  username: string
  reason: string | null
  source: 'config' | 'user' | 'builtin'
  created_at: string
}

export interface BotComment {
  id: string
  repo_id: number
  pr_number: number
  comment_id: number
  bot_username: string
  body: string
  was_excluded: boolean
  exclusion_reason: string | null
  created_at: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  enabled: boolean
  triggers: string[]
  last_run_at: string | null
  run_count: number
}

export interface DashboardStats {
  total_prs_processed: number
  issues_created: number
  bots_filtered: number
  active_repos: number
  health_status: 'healthy' | 'degraded' | 'unhealthy'
}

export interface ActivityItem {
  id: string
  type: 'pr_analyzed' | 'issue_created' | 'bot_filtered' | 'workflow_run'
  message: string
  repo: string
  created_at: string
}

// Pagination
export interface PaginationMeta {
  page: number
  per_page: number
  total: number
  total_pages: number
}

export interface ApiResponse<T> {
  data: T
  meta?: PaginationMeta
}

// API Functions
export const authApi = {
  getMe: () => api.get<ApiResponse<User>>('/auth/me'),
  logout: () => api.post('/auth/logout'),
}

export const reposApi = {
  list: (page = 1) => api.get<ApiResponse<Repository[]>>(`/repos?page=${page}`),
  get: (owner: string, name: string) => api.get<ApiResponse<Repository>>(`/repos/${owner}/${name}`),
  update: (owner: string, name: string, data: Partial<Repository>) =>
    api.patch<ApiResponse<Repository>>(`/repos/${owner}/${name}`, data),
  enable: (owner: string, name: string) => api.post(`/repos/${owner}/${name}/enable`),
  disable: (owner: string, name: string) => api.post(`/repos/${owner}/${name}/disable`),
}

export const botsApi = {
  listExclusions: () => api.get<ApiResponse<BotExclusion[]>>('/bots/exclusions'),
  addExclusion: (username: string, reason?: string) =>
    api.post<ApiResponse<BotExclusion>>('/bots/exclusions', { username, reason }),
  removeExclusion: (username: string) => api.delete(`/bots/exclusions/${username}`),
  listComments: (page = 1, excluded?: boolean) =>
    api.get<ApiResponse<BotComment[]>>(`/bots/comments?page=${page}${excluded !== undefined ? `&excluded=${excluded}` : ''}`),
  getAnalytics: () => api.get<ApiResponse<Record<string, number>>>('/bots/analytics'),
}

export const workflowsApi = {
  list: () => api.get<ApiResponse<Workflow[]>>('/workflows'),
  get: (id: string) => api.get<ApiResponse<Workflow>>(`/workflows/${id}`),
  update: (id: string, data: Partial<Workflow>) => api.patch<ApiResponse<Workflow>>(`/workflows/${id}`, data),
  trigger: (id: string) => api.post(`/workflows/${id}/trigger`),
  getExecutions: (id: string) => api.get(`/workflows/${id}/executions`),
}

export const dashboardApi = {
  getStats: () => api.get<ApiResponse<DashboardStats>>('/dashboard/stats'),
  getActivity: (limit = 20) => api.get<ApiResponse<ActivityItem[]>>(`/activity?limit=${limit}`),
}

export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: Record<string, unknown>) => api.patch('/settings', data),
  listApiKeys: () => api.get('/settings/api-keys'),
  createApiKey: (name: string, scopes: string[]) =>
    api.post('/settings/api-keys', { name, scopes }),
  revokeApiKey: (id: string) => api.delete(`/settings/api-keys/${id}`),
}
