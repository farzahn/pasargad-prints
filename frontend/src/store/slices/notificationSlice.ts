import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/apiConfig'
import type { Notification, NotificationSettings } from '../../types'

export interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  settings: NotificationSettings | null
  isLoading: boolean
  error: string | null
}

const initialState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  settings: null,
  isLoading: false,
  error: null,
}

// Async thunks
export const fetchNotifications = createAsyncThunk(
  'notification/fetchNotifications',
  async () => {
    const response = await api.get('/api/notifications/')
    return response.data
  }
)

export const markAsRead = createAsyncThunk(
  'notification/markAsRead',
  async (notificationId: number) => {
    const response = await api.patch(`/api/notifications/${notificationId}/`, {
      is_read: true
    })
    return response.data
  }
)

export const markAllAsRead = createAsyncThunk(
  'notification/markAllAsRead',
  async () => {
    const response = await api.post('/api/notifications/mark-all-read/')
    return response.data
  }
)

export const fetchNotificationSettings = createAsyncThunk(
  'notification/fetchSettings',
  async () => {
    const response = await api.get('/api/notifications/settings/')
    return response.data
  }
)

export const updateNotificationSettings = createAsyncThunk(
  'notification/updateSettings',
  async (settings: Partial<NotificationSettings>) => {
    const response = await api.patch('/api/notifications/settings/', settings)
    return response.data
  }
)

const notificationSlice = createSlice({
  name: 'notification',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.unshift(action.payload)
      if (!action.payload.is_read) {
        state.unreadCount += 1
      }
    },
    removeNotification: (state, action: PayloadAction<number>) => {
      const index = state.notifications.findIndex(n => n.id === action.payload)
      if (index !== -1) {
        const notification = state.notifications[index]
        if (!notification.is_read) {
          state.unreadCount -= 1
        }
        state.notifications.splice(index, 1)
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch notifications
      .addCase(fetchNotifications.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchNotifications.fulfilled, (state, action) => {
        state.isLoading = false
        state.notifications = action.payload.results
        state.unreadCount = action.payload.results.filter((n: Notification) => !n.is_read).length
        state.error = null
      })
      .addCase(fetchNotifications.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch notifications'
      })
      
      // Mark as read
      .addCase(markAsRead.fulfilled, (state, action) => {
        const index = state.notifications.findIndex(n => n.id === action.payload.id)
        if (index !== -1) {
          state.notifications[index] = action.payload
          if (action.payload.is_read) {
            state.unreadCount = Math.max(0, state.unreadCount - 1)
          }
        }
      })
      
      // Mark all as read
      .addCase(markAllAsRead.fulfilled, (state) => {
        state.notifications.forEach(notification => {
          notification.is_read = true
        })
        state.unreadCount = 0
      })
      
      // Fetch settings
      .addCase(fetchNotificationSettings.fulfilled, (state, action) => {
        state.settings = action.payload
      })
      
      // Update settings
      .addCase(updateNotificationSettings.fulfilled, (state, action) => {
        state.settings = action.payload
      })
  },
})

export const { clearError, addNotification, removeNotification } = notificationSlice.actions
export default notificationSlice.reducer