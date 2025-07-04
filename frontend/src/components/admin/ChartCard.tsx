import type { ReactNode } from 'react'

interface ChartCardProps {
  title: string
  children: ReactNode
  loading?: boolean
  error?: string
  className?: string
}

export default function ChartCard({ 
  title, 
  children, 
  loading = false, 
  error, 
  className = '' 
}: ChartCardProps) {
  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-900">{title}</h3>
      
      {loading ? (
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      ) : error ? (
        <div className="h-64 flex items-center justify-center text-red-500">
          <div className="text-center">
            <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      ) : (
        <div className="h-64">
          {children}
        </div>
      )}
    </div>
  )
}