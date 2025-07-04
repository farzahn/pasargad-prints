# Phase 4: Analytics and Admin Features Implementation

## Overview

This document outlines the implementation of comprehensive analytics data collection, admin dashboard APIs, user behavior tracking, A/B testing framework, and reporting endpoints for the Pasargad Prints e-commerce platform.

## Implementation Summary

### 1. Analytics Data Collection

**Models Created:**
- `PageView`: Tracks page views with user agent parsing, device detection, geolocation
- `UserBehavior`: Tracks specific user interactions (clicks, searches, cart actions)
- `ProductView`: Tracks product views with source attribution and view duration
- `CartAbandonment`: Tracks cart abandonment for recovery campaigns
- `Conversion`: Tracks conversion events with attribution data

**Features:**
- Automatic page view tracking via middleware
- User agent parsing for device/browser detection
- UTM parameter tracking for attribution
- Session-based analytics for anonymous users
- GDPR-compliant data collection

### 2. Admin Dashboard API

**Dashboard Endpoints:**
- `/api/analytics/admin/dashboard/` - Main dashboard with key metrics
- `/api/analytics/admin/product-performance/` - Product analytics
- `/api/analytics/admin/customer-analytics/` - Customer insights

**Key Metrics Provided:**
- Total page views and unique visitors
- Conversion rates
- Average order value
- Cart abandonment rates
- Top performing products
- Revenue trends
- Traffic source analysis

### 3. User Behavior Tracking

**Tracking Endpoints:**
- `/api/analytics/track/page-view/` - Track page views
- `/api/analytics/track/user-behavior/` - Track user interactions
- `/api/analytics/track/product-view/` - Track product views
- `/api/analytics/track/cart-abandonment/` - Track cart abandonment
- `/api/analytics/track/conversion/` - Track conversions

**Tracked Events:**
- Page views with referrer and UTM parameters
- Product views with source attribution
- Add to cart / Remove from cart actions
- Search queries and filters
- Form submissions
- Error tracking
- Checkout process tracking

### 4. A/B Testing Framework

**Models:**
- `ABTestExperiment`: Define A/B test experiments
- `ABTestParticipant`: Track user participation in tests

**API Endpoints:**
- `/api/analytics/ab-test/get-variant/` - Get user's A/B test variant
- `/api/analytics/ab-test/record-conversion/` - Record A/B test conversions
- `/api/analytics/admin/ab-experiments/` - Admin CRUD for experiments

**Features:**
- Consistent variant assignment using hashing
- Traffic percentage control
- Multiple variant support
- Conversion tracking with value attribution
- Statistical results calculation

### 5. Reporting System

**Report Types:**
- Sales reports with revenue analysis
- Inventory reports with stock alerts
- Customer behavior reports
- Product performance reports
- Marketing attribution reports
- Financial reports

**Features:**
- JSON data export
- PDF report generation (when ReportLab is available)
- Scheduled report generation
- Custom date ranges
- Report caching and history

## Technical Architecture

### Database Design

The analytics system uses PostgreSQL with optimized indexes for performance:

```sql
-- Page Views indexes
CREATE INDEX analytics_page_views_timestamp ON analytics_page_views(timestamp);
CREATE INDEX analytics_page_views_user ON analytics_page_views(user_id);
CREATE INDEX analytics_page_views_session ON analytics_page_views(session_id);

-- User Behavior indexes
CREATE INDEX analytics_user_behavior_timestamp ON analytics_user_behavior(timestamp);
CREATE INDEX analytics_user_behavior_event_type ON analytics_user_behavior(event_type);

-- Product Views indexes
CREATE INDEX analytics_product_views_product ON analytics_product_views(product_id);
CREATE INDEX analytics_product_views_timestamp ON analytics_product_views(timestamp);
```

### Middleware Integration

The `AnalyticsMiddleware` automatically tracks page views for all requests:

```python
# Add to MIDDLEWARE in settings.py
'analytics.middleware.AnalyticsMiddleware',
```

**Features:**
- Automatic page view tracking
- UTM parameter extraction and storage
- User agent parsing
- IP address collection
- Session management

### Performance Considerations

1. **Asynchronous Processing**: Analytics data collection is designed to be non-blocking
2. **Database Indexes**: Optimized indexes for common query patterns
3. **Data Aggregation**: Pre-calculated metrics for dashboard performance
4. **Caching**: Report caching to reduce database load
5. **Batch Processing**: Bulk analytics data processing capabilities

## API Documentation

### Analytics Tracking APIs

#### Track Page View
```http
POST /api/analytics/track/page-view/
Content-Type: application/json

{
    "page_url": "https://example.com/products/",
    "page_title": "Products - Pasargad Prints",
    "referrer": "https://google.com",
    "session_id": "abc123"
}
```

#### Track User Behavior
```http
POST /api/analytics/track/user-behavior/
Content-Type: application/json

{
    "event_type": "add_to_cart",
    "event_name": "Product Added to Cart",
    "event_data": {
        "product_id": 123,
        "quantity": 2,
        "price": 29.99
    },
    "page_url": "https://example.com/products/123/",
    "session_id": "abc123"
}
```

#### Track Product View
```http
POST /api/analytics/track/product-view/
Content-Type: application/json

{
    "product": 123,
    "view_duration": 45,
    "source": "search",
    "session_id": "abc123"
}
```

### Admin Dashboard APIs

#### Get Dashboard Metrics
```http
GET /api/analytics/admin/dashboard/?days=30
Authorization: Bearer <admin_token>
```

Response:
```json
{
    "total_page_views": 15432,
    "unique_visitors": 3421,
    "conversion_rate": 2.3,
    "average_order_value": 85.50,
    "cart_abandonment_rate": 68.2,
    "top_products": [...],
    "revenue_by_day": [...],
    "traffic_sources": {...}
}
```

### A/B Testing APIs

#### Get A/B Test Variant
```http
POST /api/analytics/ab-test/get-variant/
Content-Type: application/json

{
    "feature": "checkout_button_color",
    "session_id": "abc123"
}
```

Response:
```json
{
    "variant": "blue",
    "experiment_id": 5
}
```

#### Record A/B Test Conversion
```http
POST /api/analytics/ab-test/record-conversion/
Content-Type: application/json

{
    "experiment_id": 5,
    "conversion_value": 85.50,
    "conversion_data": {
        "order_id": 1234
    },
    "session_id": "abc123"
}
```

## Installation and Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `user-agents==2.2.0` - User agent parsing
- `reportlab==4.0.8` - PDF report generation
- `django-filter==23.5` - Advanced filtering

### 2. Database Migration

```bash
python manage.py makemigrations analytics
python manage.py migrate
```

### 3. Settings Configuration

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... other apps
    'analytics',
]
```

Add to `MIDDLEWARE`:
```python
MIDDLEWARE = [
    # ... other middleware
    'analytics.middleware.AnalyticsMiddleware',
]
```

### 4. URL Configuration

The analytics URLs are automatically included:
```python
path('api/analytics/', include('analytics.urls')),
```

## Usage Examples

### Frontend Integration

#### Track Page Views (Automatic)
Page views are automatically tracked by the middleware. No frontend code required.

#### Track User Interactions
```javascript
// Track button clicks
function trackUserAction(eventType, eventName, eventData) {
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
            page_url: window.location.href,
            session_id: getSessionId()
        })
    });
}

// Example usage
document.getElementById('add-to-cart').addEventListener('click', function() {
    trackUserAction('add_to_cart', 'Product Added to Cart', {
        product_id: productId,
        quantity: quantity,
        price: price
    });
});
```

#### A/B Testing Integration
```javascript
// Get A/B test variant
async function getABTestVariant(feature) {
    const response = await fetch('/api/analytics/ab-test/get-variant/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            feature: feature,
            session_id: getSessionId()
        })
    });
    return response.json();
}

// Example usage
const checkoutVariant = await getABTestVariant('checkout_button_color');
if (checkoutVariant.variant === 'blue') {
    document.getElementById('checkout-btn').className += ' btn-blue';
} else {
    document.getElementById('checkout-btn').className += ' btn-red';
}
```

## Admin Interface

The Django admin interface provides comprehensive management of analytics data:

### Available Admin Views:
- **Page Views**: View and filter page view data
- **User Behavior**: Track user interactions and events
- **Product Views**: Monitor product engagement
- **Cart Abandonment**: Manage cart recovery campaigns
- **Conversions**: View conversion tracking data
- **A/B Test Experiments**: Create and manage A/B tests
- **Reports**: View generated reports and download PDFs

### Admin Actions:
- Send cart recovery emails
- Mark cart abandonments as recovered
- Activate/deactivate A/B test experiments
- Generate and download reports

## Security and Privacy

### GDPR Compliance:
- User data anonymization options
- Data retention policies
- User consent tracking
- Right to be forgotten implementation

### Security Measures:
- IP address hashing for privacy
- Admin-only access to sensitive data
- Rate limiting on tracking endpoints
- Input validation and sanitization

## Performance Monitoring

### Database Performance:
- Optimized indexes for common queries
- Periodic data archiving for old analytics data
- Query optimization for dashboard metrics

### Caching Strategy:
- Dashboard metrics caching (15 minutes)
- Report result caching (1 hour)
- A/B test variant caching per session

## Future Enhancements

### Planned Features:
1. Real-time analytics dashboard
2. Advanced segmentation capabilities
3. Cohort analysis
4. Funnel analysis
5. Machine learning recommendations
6. Export to external analytics platforms
7. Custom event tracking
8. Mobile app analytics integration

### Integration Opportunities:
- Google Analytics integration
- Facebook Pixel integration
- Email marketing platform integration
- Customer support system integration

## Troubleshooting

### Common Issues:

1. **Missing Dependencies**: Install user-agents and reportlab packages
2. **Migration Errors**: Ensure all foreign key dependencies are migrated first
3. **Performance Issues**: Check database indexes and consider data archiving
4. **Session Tracking**: Ensure session middleware is properly configured

### Debug Settings:
```python
# Enable analytics debugging
LOGGING = {
    'loggers': {
        'analytics': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Conclusion

The Phase 4 analytics implementation provides a comprehensive foundation for data-driven decision making in the Pasargad Prints e-commerce platform. The system is designed to be scalable, performant, and privacy-compliant while providing rich insights into user behavior and business performance.

The modular architecture allows for easy extension and integration with external analytics platforms, making it a robust solution for current and future analytics needs.