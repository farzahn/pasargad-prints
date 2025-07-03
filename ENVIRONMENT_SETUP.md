# Environment Variable Configuration

This document explains how to properly configure environment variables for the Pasargad Prints application.

## Frontend Environment Variables

### VITE_API_URL

**IMPORTANT**: The `VITE_API_URL` should be set to the base URL of your backend API **WITHOUT** the `/api` suffix.

The frontend code automatically appends `/api` to all API endpoints, so including it in the environment variable will cause double `/api` paths (e.g., `/api/api/users/auth/login/`).

### Correct Configuration Examples:

#### Local Development (.env)
```bash
VITE_API_URL=http://localhost:8000
```

#### Docker Compose
```yaml
environment:
  - VITE_API_URL=http://backend:8000
```

#### ngrok Deployment (.env.ngrok)
```bash
VITE_API_URL=https://your-backend-url.ngrok-free.app
```

### Incorrect Configuration (DO NOT USE):
```bash
# Wrong - will cause double /api in URLs
VITE_API_URL=http://localhost:8000/api
VITE_API_URL=/api
```

## Using Different Environment Files

For different deployment scenarios, you can use different .env files:

1. **Local Development**: Use `.env`
2. **ngrok Deployment**: Copy `.env.ngrok` to `.env` and update the URL
3. **Production**: Create `.env.production` with production URLs

To use a specific environment file:
```bash
# Copy the ngrok config
cp .env.ngrok .env

# Update the ngrok URL in .env
# Replace YOUR_NGROK_URL with your actual ngrok URL
```

## Backend URL Structure

The backend Django application serves all API endpoints under the `/api` prefix:
- Authentication: `/api/users/auth/`
- Products: `/api/products/`
- Cart: `/api/cart/`
- Orders: `/api/orders/`
- Payments: `/api/payments/`

The frontend automatically prepends the VITE_API_URL and appends the endpoint path, so:
- `VITE_API_URL` = `http://localhost:8000`
- API call to `/api/users/auth/login/`
- Full URL = `http://localhost:8000/api/users/auth/login/`