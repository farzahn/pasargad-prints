# Order Management API Documentation

## Overview
The Order Management API provides endpoints for managing e-commerce orders, including listing, viewing details, tracking, and status updates.

## Authentication
All endpoints except order tracking require JWT authentication.

## Endpoints

### 1. List Orders
**GET** `/api/orders/`

Lists all orders for the authenticated user. Admin users see all orders.

**Query Parameters:**
- `status` - Filter by order status (pending, processing, shipped, delivered, cancelled, refunded)
- `fulfillment_method` - Filter by fulfillment method (shipping, pickup)
- `search` - Search by order number, recipient name, or email
- `ordering` - Sort results (created_at, -created_at, total_amount, -total_amount)
- `page` - Page number
- `page_size` - Items per page (default: 10, max: 100)
- `created_after` - Filter orders created after date (YYYY-MM-DD)
- `created_before` - Filter orders created before date (YYYY-MM-DD)
- `min_total` - Minimum order total
- `max_total` - Maximum order total

**Response:**
```json
{
  "count": 10,
  "next": "http://api.example.com/orders/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_number": "A1B2C3D4E5F6",
      "status": "processing",
      "status_display": "Processing",
      "fulfillment_method": "shipping",
      "total_amount": "37.39",
      "total_items": 2,
      "tracking_number": "",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### 2. Order Details
**GET** `/api/orders/{id}/`

Get detailed information about a specific order.

**Response:**
```json
{
  "id": 1,
  "order_number": "A1B2C3D4E5F6",
  "status": "processing",
  "status_display": "Processing",
  "fulfillment_method": "shipping",
  "fulfillment_display": "Shipping",
  "subtotal": "29.99",
  "tax_amount": "2.40",
  "shipping_cost": "5.00",
  "total_amount": "37.39",
  "shipping_name": "John Doe",
  "shipping_email": "john@example.com",
  "shipping_phone": "+1234567890",
  "shipping_address": "123 Main St",
  "shipping_city": "New York",
  "shipping_state": "NY",
  "shipping_postal_code": "10001",
  "shipping_country": "US",
  "billing_name": "John Doe",
  "billing_email": "john@example.com",
  "billing_address": "123 Main St",
  "billing_city": "New York",
  "billing_state": "NY",
  "billing_postal_code": "10001",
  "billing_country": "US",
  "tracking_number": "",
  "shipstation_order_id": "",
  "estimated_delivery": null,
  "total_items": 1,
  "total_weight": "1.5",
  "items": [
    {
      "id": 1,
      "product": 1,
      "product_name": "Test Product",
      "product_sku": "TEST001",
      "product_weight": "1.5",
      "product_image": "http://api.example.com/media/products/test.jpg",
      "quantity": 1,
      "unit_price": "29.99",
      "total_price": "29.99",
      "total_weight": "1.5"
    }
  ],
  "status_history": [
    {
      "id": 1,
      "status": "processing",
      "notes": "Order confirmed",
      "created_at": "2024-01-01T10:00:00Z",
      "created_by": 1,
      "created_by_name": "Admin User"
    }
  ],
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "shipped_at": null,
  "delivered_at": null
}
```

### 3. Public Order Tracking
**GET** `/api/orders/track/{tracking_number}/`

Track an order by tracking number. No authentication required.

**Response:**
```json
{
  "order_number": "A1B2C3D4E5F6",
  "status": "shipped",
  "status_display": "Shipped",
  "tracking_number": "PP1234567890",
  "estimated_delivery": "2024-01-05",
  "created_at": "2024-01-01T10:00:00Z",
  "shipped_at": "2024-01-02T14:30:00Z",
  "delivered_at": null,
  "items": [
    {
      "product_name": "Test Product",
      "quantity": 1
    }
  ]
}
```

### 4. Update Order Status (Admin Only)
**PATCH** `/api/orders/{id}/status/`

Update the status of an order. Creates status history entry.

**Request Body:**
```json
{
  "status": "shipped",
  "notes": "Package shipped via USPS"
}
```

**Valid Status Transitions:**
- pending → processing, cancelled
- processing → shipped, cancelled
- shipped → delivered, cancelled
- delivered → refunded
- cancelled → pending (reactivate)
- refunded → (terminal state)

**Response:**
Returns the full order details with updated status.

### 5. Order Statistics (Admin Only)
**GET** `/api/orders/statistics/`

Get aggregate statistics about orders.

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
```json
{
  "total_orders": 150,
  "total_revenue": "15750.50",
  "average_order_value": "105.00",
  "orders_by_status": [
    {"status": "delivered", "count": 100},
    {"status": "processing", "count": 30},
    {"status": "shipped", "count": 20}
  ],
  "orders_by_day": [
    {"day": "2024-01-01", "count": 5},
    {"day": "2024-01-02", "count": 8}
  ]
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 400 Bad Request
```json
{
  "status": ["Cannot transition from 'pending' to 'delivered'"]
}
```

## Testing with cURL

### Get Orders (with JWT token)
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/orders/
```

### Track Order (no auth required)
```bash
curl http://localhost:8000/api/orders/track/PP1234567890/
```

### Update Order Status (admin only)
```bash
curl -X PATCH \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "shipped", "notes": "Shipped via FedEx"}' \
  http://localhost:8000/api/orders/1/status/
```