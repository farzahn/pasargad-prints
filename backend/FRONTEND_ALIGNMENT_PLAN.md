# Frontend Alignment Plan for Backend Security and Cleanup Changes

## Overview
This plan details the necessary frontend changes to align with the backend security enhancements and code cleanup. The changes are organized by priority and risk level, with specific file paths and implementation details.

## Table of Contents
1. [Immediate Cleanup (Zero Risk)](#1-immediate-cleanup-zero-risk)
2. [API Alignment Tasks](#2-api-alignment-tasks)
3. [Security Improvements](#3-security-improvements)
4. [Testing Strategy](#4-testing-strategy)
5. [Optional Enhancements](#5-optional-enhancements)
6. [Coordination Points](#6-coordination-points)
7. [Migration Timeline](#7-migration-timeline)

---

## 1. Immediate Cleanup (Zero Risk)

### 1.1 Remove Unused Redux Slices

**Files to Delete:**
- `/frontend/src/store/slices/referralSlice.ts`
- `/frontend/src/store/slices/notificationSlice.ts`

**Files to Update:**

#### `/frontend/src/store/index.ts`
```typescript
// Remove these imports
- import referralReducer from './slices/referralSlice'
- import notificationReducer from './slices/notificationSlice'

// Update the store configuration
export const store = configureStore({
  reducer: {
    auth: authReducer,
    cart: cartReducer,
    products: productsReducer,
    wishlist: wishlistReducer,
    comparison: comparisonReducer,
    banners: bannersReducer,
    admin: adminReducer,
    // Remove these lines
-   referral: referralReducer,
-   notification: notificationReducer,
  },
  // ... rest of configuration
})
```

### 1.2 Clean Up Type Definitions

#### `/frontend/src/types/index.ts`
Remove the following unused type definitions (lines 224-318):
- `SocialProvider`
- `SocialAuthResponse`
- `Referral`
- `ReferralStats`
- `ReferralDashboard`
- `Notification`
- `NotificationSettings`
- `ShareData`
- `ShareButtonProps`

Keep only the actively used types:
- User, Address, Category, FilterOptions
- Product, ProductDetail, ProductImage, ProductReview
- CartItem, Cart
- ApiResponse, ApiError
- WishlistItem, Wishlist
- AdminUser, Order, OrderItem
- DashboardStats, RevenueData, CategoryStats, ProductStats, UserActivity, ReportFilters
- ReviewFormData, ReviewStats

### 1.3 Update TypeScript RootState Type
After removing the slices, TypeScript will automatically update the `RootState` type, but verify no components are trying to access `state.referral` or `state.notification`.

---

## 2. API Alignment Tasks

### 2.1 Remove References to Deleted Endpoints

**Endpoints Being Removed (47 total):**
- `/api/referrals/*` - All referral endpoints
- `/api/notifications/*` - All notification endpoints  
- `/api/social/*` - All social login endpoints
- `/api/oauth/*` - OAuth endpoints
- `/api/share/*` - Social sharing endpoints

**Action Required:**
1. Search for any hardcoded API calls to these endpoints
2. Remove any API service functions that call these endpoints
3. Update error handling to not expect these endpoints

### 2.2 Update API Service Configuration

#### `/frontend/src/services/apiConfig.ts`
Ensure the base URL and timeout settings are appropriate:
```typescript
export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000'
export const API_TIMEOUT = 30000 // 30 seconds

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CORS with credentials
})
```

### 2.3 Update API Error Handling

#### `/frontend/src/services/api.ts`
Add handling for new error responses:
```typescript
// Add to response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // Handle blacklisted token (new security feature)
    if (error.response?.status === 401 && error.response?.data?.code === 'token_blacklisted') {
      // Force logout without retry
      const { logout } = await import('../store/slices/authSlice')
      storeInstance.dispatch(logout())
      window.location.href = '/login'
      return Promise.reject(error)
    }
    
    // Handle rate limiting
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after']
      // Show user-friendly rate limit message
      const message = `Too many requests. Please try again in ${retryAfter} seconds.`
      // You might want to dispatch an action to show this in UI
      return Promise.reject(new Error(message))
    }
    
    // Existing 401 handling for token refresh
    if (error.response?.status === 401 && !originalRequest._retry && storeInstance) {
      // ... existing refresh logic
    }
    
    return Promise.reject(error)
  }
)
```

---

## 3. Security Improvements

### 3.1 Update CORS Handling

#### `/frontend/src/services/apiConfig.ts`
```typescript
// Ensure credentials are included for CORS
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Required for new CORS policy
})
```

### 3.2 Implement Secure Token Storage

#### Create `/frontend/src/utils/tokenStorage.ts`
```typescript
// Secure token storage utilities
const TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const tokenStorage = {
  getAccessToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEY)
  },
  
  setAccessToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token)
  },
  
  getRefreshToken: (): string | null => {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  
  setRefreshToken: (token: string): void => {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  },
  
  clearTokens: (): void => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}
```

### 3.3 Add Security Headers Check

#### Create `/frontend/src/utils/securityChecks.ts`
```typescript
export const checkSecurityHeaders = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health/`, {
      method: 'HEAD'
    })
    
    const headers = {
      'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
      'X-Frame-Options': response.headers.get('X-Frame-Options'),
      'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
      'Strict-Transport-Security': response.headers.get('Strict-Transport-Security'),
    }
    
    console.log('Security headers:', headers)
    return headers
  } catch (error) {
    console.error('Failed to check security headers:', error)
    return null
  }
}
```

### 3.4 Update Authentication Flow

#### `/frontend/src/store/slices/authSlice.ts`
Add proper logout handling for token blacklist:
```typescript
export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { getState }) => {
    const state = getState() as RootState
    const refreshToken = state.auth.refreshToken
    
    try {
      // Call backend logout to blacklist the token
      await api.post('/api/auth/logout/', { refresh: refreshToken })
    } catch (error) {
      // Even if logout fails, clear local tokens
      console.error('Logout API call failed:', error)
    }
    
    // Clear local storage
    tokenStorage.clearTokens()
  }
)
```

---

## 4. Testing Strategy

### 4.1 Component Tests

#### Update existing tests to remove referral/notification dependencies:

**Files to Update:**
- Any test files that import or mock referral/notification slices
- Component tests that check for referral/notification UI elements

**Example Test Updates:**
```typescript
// Remove from test setup
- referral: referralReducer,
- notification: notificationReducer,

// Remove from mock state
- referral: { dashboard: null, isLoading: false, error: null },
- notification: { notifications: [], unreadCount: 0, settings: null },
```

### 4.2 API Integration Tests

#### Create `/frontend/src/__tests__/api/security.test.ts`
```typescript
import { api } from '../../services/apiConfig'
import { checkSecurityHeaders } from '../../utils/securityChecks'

describe('API Security Tests', () => {
  test('includes credentials in requests', async () => {
    expect(api.defaults.withCredentials).toBe(true)
  })
  
  test('handles rate limiting', async () => {
    // Mock 429 response
    // Verify proper error handling
  })
  
  test('handles token blacklist', async () => {
    // Mock 401 with token_blacklisted code
    // Verify force logout
  })
  
  test('security headers are present', async () => {
    const headers = await checkSecurityHeaders()
    expect(headers).toBeTruthy()
    expect(headers['X-Content-Type-Options']).toBe('nosniff')
  })
})
```

### 4.3 End-to-End Tests

**Critical User Flows to Test:**
1. **Authentication Flow**
   - Login with valid credentials
   - Token refresh on 401
   - Logout and token blacklist
   - Forced logout on blacklisted token

2. **Protected Routes**
   - Access with valid token
   - Redirect on expired token
   - Proper cleanup on logout

3. **API Error Handling**
   - Rate limiting (429)
   - Server errors (500)
   - Network errors

### 4.4 Performance Tests

**Metrics to Monitor:**
1. **Bundle Size** - Should decrease after removing unused code
2. **Initial Load Time** - Should improve
3. **Redux Store Performance** - Fewer slices = better performance

---

## 5. Optional Enhancements

### 5.1 Environment Variables

#### Update `/frontend/.env.example`
```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Feature Flags (for future use)
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG_MODE=false

# Security
VITE_ENABLE_SECURITY_HEADERS_CHECK=true
```

### 5.2 Feature Flag System

#### Create `/frontend/src/utils/featureFlags.ts`
```typescript
export const features = {
  ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  DEBUG_MODE: import.meta.env.VITE_ENABLE_DEBUG_MODE === 'true',
  SECURITY_CHECK: import.meta.env.VITE_ENABLE_SECURITY_HEADERS_CHECK === 'true',
}

export const isFeatureEnabled = (feature: keyof typeof features): boolean => {
  return features[feature] ?? false
}
```

### 5.3 Improved Error Boundaries

#### Create `/frontend/src/components/ErrorBoundary.tsx`
```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            {this.state.error && this.state.error.toString()}
          </details>
        </div>
      )
    }

    return this.props.children
  }
}
```

### 5.4 Loading States

#### Create `/frontend/src/components/LoadingState.tsx`
```typescript
interface LoadingStateProps {
  isLoading: boolean
  error?: string | null
  children: ReactNode
  loadingComponent?: ReactNode
  errorComponent?: ReactNode
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  isLoading,
  error,
  children,
  loadingComponent = <LoadingSpinner />,
  errorComponent
}) => {
  if (isLoading) return <>{loadingComponent}</>
  if (error) return <>{errorComponent || <ErrorMessage message={error} />}</>
  return <>{children}</>
}
```

---

## 6. Coordination Points

### 6.1 Backend-Frontend Sync Points

1. **Before Backend Deployment**
   - Complete immediate cleanup tasks
   - Test with current backend
   - Prepare security improvements

2. **During Backend Deployment**
   - Monitor for any 404 errors on removed endpoints
   - Watch for authentication issues
   - Check CORS functionality

3. **After Backend Deployment**
   - Verify security headers
   - Test token blacklist functionality
   - Confirm rate limiting works as expected

### 6.2 Communication Protocol

**Team Sync Schedule:**
- Daily standup to review progress
- Before deployment: Final compatibility check
- During deployment: Real-time communication channel
- After deployment: Retrospective and issue tracking

**Key Stakeholders:**
- Frontend Team Lead
- Backend Team Lead
- DevOps Engineer
- QA Lead
- Product Manager

### 6.3 Rollback Plan

**Frontend Rollback Steps:**
1. Keep the removed code in a separate branch for 30 days
2. Maintain ability to quickly revert store configuration
3. Have previous build artifacts ready
4. Document any database migrations that would need reversal

---

## 7. Migration Timeline

### Phase 1: Preparation (Day 1-2)
- [ ] Create feature branch
- [ ] Complete immediate cleanup tasks
- [ ] Update tests
- [ ] Code review

### Phase 2: Testing (Day 3-4)
- [ ] Run all unit tests
- [ ] Execute integration tests
- [ ] Perform manual testing
- [ ] Load testing

### Phase 3: Staging Deployment (Day 5)
- [ ] Deploy to staging environment
- [ ] Full regression testing
- [ ] Security testing
- [ ] Performance benchmarking

### Phase 4: Production Deployment (Day 6)
- [ ] Deploy during low-traffic window
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify security headers

### Phase 5: Post-Deployment (Day 7+)
- [ ] Monitor for issues
- [ ] Gather performance data
- [ ] Document lessons learned
- [ ] Plan next improvements

---

## Appendix: Removed API Endpoints Reference

For reference, here are all 47 endpoints being removed:

### Referral Endpoints (5)
- GET `/api/referrals/dashboard/`
- POST `/api/referrals/send/`
- POST `/api/referrals/{id}/claim/`
- GET `/api/referrals/stats/`
- GET `/api/referrals/code/`

### Notification Endpoints (7)
- GET `/api/notifications/`
- PATCH `/api/notifications/{id}/`
- POST `/api/notifications/mark-all-read/`
- GET `/api/notifications/settings/`
- PATCH `/api/notifications/settings/`
- GET `/api/notifications/unread-count/`
- DELETE `/api/notifications/{id}/`

### Social Login Endpoints (15)
- GET `/api/oauth/login/{provider}/`
- GET `/api/oauth/callback/{provider}/`
- POST `/api/oauth/disconnect/{provider}/`
- GET `/api/oauth/providers/`
- GET `/api/social/auth/google/`
- GET `/api/social/auth/facebook/`
- GET `/api/social/auth/github/`
- GET `/api/social/callback/google/`
- GET `/api/social/callback/facebook/`
- GET `/api/social/callback/github/`
- POST `/api/social/disconnect/`
- GET `/api/social/connections/`
- POST `/api/social/link/`
- GET `/api/social/profile/{provider}/`
- POST `/api/social/share/`

### Share Endpoints (20)
- POST `/api/share/product/{id}/`
- POST `/api/share/category/{id}/`
- POST `/api/share/order/{id}/`
- GET `/api/share/stats/`
- POST `/api/share/track/`
- GET `/api/share/buttons/`
- POST `/api/share/email/`
- POST `/api/share/facebook/`
- POST `/api/share/twitter/`
- POST `/api/share/whatsapp/`
- POST `/api/share/linkedin/`
- POST `/api/share/pinterest/`
- GET `/api/share/link/{id}/`
- POST `/api/share/shorten/`
- GET `/api/share/analytics/`
- POST `/api/share/campaign/`
- GET `/api/share/campaign/{id}/`
- DELETE `/api/share/campaign/{id}/`
- GET `/api/share/templates/`
- POST `/api/share/custom/`

---

## Success Metrics

1. **Code Quality**
   - Reduced bundle size by ~10-15%
   - No TypeScript errors
   - 100% test coverage maintained

2. **Performance**
   - Initial load time improved by 5-10%
   - Redux store operations faster
   - Memory usage reduced

3. **Security**
   - All security headers present
   - Token blacklist working
   - No security vulnerabilities

4. **User Experience**
   - Zero user-facing errors
   - Smooth authentication flow
   - Proper error messages

---

This plan provides a comprehensive roadmap for aligning the frontend with the backend changes while improving security and performance.