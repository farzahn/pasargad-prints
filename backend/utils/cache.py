from django.core.cache import cache, caches
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class CacheKeys:
    """Centralized cache key management"""
    PRODUCT_LIST = 'product_list:{filters}'
    PRODUCT_DETAIL = 'product:{id}'
    CATEGORY_LIST = 'category_list'
    CATEGORY_PRODUCTS = 'category:{id}:products'
    USER_CART = 'user:{user_id}:cart'
    USER_WISHLIST = 'user:{user_id}:wishlist'
    USER_RECOMMENDATIONS = 'user:{user_id}:recommendations'
    FEATURED_PRODUCTS = 'featured_products'
    PROMOTION_ACTIVE = 'promotions:active'
    ORDER_STATS = 'order_stats:{period}'
    
    @staticmethod
    def get_product_list_key(**filters):
        """Generate cache key for product list with filters"""
        sorted_filters = sorted(filters.items())
        filter_string = json.dumps(sorted_filters)
        return CacheKeys.PRODUCT_LIST.format(
            filters=hashlib.md5(filter_string.encode()).hexdigest()
        )

def cache_response(timeout=300, key_prefix='', cache_alias='default'):
    """
    Decorator to cache function responses
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        cache_alias: Cache backend to use
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args[1:])}"
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                kwargs_str = json.dumps(sorted_kwargs)
                cache_key += f":{hashlib.md5(kwargs_str.encode()).hexdigest()}"
            
            # Try to get from cache
            cache_backend = caches[cache_alias]
            result = cache_backend.get(cache_key)
            
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_backend.set(cache_key, result, timeout)
            logger.debug(f"Cache miss and set for key: {cache_key}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(patterns):
    """
    Invalidate cache entries matching patterns
    
    Args:
        patterns: List of cache key patterns to invalidate
    """
    from django.conf import settings
    
    for pattern in patterns:
        if '*' in pattern:
            # Check if we're using Redis cache
            try:
                if hasattr(cache._cache, 'get_client') and settings.USE_REDIS_CACHE:
                    # Use Redis pattern matching for wildcard invalidation
                    cache._cache.get_client().delete_pattern(pattern)
                else:
                    # For local memory cache, clear all cache
                    cache.clear()
            except (AttributeError, ImportError):
                # Fallback: clear all cache for local memory cache
                cache.clear()
        else:
            cache.delete(pattern)
    logger.info(f"Invalidated cache for patterns: {patterns}")

def get_or_set_cache(key, func, timeout=300, cache_alias='default'):
    """
    Get value from cache or set it using the provided function
    
    Args:
        key: Cache key
        func: Function to call if cache miss
        timeout: Cache timeout in seconds
        cache_alias: Cache backend to use
    """
    cache_backend = caches[cache_alias]
    value = cache_backend.get(key)
    
    if value is None:
        value = func()
        cache_backend.set(key, value, timeout)
        logger.debug(f"Cache miss and set for key: {key}")
    else:
        logger.debug(f"Cache hit for key: {key}")
    
    return value

class CacheMixin:
    """Mixin for viewsets to add caching capabilities"""
    cache_timeout = 300
    cache_key_prefix = ''
    cache_alias = 'api'
    
    def get_cache_key(self, **kwargs):
        """Generate cache key for the view"""
        key_parts = [
            self.cache_key_prefix or self.__class__.__name__,
            self.request.method,
            self.request.path,
        ]
        
        # Add query parameters to key
        query_params = self.request.query_params.dict()
        if query_params:
            sorted_params = sorted(query_params.items())
            params_str = json.dumps(sorted_params)
            key_parts.append(hashlib.md5(params_str.encode()).hexdigest())
        
        # Add additional kwargs
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest())
        
        return ':'.join(key_parts)
    
    def get_cached_response(self):
        """Try to get cached response"""
        cache_key = self.get_cache_key()
        cache_backend = caches[self.cache_alias]
        return cache_backend.get(cache_key)
    
    def set_cached_response(self, response):
        """Cache the response"""
        cache_key = self.get_cache_key()
        cache_backend = caches[self.cache_alias]
        cache_backend.set(cache_key, response.data, self.cache_timeout)
        return response

# Cache invalidation signals
def invalidate_product_cache(product_id=None, category_id=None):
    """Invalidate product-related caches"""
    patterns = ['product_list:*', 'featured_products']
    
    if product_id:
        patterns.append(f'product:{product_id}')
        patterns.append(f'product:{product_id}:*')
    
    if category_id:
        patterns.append(f'category:{category_id}:products')
    
    invalidate_cache(patterns)

def invalidate_user_cache(user_id):
    """Invalidate user-related caches"""
    patterns = [
        f'user:{user_id}:cart',
        f'user:{user_id}:wishlist',
        f'user:{user_id}:recommendations',
        f'user:{user_id}:*'
    ]
    invalidate_cache(patterns)