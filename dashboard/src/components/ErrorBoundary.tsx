import { Component, ErrorInfo, ReactNode } from 'react'
import { Button } from './ui/Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
          <div className="max-w-md text-center">
            <div className="mb-4 text-6xl">:(</div>
            <h1 className="mb-2 text-2xl font-bold text-gray-900">Something went wrong</h1>
            <p className="mb-6 text-gray-600">
              An unexpected error occurred. Please try again.
            </p>
            {this.state.error && (
              <pre className="mb-6 overflow-auto rounded-lg bg-gray-100 p-4 text-left text-xs text-red-600">
                {this.state.error.message}
              </pre>
            )}
            <div className="space-x-4">
              <Button onClick={this.handleReset}>Try Again</Button>
              <Button variant="outline" onClick={() => window.location.href = '/'}>
                Go Home
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
