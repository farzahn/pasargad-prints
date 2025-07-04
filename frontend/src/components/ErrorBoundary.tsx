import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      const isCheckoutError = window.location.pathname.includes('checkout')
      
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
            <div className="text-center">
              <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {isCheckoutError ? 'Checkout Error' : 'Something went wrong!'}
              </h1>
              <p className="text-gray-600 mb-6">
                {isCheckoutError 
                  ? 'We encountered an issue processing your checkout. Please try again.'
                  : `Error: ${this.state.error?.message || 'An unexpected error occurred'}`}
              </p>
              
              <div className="space-y-3">
                <button 
                  onClick={() => window.location.reload()} 
                  className="w-full bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700 transition-colors"
                >
                  Try Again
                </button>
                
                {isCheckoutError && (
                  <button 
                    onClick={() => window.location.href = '/cart'} 
                    className="w-full bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300 transition-colors"
                  >
                    Return to Cart
                  </button>
                )}
                
                <button 
                  onClick={() => window.location.href = '/'} 
                  className="w-full text-gray-600 hover:text-gray-800 text-sm"
                >
                  Go to Homepage
                </button>
              </div>
              
              {import.meta.env.DEV && (
                <details className="mt-6 text-left">
                  <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                    Technical Details
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-3 rounded overflow-auto">
                    {JSON.stringify({
                      message: this.state.error?.message,
                      stack: this.state.error?.stack
                    }, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary