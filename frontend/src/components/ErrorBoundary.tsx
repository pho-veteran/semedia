import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from './ui/Button'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

/**
 * Error Boundary component that catches unhandled React errors
 * and displays a user-friendly fallback UI.
 * 
 * **Validates: Requirements 24.1, 24.2, 24.3, 24.4, 24.5, 24.6**
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(_error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error and errorInfo to console (Requirement 24.5)
    // Never expose stack traces to users (Requirement 24.6)
    console.error('Error caught by ErrorBoundary:', error, errorInfo)
  }

  handleReload = (): void => {
    // Reload the page (Requirement 24.4)
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // Display fallback UI when error is caught (Requirement 24.1, 24.2, 24.3)
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
          <div className="max-w-md w-full text-center space-y-6">
            {/* AlertTriangle icon (Requirement 24.2) */}
            <div className="flex justify-center">
              <div className="rounded-full bg-destructive/10 p-4">
                <AlertTriangle className="h-12 w-12 text-destructive" aria-hidden="true" />
              </div>
            </div>

            {/* Error title and description (Requirement 24.3) */}
            <div className="space-y-2">
              <h1 className="text-2xl font-semibold text-foreground">
                Something went wrong
              </h1>
              <p className="text-muted-foreground">
                An unexpected error occurred. Please try reloading the page.
              </p>
            </div>

            {/* Reload page button (Requirement 24.4) */}
            <Button onClick={this.handleReload} size="lg">
              Reload page
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
