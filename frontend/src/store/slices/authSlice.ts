import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/apiConfig'
import type { User } from '../../types'

export interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  rememberUsername: string
}

const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!localStorage.getItem('accessToken'),
  isLoading: false,
  error: null,
  rememberUsername: localStorage.getItem('rememberUsername') || '',
}

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string; rememberUsername?: boolean }) => {
    const response = await api.post('/api/users/auth/login/', {
      email: credentials.email,
      password: credentials.password,
    })
    
    // Store tokens
    localStorage.setItem('accessToken', response.data.access)
    localStorage.setItem('refreshToken', response.data.refresh)
    
    // Handle remember username
    if (credentials.rememberUsername) {
      localStorage.setItem('rememberUsername', credentials.email)
    } else {
      localStorage.removeItem('rememberUsername')
    }
    
    // Get user profile
    const userResponse = await api.get('/api/users/profile/', {
      headers: { Authorization: `Bearer ${response.data.access}` }
    })
    
    return {
      tokens: response.data,
      user: userResponse.data,
      rememberUsername: credentials.rememberUsername ? credentials.email : '',
    }
  }
)

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData: {
    email: string
    username: string
    first_name: string
    last_name: string
    password: string
    password_confirm: string
    phone?: string
    newsletter_subscription?: boolean
  }, { rejectWithValue }) => {
    try {
      console.log('🔍 authSlice - registerUser called with userData:', userData)
      console.log('🔍 authSlice - userData individual fields:')
      console.log('  - email:', userData.email)
      console.log('  - username:', userData.username)  
      console.log('  - first_name:', userData.first_name)
      console.log('  - last_name:', userData.last_name)
      console.log('  - password:', userData.password ? '[REDACTED]' : 'EMPTY')
      console.log('  - password_confirm:', userData.password_confirm ? '[REDACTED]' : 'EMPTY')
      console.log('  - phone:', userData.phone)
      console.log('  - newsletter_subscription:', userData.newsletter_subscription)
      
      // Clean up data - remove empty strings and undefined values
      const cleanedData = {
        email: userData.email.trim(),
        username: userData.username.trim(),
        first_name: userData.first_name.trim(),
        last_name: userData.last_name.trim(),
        password: userData.password,
        password_confirm: userData.password_confirm,
        ...(userData.phone && { phone: userData.phone.trim() }),
        newsletter_subscription: userData.newsletter_subscription || false
      }
      
      console.log('🔍 authSlice - Cleaned data being sent:', cleanedData)
      console.log('🔍 authSlice - Making API call to /api/users/auth/register/')
      
      const response = await api.post('/api/users/auth/register/', cleanedData)
      
      console.log('🔍 authSlice - API response:', response.data)
      
      // Store tokens
      localStorage.setItem('accessToken', response.data.tokens.access)
      localStorage.setItem('refreshToken', response.data.tokens.refresh)
      
      return response.data
    } catch (error: any) {
      console.log('🔍 authSlice - Registration error:', error)
      console.log('🔍 authSlice - Error response:', error.response?.data)
      console.log('🔍 authSlice - Error status:', error.response?.status)
      
      // Return detailed error information
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          Object.values(error.response?.data || {}).flat().join(', ') ||
                          error.message || 
                          'Registration failed'
      
      return rejectWithValue({
        message: errorMessage,
        status: error.response?.status,
        data: error.response?.data
      })
    }
  }
)

export const refreshAccessToken = createAsyncThunk(
  'auth/refresh',
  async (_, { getState, rejectWithValue }) => {
    const state = getState() as { auth: AuthState }
    const refreshToken = state.auth.refreshToken
    
    if (!refreshToken) {
      return rejectWithValue('No refresh token available')
    }
    
    try {
      const response = await api.post('/api/users/auth/refresh/', {
        refresh: refreshToken,
      })
      
      localStorage.setItem('accessToken', response.data.access)
      
      return response.data
    } catch (error) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      return rejectWithValue('Token refresh failed')
    }
  }
)

export const fetchUserProfile = createAsyncThunk(
  'auth/fetchProfile',
  async () => {
    const response = await api.get('/api/users/profile/')
    return response.data
  }
)

export const socialLogin = createAsyncThunk(
  'auth/socialLogin',
  async (data: { provider: string; access_token: string }) => {
    const response = await api.post('/api/users/auth/social/', data)
    
    // Store tokens
    localStorage.setItem('accessToken', response.data.access_token)
    localStorage.setItem('refreshToken', response.data.refresh_token)
    
    return response.data
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
      state.isAuthenticated = false
      state.error = null
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    },
    clearError: (state) => {
      state.error = null
    },
    setRememberUsername: (state, action: PayloadAction<string>) => {
      state.rememberUsername = action.payload
      localStorage.setItem('rememberUsername', action.payload)
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = true
        state.accessToken = action.payload.tokens.access
        state.refreshToken = action.payload.tokens.refresh
        state.user = action.payload.user
        state.rememberUsername = action.payload.rememberUsername
        state.error = null
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Login failed'
      })
      
      // Register
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = true
        state.accessToken = action.payload.tokens.access
        state.refreshToken = action.payload.tokens.refresh
        state.user = action.payload.user
        state.error = null
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = (action.payload as any)?.message || action.error.message || 'Registration failed'
      })
      
      // Refresh token
      .addCase(refreshAccessToken.fulfilled, (state, action) => {
        state.accessToken = action.payload.access
        if (action.payload.refresh) {
          state.refreshToken = action.payload.refresh
          localStorage.setItem('refreshToken', action.payload.refresh)
        }
      })
      .addCase(refreshAccessToken.rejected, (state) => {
        state.user = null
        state.accessToken = null
        state.refreshToken = null
        state.isAuthenticated = false
      })
      
      // Fetch profile
      .addCase(fetchUserProfile.pending, (state) => {
        state.isLoading = true
      })
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload
      })
      .addCase(fetchUserProfile.rejected, (state, action) => {
        state.isLoading = false
        // If we can't fetch the user profile due to invalid token, log out
        if (action.error.message?.includes('401') || action.error.message?.includes('Unauthorized')) {
          state.user = null
          state.accessToken = null
          state.refreshToken = null
          state.isAuthenticated = false
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
        }
      })
      
      // Social login
      .addCase(socialLogin.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(socialLogin.fulfilled, (state, action) => {
        state.isLoading = false
        state.isAuthenticated = true
        state.accessToken = action.payload.access_token
        state.refreshToken = action.payload.refresh_token
        state.user = action.payload.user
        state.error = null
      })
      .addCase(socialLogin.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Social login failed'
      })
  },
})

export const { logout, clearError, setRememberUsername } = authSlice.actions
export default authSlice.reducer