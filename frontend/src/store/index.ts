import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import cartReducer from './slices/cartSlice'
import productsReducer from './slices/productsSlice'
import wishlistReducer from './slices/wishlistSlice'
import comparisonReducer from './slices/comparisonSlice'
import bannersReducer from './slices/bannersSlice'
import adminReducer from './slices/adminSlice'
// Removed unused slices:
// - referralReducer (feature not implemented in UI)
// - notificationReducer (feature not implemented in UI)

export const store = configureStore({
  reducer: {
    auth: authReducer,
    cart: cartReducer,
    products: productsReducer,
    wishlist: wishlistReducer,
    comparison: comparisonReducer,
    banners: bannersReducer,
    admin: adminReducer,
    // Removed: referral, notification
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch