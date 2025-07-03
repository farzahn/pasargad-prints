# Ngrok Login Fix Documentation

## Problem
The application was not working properly when accessed through ngrok tunnels because:
1. The frontend was trying to make API calls to hardcoded URLs instead of relative paths
2. CORS settings were configured for specific ngrok URLs instead of allowing any ngrok subdomain

## Solution Applied

### 1. Frontend Configuration (Already in place)
- **File**: `/frontend/src/services/apiConfig.ts`
- **Change**: Uses relative URLs when `VITE_API_URL` environment variable is empty
- **Docker Compose**: Sets `VITE_API_URL=` (empty string) in the frontend service

This allows the frontend to make API calls relative to its current domain, which works seamlessly with ngrok tunnels.

### 2. Backend CORS Configuration (Updated)
- **File**: `/backend/pasargad_prints/settings.py`
- **Changes**:
  - Added `CORS_ALLOWED_ORIGIN_REGEXES` to allow any ngrok subdomain:
    ```python
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://.*\.ngrok-free\.app$",
        r"^https://.*\.ngrok\.io$",
    ]
    ```
  - Updated `ALLOWED_HOSTS` to include wildcard domains:
    ```python
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '10.100.100.118', '.ngrok-free.app', '.ngrok.io']
    ```

### 3. How It Works
1. When accessing the app through ngrok (e.g., `https://xyz.ngrok-free.app`):
   - Frontend loads from the ngrok URL
   - Frontend makes API calls to `/api/*` (relative paths)
   - These requests go through the same ngrok tunnel to the backend
   - Backend accepts the requests due to wildcard CORS and ALLOWED_HOSTS settings

2. The frontend container's Vite dev server proxies `/api/*` requests to the backend container

### 4. Testing
A test script was created at `/test-login-endpoint.js` to verify:
- Backend API is accessible on port 8000
- Frontend proxy is working on port 3000
- Login endpoint responds correctly

Run the test with: `node test-login-endpoint.js`

### 5. Container Restarts
Both frontend and backend containers were restarted to apply the changes:
```bash
docker compose restart frontend
docker compose restart backend
```

## Result
The application now works correctly when accessed through any ngrok URL without requiring configuration changes. Users can log in and use all features through the ngrok tunnel.

## For Future Reference
- Always use relative API URLs in frontend when possible
- Use regex patterns for CORS when dealing with dynamic subdomains
- Test with the provided script to verify connectivity