import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/apiConfig'
import type { Referral, ReferralStats, ReferralDashboard } from '../../types'

export interface ReferralState {
  dashboard: ReferralDashboard | null
  isLoading: boolean
  error: string | null
  sendingReferral: boolean
}

const initialState: ReferralState = {
  dashboard: null,
  isLoading: false,
  error: null,
  sendingReferral: false,
}

// Async thunks
export const fetchReferralDashboard = createAsyncThunk(
  'referral/fetchDashboard',
  async () => {
    const response = await api.get('/api/referrals/dashboard/')
    return response.data
  }
)

export const sendReferral = createAsyncThunk(
  'referral/sendReferral',
  async (email: string) => {
    const response = await api.post('/api/referrals/send/', { email })
    return response.data
  }
)

export const claimReward = createAsyncThunk(
  'referral/claimReward',
  async (referralId: number) => {
    const response = await api.post(`/api/referrals/${referralId}/claim/`)
    return response.data
  }
)

const referralSlice = createSlice({
  name: 'referral',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch dashboard
      .addCase(fetchReferralDashboard.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchReferralDashboard.fulfilled, (state, action) => {
        state.isLoading = false
        state.dashboard = action.payload
        state.error = null
      })
      .addCase(fetchReferralDashboard.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch referral dashboard'
      })
      
      // Send referral
      .addCase(sendReferral.pending, (state) => {
        state.sendingReferral = true
        state.error = null
      })
      .addCase(sendReferral.fulfilled, (state, action) => {
        state.sendingReferral = false
        if (state.dashboard) {
          state.dashboard.referrals.unshift(action.payload)
          state.dashboard.stats.total_referrals += 1
          state.dashboard.stats.pending_referrals += 1
        }
        state.error = null
      })
      .addCase(sendReferral.rejected, (state, action) => {
        state.sendingReferral = false
        state.error = action.error.message || 'Failed to send referral'
      })
      
      // Claim reward
      .addCase(claimReward.fulfilled, (state, action) => {
        if (state.dashboard) {
          const referralIndex = state.dashboard.referrals.findIndex(
            r => r.id === action.payload.id
          )
          if (referralIndex !== -1) {
            state.dashboard.referrals[referralIndex] = action.payload
            state.dashboard.stats.available_rewards = action.payload.available_rewards
          }
        }
      })
  },
})

export const { clearError } = referralSlice.actions
export default referralSlice.reducer