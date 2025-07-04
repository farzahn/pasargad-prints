# Analytics API Documentation

## Base URL
All analytics endpoints are prefixed with `/api/analytics/`

## Authentication
- Public tracking endpoints: No authentication required
- Admin endpoints: Require admin authentication (IsAdminUser permission)
- A/B testing endpoints: No authentication required (public)

## Tracking Endpoints

### 1. Track Page View
Track when a user visits a page.

**Endpoint:** `POST /api/analytics/track/page-view/`

**Request Body:**
```json
{
    "page_url": "https://example.com/products/",
    "page_title": "Products - Pasargad Prints",
    "referrer": "https://google.com"
}
```

**Response:** `201 Created`
```json
{
    "id": 123,
    "page_url": "https://example.com/products/",
    "page_title": "Products - Pasargad Prints",
    "timestamp": "2023-12-01T10:30:00Z"
}
```

### 2. Track User Behavior
Track specific user interactions and events.

**Endpoint:** `POST /api/analytics/track/user-behavior/`

**Event Types:**
- `click` - Button/link clicks
- `scroll` - Page scrolling
- `search` - Search queries
- `filter` - Filter applications
- `add_to_cart` - Add product to cart
- `remove_from_cart` - Remove product from cart
- `checkout_start` - Begin checkout process
- `checkout_complete` - Complete checkout
- `form_submit` - Form submissions
- `error` - Error occurrences
- `custom` - Custom events

**Request Body:**
```json
{
    "event_type": "add_to_cart",
    "event_name": "Product Added to Cart",
    "event_data": {
        "product_id": 123,
        "quantity": 2,
        "price": 29.99
    },
    "page_url": "https://example.com/products/123/"
}
```

**Response:** `201 Created`

### 3. Track Product View
Track when a user views a specific product.

**Endpoint:** `POST /api/analytics/track/product-view/`

**Request Body:**
```json
{
    "product": 123,
    "view_duration": 45,
    "source": "search"
}
```

**Response:** `201 Created`

### 4. Track Cart Abandonment
Track when a user abandons their cart.

**Endpoint:** `POST /api/analytics/track/cart-abandonment/`

**Request Body:** (Empty - automatically detects cart from session)
```json
{}
```

**Response:** `200 OK`
```json
{
    "message": "Cart abandonment tracked"
}
```

### 5. Track Conversion
Track when an order is completed.

**Endpoint:** `POST /api/analytics/track/conversion/`

**Request Body:**
```json
{
    "order_id": 1234,
    "source": "google",
    "medium": "organic",
    "campaign": "winter_sale"
}
```

**Response:** `200 OK`
```json
{
    "message": "Conversion tracked"
}
```

## A/B Testing Endpoints

### 1. Get A/B Test Variant
Get the assigned variant for a user in an A/B test.

**Endpoint:** `POST /api/analytics/ab-test/get-variant/`

**Request Body:**
```json
{
    "feature": "checkout_button_color"
}
```

**Response:** `200 OK`
```json
{
    "variant": "blue",
    "experiment_id": 5
}
```

### 2. Record A/B Test Conversion
Record a conversion for an A/B test participant.

**Endpoint:** `POST /api/analytics/ab-test/record-conversion/`

**Request Body:**
```json
{
    "experiment_id": 5,
    "conversion_value": 85.50,
    "conversion_data": {
        "order_id": 1234
    }
}
```

**Response:** `200 OK`
```json
{
    "message": "Conversion recorded"
}
```

## Admin Dashboard Endpoints

### 1. Dashboard Metrics
Get main dashboard metrics.

**Endpoint:** `GET /api/analytics/admin/dashboard/`

**Query Parameters:**
- `days` (optional): Number of days to include (default: 30)

**Response:** `200 OK`
```json
{
    "total_page_views": 15432,
    "unique_visitors": 3421,
    "conversion_rate": 2.3,
    "average_order_value": 85.50,
    "cart_abandonment_rate": 68.2,
    "top_products": [
        {
            "product__id": 123,
            "product__name": "Sample Product",
            "total_sold": 45,
            "revenue": 1350.00
        }
    ],
    "revenue_by_day": [
        {
            "day": "2023-12-01",
            "revenue": 1250.00
        }
    ],
    "traffic_sources": {
        "google": 120,
        "facebook": 80,
        "direct": 200
    }
}
```

### 2. Product Performance
Get product performance analytics.

**Endpoint:** `GET /api/analytics/admin/product-performance/`

**Query Parameters:**
- `days` (optional): Number of days to include (default: 30)

**Response:** `200 OK`
```json
[
    {
        "product_id": 123,
        "product_name": "Sample Product",
        "views": 1250,
        "add_to_cart_rate": 15.2,
        "conversion_rate": 3.4,
        "revenue": 2850.00,
        "average_view_duration": 42.5
    }
]
```

### 3. Customer Analytics
Get customer behavior analytics.

**Endpoint:** `GET /api/analytics/admin/customer-analytics/`

**Query Parameters:**
- `days` (optional): Number of days to include (default: 365)

**Response:** `200 OK`
```json
[
    {
        "customer_id": 456,
        "customer_email": "customer@example.com",
        "total_orders": 5,
        "lifetime_value": 425.00,
        "average_order_value": 85.00,
        "last_order_date": "2023-11-28T15:30:00Z",
        "favorite_categories": ["Electronics", "Clothing"]
    }
]
```

## Report Generation Endpoints

### 1. Generate Report
Generate a business report.

**Endpoint:** `POST /api/analytics/admin/reports/generate/`

**Report Types:**
- `sales` - Sales performance report
- `inventory` - Inventory status report
- `customer` - Customer behavior report
- `product` - Product performance report
- `marketing` - Marketing attribution report
- `financial` - Financial summary report

**Request Body:**
```json
{
    "report_type": "sales",
    "parameters": {
        "start_date": "2023-11-01T00:00:00Z",
        "end_date": "2023-11-30T23:59:59Z"
    },
    "generate_pdf": true
}
```

**Response:** `201 Created`
```json
{
    "id": 789,
    "report_type": "sales",
    "name": "Sales Report - 2023-12-01",
    "generated_at": "2023-12-01T10:30:00Z",
    "file_path": "/media/reports/sales_report_20231201_103000.pdf",
    "data": {
        "total_orders": 156,
        "total_revenue": 13250.00,
        "average_order_value": 84.94
    }
}
```

### 2. List Reports
List all generated reports.

**Endpoint:** `GET /api/analytics/admin/reports/`

**Query Parameters:**
- `report_type` (optional): Filter by report type

**Response:** `200 OK`
```json
[
    {
        "id": 789,
        "name": "Sales Report - 2023-12-01",
        "report_type": "sales",
        "generated_by_username": "admin",
        "generated_at": "2023-12-01T10:30:00Z"
    }
]
```

## Admin Data Management Endpoints

### 1. Page Views (Read-only)
**Endpoint:** `GET /api/analytics/admin/page-views/`

**Query Parameters:**
- Filtering: `user`, `page_url`, `device_type`, `browser`
- Ordering: `timestamp`
- Search: `page_url`, `user__username`, `user__email`

### 2. User Behavior (Read-only)
**Endpoint:** `GET /api/analytics/admin/user-behavior/`

**Query Parameters:**
- Filtering: `user`, `event_type`, `session_id`
- Ordering: `timestamp`
- Search: `event_name`, `user__username`, `user__email`

### 3. Cart Abandonment
**Endpoint:** `GET /api/analytics/admin/cart-abandonment/`

**Special Actions:**
- `POST /api/analytics/admin/cart-abandonment/{id}/send_recovery_email/`

### 4. A/B Test Experiments
**Endpoint:** `GET/POST/PUT/DELETE /api/analytics/admin/ab-experiments/`

**Special Actions:**
- `POST /api/analytics/admin/ab-experiments/{id}/activate/`
- `POST /api/analytics/admin/ab-experiments/{id}/deactivate/`
- `GET /api/analytics/admin/ab-experiments/{id}/results/`

## Error Responses

### 400 Bad Request
```json
{
    "error": "Invalid data provided",
    "details": {
        "field_name": ["This field is required."]
    }
}
```

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
    "error": "Resource not found"
}
```

## Rate Limiting

Public tracking endpoints are rate limited to prevent abuse:
- Anonymous users: 100 requests per hour
- Authenticated users: 1000 requests per hour

## Privacy and GDPR

- All tracking respects user privacy settings
- IP addresses can be hashed for anonymization
- Data retention policies are configurable
- Users can request data deletion

## Frontend Integration Examples

### JavaScript Tracking
```javascript
// Initialize analytics
const analytics = {
    track: async (endpoint, data) => {
        try {
            await fetch(`/api/analytics/${endpoint}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
        } catch (error) {
            console.error('Analytics tracking error:', error);
        }
    }
};

// Track user actions
analytics.track('track/user-behavior', {
    event_type: 'click',
    event_name: 'Header Logo Click',
    page_url: window.location.href
});

// Track product views
analytics.track('track/product-view', {
    product: productId,
    source: 'category_page'
});
```

### React Hook Example
```javascript
import { useEffect } from 'react';

const useAnalytics = () => {
    const trackEvent = (eventType, eventName, eventData = {}) => {
        fetch('/api/analytics/track/user-behavior/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                event_type: eventType,
                event_name: eventName,
                event_data: eventData,
                page_url: window.location.href
            })
        }).catch(console.error);
    };

    return { trackEvent };
};

// Usage in component
const ProductCard = ({ product }) => {
    const { trackEvent } = useAnalytics();

    const handleAddToCart = () => {
        trackEvent('add_to_cart', 'Product Added to Cart', {
            product_id: product.id,
            price: product.price
        });
    };

    return (
        <button onClick={handleAddToCart}>
            Add to Cart
        </button>
    );
};
```