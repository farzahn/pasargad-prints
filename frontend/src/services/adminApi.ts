import { api } from './apiConfig'
import type { 
  DashboardStats, 
  Order, 
  Product, 
  ProductDetail,
  User,
  RevenueData,
  CategoryStats,
  ProductStats,
  UserActivity,
  ReportFilters,
  ApiResponse 
} from '../types'

// Dashboard APIs
export const adminApi = {
  // Dashboard Statistics
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await api.get('/api/admin/dashboard/stats/')
    return response.data
  },

  getRevenueData: async (period: 'daily' | 'weekly' | 'monthly' = 'daily'): Promise<RevenueData[]> => {
    const response = await api.get(`/api/admin/dashboard/revenue/?period=${period}`)
    return response.data
  },

  getCategoryStats: async (): Promise<CategoryStats[]> => {
    const response = await api.get('/api/admin/dashboard/categories/')
    return response.data
  },

  getTopProducts: async (limit: number = 10): Promise<ProductStats[]> => {
    const response = await api.get(`/api/admin/dashboard/top-products/?limit=${limit}`)
    return response.data
  },

  getUserActivity: async (days: number = 30): Promise<UserActivity[]> => {
    const response = await api.get(`/api/admin/dashboard/user-activity/?days=${days}`)
    return response.data
  },

  // Orders Management
  getOrders: async (filters?: Partial<ReportFilters>): Promise<ApiResponse<Order>> => {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString())
      })
    }
    const response = await api.get(`/api/admin/orders/?${params.toString()}`)
    return response.data
  },

  getOrder: async (id: number): Promise<Order> => {
    const response = await api.get(`/api/admin/orders/${id}/`)
    return response.data
  },

  updateOrderStatus: async (id: number, status: Order['status']): Promise<Order> => {
    const response = await api.patch(`/api/admin/orders/${id}/`, { status })
    return response.data
  },

  updatePaymentStatus: async (id: number, payment_status: Order['payment_status']): Promise<Order> => {
    const response = await api.patch(`/api/admin/orders/${id}/`, { payment_status })
    return response.data
  },

  updateTrackingNumber: async (id: number, tracking_number: string): Promise<Order> => {
    const response = await api.patch(`/api/admin/orders/${id}/`, { tracking_number })
    return response.data
  },

  // Products Management
  getProducts: async (filters?: { category?: number; search?: string; is_active?: boolean }): Promise<ApiResponse<Product>> => {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString())
      })
    }
    const response = await api.get(`/api/admin/products/?${params.toString()}`)
    return response.data
  },

  getProduct: async (id: number): Promise<ProductDetail> => {
    const response = await api.get(`/api/admin/products/${id}/`)
    return response.data
  },

  createProduct: async (productData: FormData): Promise<ProductDetail> => {
    const response = await api.post('/api/admin/products/', productData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  updateProduct: async (id: number, productData: FormData): Promise<ProductDetail> => {
    const response = await api.patch(`/api/admin/products/${id}/`, productData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  deleteProduct: async (id: number): Promise<void> => {
    await api.delete(`/api/admin/products/${id}/`)
  },

  updateStock: async (id: number, stock_quantity: number): Promise<ProductDetail> => {
    const response = await api.patch(`/api/admin/products/${id}/stock/`, { stock_quantity })
    return response.data
  },

  // Users Management
  getUsers: async (filters?: { search?: string; is_active?: boolean }): Promise<ApiResponse<User>> => {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) params.append(key, value.toString())
      })
    }
    const response = await api.get(`/api/admin/users/?${params.toString()}`)
    return response.data
  },

  getUser: async (id: number): Promise<User> => {
    const response = await api.get(`/api/admin/users/${id}/`)
    return response.data
  },

  updateUser: async (id: number, userData: Partial<User>): Promise<User> => {
    const response = await api.patch(`/api/admin/users/${id}/`, userData)
    return response.data
  },

  deleteUser: async (id: number): Promise<void> => {
    await api.delete(`/api/admin/users/${id}/`)
  },

  // Reports
  generateReport: async (type: 'sales' | 'inventory' | 'users', filters: ReportFilters, format: 'csv' | 'pdf' | 'xlsx' = 'csv'): Promise<Blob> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, value.toString())
    })
    params.append('format', format)
    
    const response = await api.get(`/api/admin/reports/${type}/?${params.toString()}`, {
      responseType: 'blob'
    })
    return response.data
  },

  // Real-time updates (polling for now, can be replaced with WebSockets)
  getRealtimeStats: async (): Promise<{
    active_users: number
    pending_orders: number
    low_stock_alerts: number
    today_revenue: number
  }> => {
    const response = await api.get('/api/admin/dashboard/realtime/')
    return response.data
  }
}