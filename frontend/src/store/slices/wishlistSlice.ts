import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit'
import api from '../../services/api'
import type { Wishlist, WishlistItem, ApiError } from '../../types'
import type { RootState } from '../index'

interface WishlistState {
  wishlist: Wishlist | null
  loading: boolean
  error: string | null
  isItemInWishlist: Record<number, boolean>
}

const initialState: WishlistState = {
  wishlist: null,
  loading: false,
  error: null,
  isItemInWishlist: {},
}

// Thunks
export const fetchWishlist = createAsyncThunk<Wishlist, void, { rejectValue: ApiError }>(
  'wishlist/fetchWishlist',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/wishlist/')
      return response.data
    } catch (error: any) {
      return rejectWithValue({
        message: error.response?.data?.detail || 'Failed to fetch wishlist',
        status: error.response?.status,
      })
    }
  }
)

export const addToWishlist = createAsyncThunk<
  WishlistItem,
  { product_id: number },
  { rejectValue: ApiError }
>('wishlist/addToWishlist', async ({ product_id }, { rejectWithValue }) => {
  try {
    const response = await api.post('/api/wishlist/items/', { product_id })
    return response.data
  } catch (error: any) {
    return rejectWithValue({
      message: error.response?.data?.detail || 'Failed to add to wishlist',
      status: error.response?.status,
    })
  }
})

export const removeFromWishlist = createAsyncThunk<
  { id: number },
  { item_id: number },
  { rejectValue: ApiError }
>('wishlist/removeFromWishlist', async ({ item_id }, { rejectWithValue }) => {
  try {
    await api.delete(`/api/wishlist/items/${item_id}/`)
    return { id: item_id }
  } catch (error: any) {
    return rejectWithValue({
      message: error.response?.data?.detail || 'Failed to remove from wishlist',
      status: error.response?.status,
    })
  }
})

export const clearWishlist = createAsyncThunk<void, void, { rejectValue: ApiError }>(
  'wishlist/clearWishlist',
  async (_, { rejectWithValue }) => {
    try {
      await api.delete('/api/wishlist/')
    } catch (error: any) {
      return rejectWithValue({
        message: error.response?.data?.detail || 'Failed to clear wishlist',
        status: error.response?.status,
      })
    }
  }
)

const wishlistSlice = createSlice({
  name: 'wishlist',
  initialState,
  reducers: {
    resetWishlistError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    // Fetch wishlist
    builder
      .addCase(fetchWishlist.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchWishlist.fulfilled, (state, action) => {
        state.loading = false
        state.wishlist = action.payload
        // Update isItemInWishlist map
        state.isItemInWishlist = {}
        action.payload.items.forEach((item) => {
          state.isItemInWishlist[item.product.id] = true
        })
      })
      .addCase(fetchWishlist.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload?.message || 'Failed to fetch wishlist'
      })

    // Add to wishlist
    builder
      .addCase(addToWishlist.pending, (state) => {
        state.error = null
      })
      .addCase(addToWishlist.fulfilled, (state, action) => {
        if (state.wishlist) {
          state.wishlist.items.push(action.payload)
          state.wishlist.total_items += 1
          state.isItemInWishlist[action.payload.product.id] = true
        }
      })
      .addCase(addToWishlist.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to add to wishlist'
      })

    // Remove from wishlist
    builder
      .addCase(removeFromWishlist.pending, (state) => {
        state.error = null
      })
      .addCase(removeFromWishlist.fulfilled, (state, action) => {
        if (state.wishlist) {
          const removedItem = state.wishlist.items.find(
            (item) => item.id === action.payload.id
          )
          if (removedItem) {
            state.wishlist.items = state.wishlist.items.filter(
              (item) => item.id !== action.payload.id
            )
            state.wishlist.total_items -= 1
            state.isItemInWishlist[removedItem.product.id] = false
          }
        }
      })
      .addCase(removeFromWishlist.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to remove from wishlist'
      })

    // Clear wishlist
    builder
      .addCase(clearWishlist.pending, (state) => {
        state.error = null
      })
      .addCase(clearWishlist.fulfilled, (state) => {
        state.wishlist = null
        state.isItemInWishlist = {}
      })
      .addCase(clearWishlist.rejected, (state, action) => {
        state.error = action.payload?.message || 'Failed to clear wishlist'
      })
  },
})

export const { resetWishlistError } = wishlistSlice.actions

// Selectors
export const selectWishlist = (state: RootState) => state.wishlist.wishlist
export const selectWishlistItems = (state: RootState) => state.wishlist.wishlist?.items || []
export const selectWishlistCount = (state: RootState) => state.wishlist.wishlist?.total_items || 0
export const selectIsItemInWishlist = (state: RootState, productId: number) =>
  state.wishlist.isItemInWishlist[productId] || false
export const selectWishlistLoading = (state: RootState) => state.wishlist.loading
export const selectWishlistError = (state: RootState) => state.wishlist.error

export default wishlistSlice.reducer