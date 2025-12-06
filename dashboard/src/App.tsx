import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Layout } from '@/components/layout/Layout'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

// Pages
import { DashboardPage } from '@/pages/Dashboard'
import { RepositoriesPage } from '@/pages/Repositories'
import { BotsPage } from '@/pages/Bots'
import { WorkflowsPage } from '@/pages/Workflows'
import { SettingsPage } from '@/pages/Settings'
import { LoginPage } from '@/pages/Login'
import { NotFoundPage } from '@/pages/NotFound'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="repos" element={<RepositoriesPage />} />
        <Route path="bots" element={<BotsPage />} />
        <Route path="workflows" element={<WorkflowsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
