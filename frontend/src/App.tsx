import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { HelmetProvider } from 'react-helmet-async'
import { store } from './store'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import GlobalLoadingOverlay, { useGlobalLoading } from './components/GlobalLoadingOverlay'
import LoadingSpinner from './components/LoadingSpinner'
import PerformanceMonitor from './components/PerformanceMonitor'
import PWAInstallPrompt from './components/PWAInstallPrompt'

// Lazy load pages for better performance
const HomePage = lazy(() => import('./pages/HomePage'))
const EnhancedProductsPage = lazy(() => import('./pages/EnhancedProductsPage'))
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'))
const CartPage = lazy(() => import('./pages/CartPage'))
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'))
const CheckoutSuccessPage = lazy(() => import('./pages/CheckoutSuccessPage'))
const CheckoutCancelPage = lazy(() => import('./pages/CheckoutCancelPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const OrderTrackingPage = lazy(() => import('./pages/OrderTrackingPage'))
const WishlistPage = lazy(() => import('./pages/WishlistPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

// Admin components
const AdminRoute = lazy(() => import('./components/AdminRoute'))
const AdminLayout = lazy(() => import('./components/admin/AdminLayout'))
const DashboardPage = lazy(() => import('./pages/admin/DashboardPage'))
const OrdersPage = lazy(() => import('./pages/admin/OrdersPage'))
const ProductsPage = lazy(() => import('./pages/admin/ProductsPage'))
const UsersPage = lazy(() => import('./pages/admin/UsersPage'))
const ReportsPage = lazy(() => import('./pages/admin/ReportsPage'))

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <HelmetProvider>
          <Router>
            <AppContent />
          </Router>
        </HelmetProvider>
      </Provider>
    </ErrorBoundary>
  )
}

function AppContent() {
  const { isLoading, message } = useGlobalLoading();
  
  return (
    <>
      <PerformanceMonitor />
      <PWAInstallPrompt />
      <GlobalLoadingOverlay isLoading={isLoading} message={message} />
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          {/* Main Site Routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="products" element={<EnhancedProductsPage />} />
            <Route path="products/:id" element={<ProductDetailPage />} />
            <Route path="cart" element={<CartPage />} />
            <Route path="checkout" element={<CheckoutPage />} />
            <Route path="checkout/success" element={<CheckoutSuccessPage />} />
            <Route path="checkout/cancel" element={<CheckoutCancelPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="wishlist" element={<WishlistPage />} />
            <Route path="orders/track" element={<OrderTrackingPage />} />
          </Route>
          
          {/* Admin Routes */}
          <Route path="/admin" element={<AdminRoute />}>
            <Route element={<AdminLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="reports" element={<ReportsPage />} />
            </Route>
          </Route>
          
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </>
  )
}

export default App