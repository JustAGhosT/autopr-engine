import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useRequireAuth } from '../../hooks/useAuth'
import { LoadingPage } from '../ui/LoadingSpinner'

export function Layout() {
  const { isLoading, isAuthenticated } = useRequireAuth()

  if (isLoading) {
    return <LoadingPage />
  }

  if (!isAuthenticated) {
    return null // Will redirect to login
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
