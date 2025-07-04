# Phase 3: Backend Performance Optimization

## Overview
This document outlines the performance optimizations implemented in Phase 3 of the Pasargad Prints e-commerce platform.

## 1. Redis Caching Implementation

### Configuration
- **Cache Backends**: Three separate Redis databases for different purposes:
  - `default`: General purpose caching (DB 1)
  - `session`: Session storage (DB 2)
  - `api`: API response caching (DB 3)

### Features
- Automatic cache invalidation on model changes
- Cache warming for frequently accessed data
- Compressed storage for large objects
- Connection pooling for better performance

### Usage Examples
```python
from utils.cache import cache_response, get_or_set_cache, CacheKeys

# Decorator for caching function results
@cache_response(timeout=300, key_prefix='products')
def get_featured_products():
    return Product.objects.filter(is_featured=True)

# Manual cache management
cache_key = CacheKeys.PRODUCT_DETAIL.format(id=product_id)
product_data = get_or_set_cache(
    cache_key,
    lambda: ProductSerializer(product).data,
    timeout=600
)
```

## 2. Database Query Optimization

### Implemented Optimizations
- **select_related**: Used for ForeignKey relationships
- **prefetch_related**: Used for reverse ForeignKey and ManyToMany
- **Database indexes**: Added for frequently queried fields
- **Full-text search**: PostgreSQL GIN indexes for product search

### Example Optimized Queries
```python
# Before optimization
products = Product.objects.all()

# After optimization
products = Product.objects.select_related('category').prefetch_related(
    Prefetch('images', queryset=ProductImage.objects.filter(is_main=True)),
    'reviews'
).annotate(
    avg_rating=Avg('reviews__rating'),
    review_count=Count('reviews')
)
```

## 3. CDN Integration

### Configuration
- Environment variables:
  - `USE_CDN`: Enable/disable CDN
  - `CDN_URL`: Base CDN URL
  - `USE_S3`: Enable S3 for media storage
  - `AWS_*`: S3 configuration

### Features
- Automatic URL rewriting for static/media files
- S3 integration for media storage
- CloudFront support ready
- Cache headers configuration

## 4. API Rate Limiting

### Rate Limit Types
1. **Anonymous Users**: 100 requests/hour
2. **Authenticated Users**: 1000 requests/hour
3. **Burst Rate**: 20 requests/minute
4. **Sustained Rate**: 1000 requests/day

### Custom Rate Limits
```python
from utils.rate_limiting import rate_limit

@rate_limit('checkout', limit=10, period=3600)
def checkout_view(request):
    # Limited to 10 checkouts per hour
    pass
```

### IP Blocking
- Automatic blocking after 10 rate limit violations
- 24-hour block duration
- Configurable thresholds

## 5. Celery Background Tasks

### Task Queues
- `products`: Product-related tasks
- `orders`: Order processing tasks
- `payments`: Payment processing
- `cart`: Cart management
- `default`: General tasks

### Scheduled Tasks
```python
CELERY_BEAT_SCHEDULE = {
    'check-low-stock': {
        'task': 'products.tasks.check_low_stock',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-expired-sessions': {
        'task': 'utils.tasks.cleanup_expired_sessions',
        'schedule': 86400.0,  # Every day
    },
    'process-abandoned-carts': {
        'task': 'cart.tasks.process_abandoned_carts',
        'schedule': 86400.0,  # Every day
    },
}
```

### Running Celery
```bash
# Start worker
celery -A pasargad_prints worker -l info

# Start beat scheduler
celery -A pasargad_prints beat -l info

# Start worker with specific queues
celery -A pasargad_prints worker -Q products,orders -l info
```

## 6. Performance Monitoring

### Monitoring Endpoints
- `/api/utils/monitoring/system/` - System health check
- `/api/utils/monitoring/cache/` - Cache statistics
- `/api/utils/monitoring/database/` - Database performance
- `/api/utils/monitoring/cache/clear/` - Clear cache

### Metrics Tracked
- Response times
- Cache hit rates
- Slow queries
- System resources (CPU, memory, disk)
- Request patterns

## 7. Middleware Optimizations

### CacheMiddleware
- Automatic caching of GET requests
- Cache key generation based on URL and query params
- User-specific cache keys for personalized content

### PerformanceMonitoringMiddleware
- Tracks slow requests (>3 seconds)
- Logs performance metrics
- Request ID tracking

## 8. Static File Optimization

### WhiteNoise Integration
- Compressed static file serving
- Efficient caching headers
- CDN-ready configuration

### Image Optimization
- Automatic image resizing on upload
- WebP conversion support (future)
- Lazy loading implementation ready

## 9. Best Practices

### Cache Invalidation
```python
from utils.cache import invalidate_cache

# Invalidate specific patterns
invalidate_cache([
    'product_list:*',
    f'product:{product_id}',
    'featured_products'
])
```

### Query Optimization
```python
# Use only() for specific fields
products = Product.objects.only('id', 'name', 'price')

# Use defer() to exclude fields
products = Product.objects.defer('description', 'search_vector')

# Aggregate in database
from django.db.models import Count, Avg
stats = Product.objects.aggregate(
    total=Count('id'),
    avg_price=Avg('price')
)
```

## 10. Environment Variables

### Required for Production
```env
# Redis
REDIS_URL=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CDN
USE_CDN=True
CDN_URL=https://cdn.example.com

# S3 (optional)
USE_S3=True
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1
```

## Deployment Considerations

1. **Redis Setup**
   - Use Redis Sentinel or Cluster for HA
   - Configure memory limits and eviction policies
   - Enable persistence for session data

2. **Database**
   - Enable connection pooling
   - Configure read replicas for heavy read operations
   - Regular VACUUM and ANALYZE

3. **Load Balancing**
   - Sticky sessions for WebSocket support
   - Health check endpoints configured
   - Proper X-Forwarded headers

4. **Monitoring**
   - Set up alerts for high response times
   - Monitor cache hit rates
   - Track error rates and patterns

## Performance Testing

### Load Testing with Locust
```python
from locust import HttpUser, task, between

class EcommerceUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def view_products(self):
        self.client.get("/api/products/")
    
    @task(2)
    def view_product_detail(self):
        self.client.get("/api/products/1/")
    
    @task(1)
    def search_products(self):
        self.client.get("/api/products/search/?q=3d")
```

### Expected Performance Improvements
- 50-70% reduction in database queries
- 80% cache hit rate for product listings
- <100ms response time for cached endpoints
- 3x throughput increase for read operations