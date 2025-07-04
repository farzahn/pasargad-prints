from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.throttling import BaseThrottle, SimpleRateThrottle
from functools import wraps
import time
import hashlib

class BurstRateThrottle(SimpleRateThrottle):
    """
    Throttle for burst requests - allows short bursts but limits sustained traffic
    """
    scope = 'burst'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

class SustainedRateThrottle(SimpleRateThrottle):
    """
    Throttle for sustained requests - lower rate for longer period
    """
    scope = 'sustained'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

class UserActionThrottle(BaseThrottle):
    """
    Throttle specific user actions (like order creation, review submission)
    """
    def __init__(self):
        self.rate_limits = {
            'order_create': (5, 3600),  # 5 orders per hour
            'review_create': (10, 86400),  # 10 reviews per day
            'password_reset': (3, 3600),  # 3 password resets per hour
            'registration': (3, 3600),  # 3 registrations per hour per IP
        }
    
    def get_cache_key(self, request, action):
        """Generate cache key for rate limiting"""
        if request.user.is_authenticated:
            ident = f"user_{request.user.pk}"
        else:
            # Use IP address for anonymous users
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            ident = f"ip_{ip}"
        
        return f"rate_limit:{action}:{ident}"
    
    def allow_request(self, request, view):
        """Check if request is allowed"""
        action = getattr(view, 'rate_limit_action', None)
        if not action or action not in self.rate_limits:
            return True
        
        limit, period = self.rate_limits[action]
        cache_key = self.get_cache_key(request, action)
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return False
        
        # Increment count
        cache.set(cache_key, current_count + 1, period)
        return True
    
    def wait(self):
        """Return number of seconds until next request is allowed"""
        return 60  # Default wait time

def rate_limit(action, limit=None, period=None):
    """
    Decorator for rate limiting specific actions
    
    Args:
        action: Action identifier
        limit: Number of allowed requests (optional, uses default if not provided)
        period: Time period in seconds (optional, uses default if not provided)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Get user identifier
            if request.user.is_authenticated:
                ident = f"user_{request.user.pk}"
            else:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                ident = f"ip_{ip}"
            
            # Default limits
            default_limits = {
                'api_call': (100, 3600),  # 100 calls per hour
                'search': (30, 60),  # 30 searches per minute
                'checkout': (10, 3600),  # 10 checkouts per hour
                'contact': (5, 3600),  # 5 contact form submissions per hour
            }
            
            # Use provided limit/period or defaults
            if limit and period:
                rate_limit_config = (limit, period)
            else:
                rate_limit_config = default_limits.get(action, (10, 60))
            
            request_limit, time_period = rate_limit_config
            cache_key = f"rate_limit:{action}:{ident}"
            
            # Check current count
            current_count = cache.get(cache_key, 0)
            
            if current_count >= request_limit:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many {action} requests. Please try again later.',
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Increment count
            cache.set(cache_key, current_count + 1, time_period)
            
            # Add rate limit headers
            response = func(request, *args, **kwargs)
            response['X-RateLimit-Limit'] = str(request_limit)
            response['X-RateLimit-Remaining'] = str(request_limit - current_count - 1)
            response['X-RateLimit-Reset'] = str(int(time.time()) + time_period)
            
            return response
        
        return wrapper
    return decorator

class IPBlockingMiddleware:
    """
    Middleware to block IPs that repeatedly violate rate limits
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.violation_threshold = 10  # Number of violations before blocking
        self.block_duration = 86400  # 24 hours
    
    def __call__(self, request):
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Check if IP is blocked
        block_key = f"ip_block:{ip}"
        if cache.get(block_key):
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Your IP has been temporarily blocked due to excessive requests.',
            }, status=status.HTTP_403_FORBIDDEN)
        
        response = self.get_response(request)
        
        # Check for rate limit violations
        if response.status_code == 429:
            # Increment violation count
            violation_key = f"ip_violations:{ip}"
            violations = cache.get(violation_key, 0) + 1
            cache.set(violation_key, violations, 3600)  # Track for 1 hour
            
            # Block IP if threshold exceeded
            if violations >= self.violation_threshold:
                cache.set(block_key, True, self.block_duration)
                cache.delete(violation_key)  # Reset violations
        
        return response