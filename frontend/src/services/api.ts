import { api } from './apiConfig'

let storeInstance: any = null

export const setStore = (store: any) => {
  storeInstance = store
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (storeInstance) {
      const token = storeInstance.getState().auth.accessToken
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry && storeInstance) {
      originalRequest._retry = true
      
      try {
        // Import actions dynamically to avoid circular dependency
        const { refreshAccessToken, logout } = await import('../store/slices/authSlice')
        await storeInstance.dispatch(refreshAccessToken())
        const newToken = storeInstance.getState().auth.accessToken
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        const { logout } = await import('../store/slices/authSlice')
        storeInstance.dispatch(logout())
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api