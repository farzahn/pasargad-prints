import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Outlet } from 'react-router-dom'
import type { AppDispatch, RootState } from '../store/index'
import { fetchCart } from '../store/slices/cartSlice'
import { fetchWishlist } from '../store/slices/wishlistSlice'
import { fetchUserProfile } from '../store/slices/authSlice'
import Header from './Header'
import Footer from './Footer'
import ProductComparison from './ProductComparison'

interface LayoutProps {
  children?: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)

  useEffect(() => {
    // Fetch cart on app load
    dispatch(fetchCart())
    
    // Fetch user profile and wishlist if authenticated
    if (isAuthenticated) {
      // Only fetch user profile if we don't have it yet
      if (!user) {
        dispatch(fetchUserProfile())
      }
      dispatch(fetchWishlist())
    }
  }, [dispatch, isAuthenticated, user])

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1">
        {children || <Outlet />}
      </main>
      <Footer />
      <ProductComparison />
    </div>
  )
}

export default Layout