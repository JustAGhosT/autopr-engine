import { useAuth } from '../../hooks/useAuth'
import { Button } from '../ui/Button'

export function Header() {
  const { user, logout, isLoggingOut } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="flex items-center">
        <h1 className="text-lg font-semibold text-gray-900">Dashboard</h1>
      </div>
      <div className="flex items-center space-x-4">
        {user && (
          <>
            <div className="flex items-center space-x-3">
              {user.avatar_url && (
                <img
                  src={user.avatar_url}
                  alt={user.github_login}
                  className="h-8 w-8 rounded-full"
                />
              )}
              <span className="text-sm font-medium text-gray-700">{user.github_login}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => logout()}
              isLoading={isLoggingOut}
            >
              Sign out
            </Button>
          </>
        )}
      </div>
    </header>
  )
}
