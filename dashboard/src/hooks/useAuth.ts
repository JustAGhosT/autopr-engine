import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, User } from '../services/api'

export function useAuth() {
  const queryClient = useQueryClient()

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await authApi.getMe()
      return response.data.data
    },
    retry: false,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.clear()
      window.location.href = '/login'
    },
  })

  return {
    user: user as User | undefined,
    isLoading,
    isAuthenticated: !!user && !error,
    error,
    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,
  }
}

export function useRequireAuth() {
  const auth = useAuth()

  if (!auth.isLoading && !auth.isAuthenticated) {
    window.location.href = '/login'
  }

  return auth
}
