import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { adminApi } from '../../services/adminApi'
import type { 
  DashboardStats, 
  Order, 
  Product, 
  User,
  RevenueData,
  CategoryStats,
  ProductStats,
  UserActivity,
  ReportFilters 
} from '../../types'

interface AdminState {
  // Dashboard
  dashboardStats: DashboardStats | null
  revenueData: RevenueData[]
  categoryStats: CategoryStats[]
  topProducts: ProductStats[]
  userActivity: UserActivity[]
  realtimeStats: {
    active_users: number
    pending_orders: number
    low_stock_alerts: number
    today_revenue: number
  } | null
  
  // Orders
  orders: Order[]
  selectedOrder: Order | null
  ordersCount: number
  
  // Products
  products: Product[]
  selectedProduct: Product | null
  productsCount: number
  
  // Users
  users: User[]
  selectedUser: User | null
  usersCount: number
  
  // UI State
  isLoading: boolean
  error: string | null
  filters: ReportFilters
}

const initialState: AdminState = {
  dashboardStats: null,
  revenueData: [],
  categoryStats: [],
  topProducts: [],
  userActivity: [],
  realtimeStats: null,
  orders: [],
  selectedOrder: null,
  ordersCount: 0,
  products: [],
  selectedProduct: null,
  productsCount: 0,
  users: [],
  selectedUser: null,
  usersCount: 0,
  isLoading: false,
  error: null,
  filters: {
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  }
}

// Dashboard Thunks
export const fetchDashboardStats = createAsyncThunk(
  'admin/fetchDashboardStats',
  async () => {
    return await adminApi.getDashboardStats()
  }
)

export const fetchRevenueData = createAsyncThunk(
  'admin/fetchRevenueData',
  async (period: 'daily' | 'weekly' | 'monthly' = 'daily') => {
    return await adminApi.getRevenueData(period)
  }
)

export const fetchCategoryStats = createAsyncThunk(
  'admin/fetchCategoryStats',
  async () => {
    return await adminApi.getCategoryStats()
  }
)

export const fetchTopProducts = createAsyncThunk(
  'admin/fetchTopProducts',
  async (limit: number = 10) => {
    return await adminApi.getTopProducts(limit)
  }
)

export const fetchUserActivity = createAsyncThunk(
  'admin/fetchUserActivity',
  async (days: number = 30) => {
    return await adminApi.getUserActivity(days)
  }
)

export const fetchRealtimeStats = createAsyncThunk(
  'admin/fetchRealtimeStats',
  async () => {
    return await adminApi.getRealtimeStats()
  }
)

// Orders Thunks
export const fetchOrders = createAsyncThunk(
  'admin/fetchOrders',
  async (filters?: Partial<ReportFilters>) => {
    return await adminApi.getOrders(filters)
  }
)

export const fetchOrder = createAsyncThunk(
  'admin/fetchOrder',
  async (id: number) => {
    return await adminApi.getOrder(id)
  }
)

export const updateOrderStatus = createAsyncThunk(
  'admin/updateOrderStatus',
  async ({ id, status }: { id: number; status: Order['status'] }) => {
    return await adminApi.updateOrderStatus(id, status)
  }
)

export const updatePaymentStatus = createAsyncThunk(
  'admin/updatePaymentStatus',
  async ({ id, payment_status }: { id: number; payment_status: Order['payment_status'] }) => {
    return await adminApi.updatePaymentStatus(id, payment_status)
  }
)

export const updateTrackingNumber = createAsyncThunk(
  'admin/updateTrackingNumber',
  async ({ id, tracking_number }: { id: number; tracking_number: string }) => {
    return await adminApi.updateTrackingNumber(id, tracking_number)
  }
)

// Products Thunks
export const fetchAdminProducts = createAsyncThunk(
  'admin/fetchProducts',
  async (filters?: { category?: number; search?: string; is_active?: boolean }) => {
    return await adminApi.getProducts(filters)
  }
)

export const updateProductStock = createAsyncThunk(
  'admin/updateProductStock',
  async ({ id, stock_quantity }: { id: number; stock_quantity: number }) => {
    return await adminApi.updateStock(id, stock_quantity)
  }
)

// Users Thunks
export const fetchUsers = createAsyncThunk(
  'admin/fetchUsers',
  async (filters?: { search?: string; is_active?: boolean }) => {
    return await adminApi.getUsers(filters)
  }
)

export const fetchUser = createAsyncThunk(
  'admin/fetchUser',
  async (id: number) => {
    return await adminApi.getUser(id)
  }
)

// Reports Thunk
export const generateReport = createAsyncThunk(
  'admin/generateReport',
  async ({ type, filters, format }: { 
    type: 'sales' | 'inventory' | 'users'
    filters: ReportFilters
    format: 'csv' | 'pdf' | 'xlsx'
  }) => {
    const blob = await adminApi.generateReport(type, filters, format)
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${type}-report-${new Date().toISOString().split('T')[0]}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    return { success: true }
  }
)

const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearError: (state) => {
      state.error = null
    }
  },
  extraReducers: (builder) => {
    builder
      // Dashboard Stats
      .addCase(fetchDashboardStats.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchDashboardStats.fulfilled, (state, action) => {
        state.isLoading = false
        state.dashboardStats = action.payload
      })
      .addCase(fetchDashboardStats.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch dashboard stats'
      })
      
      // Revenue Data
      .addCase(fetchRevenueData.fulfilled, (state, action) => {
        state.revenueData = action.payload
      })
      
      // Category Stats
      .addCase(fetchCategoryStats.fulfilled, (state, action) => {
        state.categoryStats = action.payload
      })
      
      // Top Products
      .addCase(fetchTopProducts.fulfilled, (state, action) => {
        state.topProducts = action.payload
      })
      
      // User Activity
      .addCase(fetchUserActivity.fulfilled, (state, action) => {
        state.userActivity = action.payload
      })
      
      // Realtime Stats
      .addCase(fetchRealtimeStats.fulfilled, (state, action) => {
        state.realtimeStats = action.payload
      })
      
      // Orders
      .addCase(fetchOrders.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.isLoading = false
        state.orders = action.payload.results
        state.ordersCount = action.payload.count || 0
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch orders'
      })
      
      // Single Order
      .addCase(fetchOrder.fulfilled, (state, action) => {
        state.selectedOrder = action.payload
      })
      
      // Update Order Status
      .addCase(updateOrderStatus.fulfilled, (state, action) => {
        const index = state.orders.findIndex(order => order.id === action.payload.id)
        if (index !== -1) {
          state.orders[index] = action.payload
        }
        if (state.selectedOrder?.id === action.payload.id) {
          state.selectedOrder = action.payload
        }
      })
      
      // Update Payment Status
      .addCase(updatePaymentStatus.fulfilled, (state, action) => {
        const index = state.orders.findIndex(order => order.id === action.payload.id)
        if (index !== -1) {
          state.orders[index] = action.payload
        }
        if (state.selectedOrder?.id === action.payload.id) {
          state.selectedOrder = action.payload
        }
      })
      
      // Update Tracking Number
      .addCase(updateTrackingNumber.fulfilled, (state, action) => {
        const index = state.orders.findIndex(order => order.id === action.payload.id)
        if (index !== -1) {
          state.orders[index] = action.payload
        }
        if (state.selectedOrder?.id === action.payload.id) {
          state.selectedOrder = action.payload
        }
      })
      
      // Products
      .addCase(fetchAdminProducts.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchAdminProducts.fulfilled, (state, action) => {
        state.isLoading = false
        state.products = action.payload.results
        state.productsCount = action.payload.count || 0
      })
      .addCase(fetchAdminProducts.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch products'
      })
      
      // Users
      .addCase(fetchUsers.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.isLoading = false
        state.users = action.payload.results
        state.usersCount = action.payload.count || 0
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch users'
      })
      
      // Single User
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.selectedUser = action.payload
      })
  }
})

export const { setFilters, clearError } = adminSlice.actions
export default adminSlice.reducer