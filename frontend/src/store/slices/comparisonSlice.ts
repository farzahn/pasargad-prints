import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { Product } from '../../types'
import type { RootState } from '../index'

interface ComparisonState {
  products: Product[]
  isOpen: boolean
  maxProducts: number
}

const initialState: ComparisonState = {
  products: [],
  isOpen: false,
  maxProducts: 4,
}

const comparisonSlice = createSlice({
  name: 'comparison',
  initialState,
  reducers: {
    addToComparison: (state, action: PayloadAction<Product>) => {
      const existingProduct = state.products.find(p => p.id === action.payload.id)
      if (!existingProduct && state.products.length < state.maxProducts) {
        state.products.push(action.payload)
        state.isOpen = true
      }
    },
    removeFromComparison: (state, action: PayloadAction<number>) => {
      state.products = state.products.filter(p => p.id !== action.payload)
      if (state.products.length === 0) {
        state.isOpen = false
      }
    },
    clearComparison: (state) => {
      state.products = []
      state.isOpen = false
    },
    toggleComparisonPanel: (state) => {
      state.isOpen = !state.isOpen
    },
    setComparisonPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.isOpen = action.payload
    },
  },
})

export const {
  addToComparison,
  removeFromComparison,
  clearComparison,
  toggleComparisonPanel,
  setComparisonPanelOpen,
} = comparisonSlice.actions

// Selectors
export const selectComparisonProducts = (state: RootState) => state.comparison.products
export const selectIsComparisonOpen = (state: RootState) => state.comparison.isOpen
export const selectComparisonCount = (state: RootState) => state.comparison.products.length
export const selectCanAddToComparison = (state: RootState) => 
  state.comparison.products.length < state.comparison.maxProducts
export const selectIsInComparison = (state: RootState, productId: number) =>
  state.comparison.products.some(p => p.id === productId)

export default comparisonSlice.reducer