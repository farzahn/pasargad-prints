import { Navigate, Outlet } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'
import LoadingSpinner from './LoadingSpinner'
import type { AdminUser } from '../types'

interface AdminRouteProps {
  children?: React.ReactNode
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { user, isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth)
  
  if (isLoading) {
    return <LoadingSpinner />
  }
  
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }
  
  // Check if user is admin
  const adminUser = user as AdminUser
  if (!adminUser.is_staff && !adminUser.is_superuser) {
    return <Navigate to="/" replace />
  }
  
  return children ? <>{children}</> : <Outlet />
}