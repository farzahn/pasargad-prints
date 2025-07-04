import axios from 'axios'
import type { AxiosResponse } from 'axios'

// When VITE_API_URL is empty, use relative URLs which work with ngrok
// This allows the frontend to work with any domain/tunnel without hardcoding URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

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