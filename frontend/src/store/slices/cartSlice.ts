import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/apiConfig'
import type { Product, CartItem, Cart } from '../../types'

export interface CartState {
  cart: Cart | null
  isLoading: boolean
  error: string | null
  sessionKey: string | null
}

const initialState: CartState = {
  cart: null,
  isLoading: false,
  error: null,
  sessionKey: null,
}

// Async thunks
export const fetchCart = createAsyncThunk(
  'cart/fetch',
  async () => {
    const response = await api.get('/api/cart/')
    return response.data
  }
)

export const addToCart = createAsyncThunk(
  'cart/addItem',
  async (item: { product_id: number; quantity: number }) => {
    const response = await api.post('/api/cart/add/', item)
    return response.data
  }
)

export const updateCartItem = createAsyncThunk(
  'cart/updateItem',
  async ({ itemId, quantity }: { itemId: number; quantity: number }) => {
    const response = await api.put(`/api/cart/items/${itemId}/`, { quantity })
    return response.data
  }
)

export const removeFromCart = createAsyncThunk(
  'cart/removeItem',
  async (itemId: number) => {
    const response = await api.delete(`/api/cart/items/${itemId}/remove/`)
    return response.data
  }
)

export const clearCart = createAsyncThunk(
  'cart/clear',
  async () => {
    const response = await api.delete('/api/cart/clear/')
    return response.data
  }
)

export const mergeGuestCart = createAsyncThunk(
  'cart/mergeGuest',
  async (sessionKey: string) => {
    const response = await api.post('/api/cart/merge/', { session_key: sessionKey })
    return response.data
  }
)

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setSessionKey: (state, action: PayloadAction<string>) => {
      state.sessionKey = action.payload
    },
    clearCart: (state) => {
      state.cart = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch cart
      .addCase(fetchCart.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.isLoading = false
        state.cart = action.payload
        state.error = null
      })
      .addCase(fetchCart.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch cart'
      })
      
      // Add to cart
      .addCase(addToCart.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(addToCart.fulfilled, (state, action) => {
        state.isLoading = false
        state.cart = action.payload
        state.error = null
      })
      .addCase(addToCart.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to add item to cart'
      })
      
      // Update cart item
      .addCase(updateCartItem.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(updateCartItem.fulfilled, (state, action) => {
        state.isLoading = false
        state.cart = action.payload
        state.error = null
      })
      .addCase(updateCartItem.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to update cart item'
      })
      
      // Remove from cart
      .addCase(removeFromCart.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(removeFromCart.fulfilled, (state, action) => {
        state.isLoading = false
        state.cart = action.payload
        state.error = null
      })
      .addCase(removeFromCart.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to remove item from cart'
      })
      
      // Clear cart
      .addCase(clearCart.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(clearCart.fulfilled, (state, action) => {
        state.isLoading = false
        state.cart = action.payload
        state.error = null
      })
      .addCase(clearCart.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to clear cart'
      })
      
      // Merge guest cart
      .addCase(mergeGuestCart.fulfilled, (state, action) => {
        state.cart = action.payload
        state.sessionKey = null
      })
  },
})

export const { clearError, setSessionKey, clearCart: clearCartState } = cartSlice.actions
export default cartSlice.reducer