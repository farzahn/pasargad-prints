import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit'
import api from '../../services/api'
import type { RootState } from '../index'

export interface Banner {
  id: number
  title: string
  subtitle?: string
  description?: string
  image_url: string
  link_url?: string
  link_text?: string
  banner_type: 'hero' | 'promotion' | 'announcement' | 'sale'
  position: 'top' | 'middle' | 'bottom'
  is_active: boolean
  start_date?: string
  end_date?: string
  priority: number
  background_color?: string
  text_color?: string
  created_at: string
  updated_at: string
}

interface BannersState {
  banners: Banner[]
  loading: boolean
  error: string | null
  dismissedBanners: number[]
}

const initialState: BannersState = {
  banners: [],
  loading: false,
  error: null,
  dismissedBanners: JSON.parse(localStorage.getItem('dismissedBanners') || '[]'),
}

// Thunks
export const fetchBanners = createAsyncThunk<Banner[]>(
  'banners/fetchBanners',
  async () => {
    const response = await api.get('/api/banners/')
    return response.data
  }
)

const bannersSlice = createSlice({
  name: 'banners',
  initialState,
  reducers: {
    dismissBanner: (state, action: PayloadAction<number>) => {
      state.dismissedBanners.push(action.payload)
      localStorage.setItem('dismissedBanners', JSON.stringify(state.dismissedBanners))
    },
    clearDismissedBanners: (state) => {
      state.dismissedBanners = []
      localStorage.removeItem('dismissedBanners')
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBanners.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchBanners.fulfilled, (state, action) => {
        state.loading = false
        state.banners = action.payload
      })
      .addCase(fetchBanners.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch banners'
      })
  },
})

export const { dismissBanner, clearDismissedBanners } = bannersSlice.actions

// Selectors
export const selectActiveBanners = (state: RootState) => {
  const now = new Date().toISOString()
  return state.banners.banners.filter(banner =>
    banner.is_active &&
    !state.banners.dismissedBanners.includes(banner.id) &&
    (!banner.start_date || banner.start_date <= now) &&
    (!banner.end_date || banner.end_date >= now)
  ).sort((a, b) => b.priority - a.priority)
}

export const selectBannersByPosition = (state: RootState) => {
  const banners = selectActiveBanners(state)
  return banners.reduce((acc, banner) => {
    if (!acc[banner.position]) {
      acc[banner.position] = []
    }
    acc[banner.position].push(banner)
    return acc
  }, {} as Record<Banner['position'], Banner[]>)
}

export const selectBannersByType = (state: RootState) => {
  const banners = selectActiveBanners(state)
  return banners.reduce((acc, banner) => {
    if (!acc[banner.banner_type]) {
      acc[banner.banner_type] = []
    }
    acc[banner.banner_type].push(banner)
    return acc
  }, {} as Record<Banner['banner_type'], Banner[]>)
}

export default bannersSlice.reducer