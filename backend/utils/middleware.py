"""
Custom middleware for error handling, logging, and monitoring
"""
import logging
import time
import json
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.cache import get_cache_key
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and responses with performance monitoring
    """
    
    SLOW_REQUEST_THRESHOLD = 3.0  # seconds
    
    def process_request(self, request):
        # Generate unique request ID
        request.id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request started: {request.id} - {request.method} {request.path}",
            extra={
                'request_id': request.id,
                'method': request.method,
                'path': request.path,
                'user': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                'ip': self._get_client_ip(request),
            }
        )
        
        return None
    
    def process_response(self, request, response):
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0
        
        # Log slow requests with warning
        if duration > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow request detected: {getattr(request, 'id', 'unknown')} - "
                f"{request.method} {request.path} - Status: {response.status_code} - "
                f"Duration: {duration:.3f}s",
                extra={
                    'request_id': getattr(request, 'id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                }
            )
        else:
            # Log normal response
            logger.info(
                f"Request completed: {getattr(request, 'id', 'unknown')} - "
                f"{request.method} {request.path} - Status: {response.status_code} - "
                f"Duration: {duration:.3f}s",
                extra={
                    'request_id': getattr(request, 'id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                }
            )
        
        # Add request ID and performance headers
        if hasattr(request, 'id'):
            response['X-Request-ID'] = request.id
        response['X-Response-Time'] = f"{duration:.3f}"
        
        return response
    
    def process_exception(self, request, exception):
        # Log exception details
        logger.error(
            f"Request failed: {getattr(request, 'id', 'unknown')} - "
            f"{request.method} {request.path} - Exception: {str(exception)}",
            exc_info=True,
            extra={
                'request_id': getattr(request, 'id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'user': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            }
        )
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses
    """
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for additional XSS protection
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://www.google-analytics.com https://www.googletagmanager.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com https://www.google-analytics.com https://analytics.google.com https://api.goshippo.com; "
                "frame-src https://js.stripe.com https://hooks.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests;"
            )
        
        return response


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware to handle unexpected errors gracefully
    """
    
    def process_exception(self, request, exception):
        # Don't handle exceptions in DEBUG mode
        if settings.DEBUG:
            return None
        
        # Log the exception
        logger.error(
            f"Unhandled exception in {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'request_id': getattr(request, 'id', 'unknown'),
                'method': request.method,
                'path': request.path,
            }
        )
        
        # Return generic error response
        return JsonResponse({
            'error': True,
            'message': 'An unexpected error occurred. Please try again later.',
            'request_id': getattr(request, 'id', 'unknown'),
        }, status=500)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor performance and log slow requests
    """
    
    SLOW_REQUEST_THRESHOLD = 3.0  # seconds
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests
            if duration > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} - "
                    f"Duration: {duration:.3f}s",
                    extra={
                        'request_id': getattr(request, 'id', 'unknown'),
                        'method': request.method,
                        'path': request.path,
                        'duration': duration,
                        'status_code': response.status_code,
                    }
                )
        
        return response


class CacheMiddleware(MiddlewareMixin):
    """
    Middleware for API response caching
    """
    
    CACHE_METHODS = ['GET', 'HEAD']
    CACHE_PATHS = [
        '/api/products/',
        '/api/categories/',
        '/api/promotions/',
    ]
    
    def should_cache(self, request):
        """Determine if request should be cached"""
        if request.method not in self.CACHE_METHODS:
            return False
        
        # Check if path should be cached
        for path in self.CACHE_PATHS:
            if request.path.startswith(path):
                return True
        
        return False
    
    def get_cache_key(self, request):
        """Generate cache key for request"""
        key_parts = [
            'api_cache',
            request.method,
            request.path,
        ]
        
        # Add query parameters
        query_params = request.GET.dict()
        if query_params:
            sorted_params = sorted(query_params.items())
            key_parts.append(str(sorted_params))
        
        # Add user ID for personalized content
        if hasattr(request, 'user') and request.user.is_authenticated:
            key_parts.append(f'user_{request.user.id}')
        
        return ':'.join(key_parts)
    
    def process_request(self, request):
        """Try to serve from cache"""
        if not self.should_cache(request):
            return None
        
        cache_key = self.get_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.debug(f"Cache hit for {request.path}")
            response = JsonResponse(cached_response)
            response['X-Cache'] = 'HIT'
            return response
        
        # Store cache key for response processing
        request._cache_key = cache_key
        return None
    
    def process_response(self, request, response):
        """Cache successful responses"""
        if hasattr(request, '_cache_key') and response.status_code == 200:
            # Only cache JSON responses
            if response.get('Content-Type', '').startswith('application/json'):
                try:
                    # Parse response content
                    if hasattr(response, 'data'):
                        data = response.data
                    else:
                        data = json.loads(response.content)
                    
                    # Cache the data
                    cache.set(request._cache_key, data, timeout=60)  # 1 minute cache
                    response['X-Cache'] = 'MISS'
                    logger.debug(f"Cached response for {request.path}")
                except:
                    pass
        
        return response