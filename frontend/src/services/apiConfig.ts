import axios from 'axios'
import type { AxiosResponse } from 'axios'

// API Configuration with proper fallbacks
// Priority: Environment variable > localhost:8000 for development > relative URLs for production
const getApiBaseUrl = () => {
  // Check for explicit API URL from environment
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // In development, default to localhost:8000
  if (import.meta.env.DEV) {
    return 'http://localhost:8000'
  }
  
  // In production, use relative URLs (works with reverse proxy)
  return ''
}

const API_BASE_URL = getApiBaseUrl()

// Debug: Log the API base URL in development
if (import.meta.env.DEV) {
  console.log('🔗 API Base URL:', API_BASE_URL || 'Using relative URLs')
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CORS with credentials
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Debug logging for registration requests
    if (config.url?.includes('/auth/register/') && import.meta.env.DEV) {
      console.log('🔍 API Config - Request interceptor for registration:')
      console.log('  - URL:', config.url)
      console.log('  - Method:', config.method)
      console.log('  - Headers:', config.headers)
      console.log('  - Data:', config.data)
      console.log('  - Base URL:', config.baseURL)
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for automatic token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // Debug logging for registration errors
    if (originalRequest.url?.includes('/auth/register/') && import.meta.env.DEV) {
      console.log('🔍 API Config - Response interceptor error for registration:')
      console.log('  - Status:', error.response?.status)
      console.log('  - Status Text:', error.response?.statusText)
      console.log('  - Error Data:', error.response?.data)
      console.log('  - Request Data:', originalRequest.data)
      console.log('  - Request Headers:', originalRequest.headers)
    }
    
    // If we get a 401 and haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/users/auth/refresh/`, {
            refresh: refreshToken
          })
          
          const newAccessToken = response.data.access
          localStorage.setItem('accessToken', newAccessToken)
          
          // Update the original request with new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          
          // Retry the original request
          return api(originalRequest)
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        // No refresh token, redirect to login
        localStorage.removeItem('accessToken')
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export default api