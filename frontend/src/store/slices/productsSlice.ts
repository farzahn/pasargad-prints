import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/apiConfig'
import type { Product, Category, ProductDetail, ApiResponse } from '../../types'


export interface ProductsState {
  products: Product[]
  currentProduct: ProductDetail | null
  categories: Category[]
  isLoading: boolean
  error: string | null
  pagination: {
    count: number
    next: string | null
    previous: string | null
  }
  filters: {
    category?: number
    search?: string
    min_price?: number
    max_price?: number
    in_stock?: boolean
    ordering?: string
  }
}

const initialState: ProductsState = {
  products: [],
  currentProduct: null,
  categories: [],
  isLoading: false,
  error: null,
  pagination: {
    count: 0,
    next: null,
    previous: null,
  },
  filters: {},
}

// Async thunks
export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async (params?: Record<string, any>, { rejectWithValue }) => {
    try {
      const searchParams = new URLSearchParams()
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            searchParams.append(key, value.toString())
          }
        })
      }
      
      const response = await api.get(`/api/products/?${searchParams.toString()}`)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || 'Failed to fetch products')
    }
  }
)


export const fetchProductDetail = createAsyncThunk(
  'products/fetchDetail',
  async (productId: number) => {
    const response = await api.get(`/api/products/${productId}/`)
    return response.data
  }
)

export const fetchCategories = createAsyncThunk(
  'products/fetchCategories',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/products/categories/')
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || 'Failed to fetch categories')
    }
  }
)

export const searchProducts = createAsyncThunk(
  'products/search',
  async (query: string) => {
    const response = await api.get(`/api/products/search/?q=${encodeURIComponent(query)}`)
    return response.data
  }
)

const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setFilters: (state, action: PayloadAction<Partial<ProductsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {}
    },
    clearCurrentProduct: (state) => {
      state.currentProduct = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch products
      .addCase(fetchProducts.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.isLoading = false
        state.products = action.payload.results || action.payload
        if (action.payload.count !== undefined) {
          state.pagination = {
            count: action.payload.count,
            next: action.payload.next,
            previous: action.payload.previous,
          }
        }
        state.error = null
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || action.error.message || 'Failed to fetch products'
      })

      
      // Fetch product detail
      .addCase(fetchProductDetail.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchProductDetail.fulfilled, (state, action) => {
        state.isLoading = false
        state.currentProduct = action.payload
        state.error = null
      })
      .addCase(fetchProductDetail.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to fetch product details'
      })
      
      // Fetch categories
      .addCase(fetchCategories.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.isLoading = false
        state.categories = action.payload.results || action.payload
        state.error = null
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || action.error.message || 'Failed to fetch categories'
      })
      
      // Search products
      .addCase(searchProducts.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.isLoading = false
        state.products = action.payload.results
        state.pagination = {
          count: action.payload.count,
          next: null,
          previous: null,
        }
        state.error = null
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to search products'
      })
  },
})

export const { clearError, setFilters, clearFilters, clearCurrentProduct } = productsSlice.actions
export default productsSlice.reducer