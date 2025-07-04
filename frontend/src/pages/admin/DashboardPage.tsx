import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts'
import type { RootState, AppDispatch } from '../../store'
import { 
  fetchDashboardStats, 
  fetchRevenueData, 
  fetchCategoryStats,
  fetchTopProducts,
  fetchUserActivity,
  fetchRealtimeStats
} from '../../store/slices/adminSlice'
import LoadingSpinner from '../../components/LoadingSpinner'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

export default function DashboardPage() {
  const dispatch = useDispatch<AppDispatch>()
  const { 
    dashboardStats, 
    revenueData, 
    categoryStats,
    topProducts,
    userActivity,
    realtimeStats,
    isLoading 
  } = useSelector((state: RootState) => state.admin)

  useEffect(() => {
    // Initial data fetch
    dispatch(fetchDashboardStats())
    dispatch(fetchRevenueData('daily'))
    dispatch(fetchCategoryStats())
    dispatch(fetchTopProducts(5))
    dispatch(fetchUserActivity(30))
    dispatch(fetchRealtimeStats())

    // Set up polling for real-time stats
    const interval = setInterval(() => {
      dispatch(fetchRealtimeStats())
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [dispatch])

  if (isLoading && !dashboardStats) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome to your admin dashboard</p>
      </div>

      {/* Real-time Stats */}
      {realtimeStats && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-yellow-800 mb-2">Live Updates</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-yellow-600">Active Users:</span>
              <span className="ml-2 font-semibold">{realtimeStats.active_users}</span>
            </div>
            <div>
              <span className="text-yellow-600">Pending Orders:</span>
              <span className="ml-2 font-semibold">{realtimeStats.pending_orders}</span>
            </div>
            <div>
              <span className="text-yellow-600">Low Stock Alerts:</span>
              <span className="ml-2 font-semibold">{realtimeStats.low_stock_alerts}</span>
            </div>
            <div>
              <span className="text-yellow-600">Today's Revenue:</span>
              <span className="ml-2 font-semibold">${realtimeStats.today_revenue.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      {dashboardStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold">${dashboardStats.total_revenue.toFixed(2)}</p>
                <p className={`text-sm mt-2 ${dashboardStats.revenue_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboardStats.revenue_change >= 0 ? '↑' : '↓'} {Math.abs(dashboardStats.revenue_change)}% from last period
                </p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Orders</p>
                <p className="text-2xl font-bold">{dashboardStats.total_orders}</p>
                <p className={`text-sm mt-2 ${dashboardStats.orders_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboardStats.orders_change >= 0 ? '↑' : '↓'} {Math.abs(dashboardStats.orders_change)}% from last period
                </p>
              </div>
              <div className="text-3xl">📦</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Users</p>
                <p className="text-2xl font-bold">{dashboardStats.total_users}</p>
                <p className={`text-sm mt-2 ${dashboardStats.users_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboardStats.users_change >= 0 ? '↑' : '↓'} {Math.abs(dashboardStats.users_change)}% from last period
                </p>
              </div>
              <div className="text-3xl">👥</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Products</p>
                <p className="text-2xl font-bold">{dashboardStats.total_products}</p>
                <p className="text-sm mt-2 text-orange-600">
                  {dashboardStats.low_stock_products} low stock
                </p>
              </div>
              <div className="text-3xl">🛍️</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue Overview</h3>
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="revenue" stroke="#3B82F6" name="Revenue" />
                <Line type="monotone" dataKey="orders" stroke="#10B981" name="Orders" yAxisId="right" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No revenue data available</p>
          )}
        </div>

        {/* Category Sales Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Sales by Category</h3>
          {categoryStats.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryStats}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name}: ${percentage}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="revenue"
                >
                  {categoryStats.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No category data available</p>
          )}
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Top Selling Products</h3>
          {topProducts.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topProducts}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="product.name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="quantity_sold" fill="#3B82F6" name="Units Sold" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No product data available</p>
          )}
        </div>

        {/* User Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">User Activity (Last 30 Days)</h3>
          {userActivity.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={userActivity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="new_users" stroke="#10B981" name="New Users" />
                <Line type="monotone" dataKey="active_users" stroke="#F59E0B" name="Active Users" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No user activity data available</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {dashboardStats && dashboardStats.pending_orders > 0 && (
            <a
              href="/admin/orders?status=pending"
              className="flex items-center justify-between p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors"
            >
              <div>
                <p className="font-medium text-orange-900">Pending Orders</p>
                <p className="text-2xl font-bold text-orange-600">{dashboardStats.pending_orders}</p>
              </div>
              <span className="text-orange-500">→</span>
            </a>
          )}
          
          {dashboardStats && dashboardStats.low_stock_products > 0 && (
            <a
              href="/admin/products?stock=low"
              className="flex items-center justify-between p-4 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
            >
              <div>
                <p className="font-medium text-red-900">Low Stock Products</p>
                <p className="text-2xl font-bold text-red-600">{dashboardStats.low_stock_products}</p>
              </div>
              <span className="text-red-500">→</span>
            </a>
          )}
          
          <a
            href="/admin/reports"
            className="flex items-center justify-between p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <div>
              <p className="font-medium text-blue-900">Generate Reports</p>
              <p className="text-sm text-blue-600">Export data and analytics</p>
            </div>
            <span className="text-blue-500">→</span>
          </a>
        </div>
      </div>
    </div>
  )
}