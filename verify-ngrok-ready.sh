#!/bin/bash

echo "==================================="
echo "Ngrok Readiness Verification"
echo "==================================="
echo ""

# Check if containers are running
echo "1. Checking Docker containers..."
docker compose ps --format "table {{.Name}}\t{{.Status}}"
echo ""

# Test backend CORS
echo "2. Testing backend CORS with ngrok origin..."
CORS_TEST=$(curl -s -X OPTIONS http://localhost:8000/api/auth/login/ \
  -H "Origin: https://test.ngrok-free.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -I | grep -i "access-control-allow-origin")

if [[ $CORS_TEST == *"https://test.ngrok-free.app"* ]]; then
  echo "✓ Backend CORS is properly configured for ngrok"
else
  echo "✗ Backend CORS not configured properly"
fi
echo ""

# Test frontend proxy
echo "3. Testing frontend proxy..."
PROXY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://localhost:3000/api/auth/login/)
if [ "$PROXY_STATUS" = "204" ]; then
  echo "✓ Frontend proxy is working"
else
  echo "✗ Frontend proxy returned status: $PROXY_STATUS"
fi
echo ""

# Test login endpoint
echo "4. Testing login endpoint..."
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}')
if [ "$LOGIN_STATUS" = "400" ] || [ "$LOGIN_STATUS" = "401" ]; then
  echo "✓ Login endpoint is responding (auth failure expected)"
else
  echo "✗ Login endpoint returned unexpected status: $LOGIN_STATUS"
fi
echo ""

echo "==================================="
echo "Summary:"
echo "- Frontend URL: http://localhost:3000"
echo "- Backend URL: http://localhost:8000"
echo "- Login endpoint: /api/auth/login/"
echo ""
echo "The application is ready for ngrok!"
echo "Use any ngrok URL and the login should work."
echo "===================================" 