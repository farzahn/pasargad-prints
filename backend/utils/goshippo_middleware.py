"""
Goshippo authentication and request/response middleware for ShipStation integration replacement.

Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
import shippo

logger = logging.getLogger(__name__)


class GoshippoAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to handle Goshippo authentication for shipping API requests.
    Authenticates requests to shipping endpoints using Goshippo test API key.
    """
    
    SHIPPING_PATHS = [
        '/api/shipping/',
        '/api/orders/shipping/',
        '/api/shipping/rates/',
        '/api/shipping/labels/',
        '/api/shipping/tracking/',
    ]
    
    def __init__(self, get_response):
        super().__init__(get_response)
        # Initialize Goshippo client with test API key
        self.goshippo_client = shippo.Shippo(
            security=security.Security(
                api_key_header=getattr(settings, 'GOSHIPPO_API_KEY', 'shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15')
            )
        )
        
    def process_request(self, request):
        """Process incoming requests to shipping endpoints."""
        # Check if this is a shipping-related request
        if any(request.path.startswith(path) for path in self.SHIPPING_PATHS):
            # Add Goshippo client to request for use in views
            request.goshippo_client = self.goshippo_client
            
            # Log shipping API request
            logger.info(
                f"Goshippo API request: {request.method} {request.path}",
                extra={
                    'request_id': getattr(request, 'id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'goshippo_enabled': True,
                }
            )
        
        return None
    
    def process_response(self, request, response):
        """Process responses from shipping endpoints."""
        # Add Goshippo headers to shipping responses
        if hasattr(request, 'goshippo_client') and any(request.path.startswith(path) for path in self.SHIPPING_PATHS):
            response['X-Shipping-Provider'] = 'Goshippo'
            response['X-Shipping-API-Version'] = '2018-02-08'
            
            # Log shipping API response
            logger.info(
                f"Goshippo API response: {request.method} {request.path} - Status: {response.status_code}",
                extra={
                    'request_id': getattr(request, 'id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'goshippo_enabled': True,
                }
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Handle Goshippo SDK exceptions."""
        if hasattr(request, 'goshippo_client') and isinstance(exception, SDKError):
            logger.error(
                f"Goshippo SDK error: {request.method} {request.path} - {str(exception)}",
                exc_info=True,
                extra={
                    'request_id': getattr(request, 'id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'goshippo_error': True,
                }
            )
            
            # Return standardized error response
            return JsonResponse({
                'error': True,
                'message': 'Shipping service temporarily unavailable. Please try again later.',
                'request_id': getattr(request, 'id', 'unknown'),
                'provider': 'goshippo',
            }, status=503)
        
        return None


class GoshippoRequestProcessingMiddleware(MiddlewareMixin):
    """
    Middleware to process and validate Goshippo shipping requests and responses.
    Handles request/response transformation and caching.
    """
    
    CACHE_PREFIX = 'goshippo_cache'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def process_request(self, request):
        """Process and validate shipping requests."""
        if not hasattr(request, 'goshippo_client'):
            return None
            
        # Cache shipping rates requests
        if request.path.startswith('/api/shipping/rates/') and request.method == 'POST':
            cache_key = self._generate_cache_key(request)
            cached_rates = cache.get(cache_key)
            
            if cached_rates:
                logger.info(f"Cache hit for shipping rates request: {cache_key}")
                response = JsonResponse(cached_rates)
                response['X-Cache'] = 'HIT'
                response['X-Shipping-Provider'] = 'Goshippo'
                return response
            
            # Store cache key for response processing
            request._goshippo_cache_key = cache_key
        
        return None
    
    def process_response(self, request, response):
        """Process and cache shipping responses."""
        if not hasattr(request, 'goshippo_client'):
            return response
            
        # Cache successful shipping rates responses
        if (hasattr(request, '_goshippo_cache_key') and 
            response.status_code == 200 and 
            response.get('Content-Type', '').startswith('application/json')):
            
            try:
                # Parse and cache response data
                if hasattr(response, 'data'):
                    data = response.data
                else:
                    data = json.loads(response.content)
                
                cache.set(request._goshippo_cache_key, data, timeout=self.CACHE_TIMEOUT)
                response['X-Cache'] = 'MISS'
                logger.info(f"Cached shipping rates response: {request._goshippo_cache_key}")
                
            except Exception as e:
                logger.warning(f"Failed to cache shipping response: {e}")
        
        return response
    
    def _generate_cache_key(self, request):
        """Generate cache key for shipping requests."""
        try:
            # Create cache key from request data
            request_data = json.loads(request.body) if request.body else {}
            
            # Create a hash of relevant shipping parameters
            import hashlib
            
            cache_data = {
                'from_address': request_data.get('from_address', {}),
                'to_address': request_data.get('to_address', {}),
                'parcel': request_data.get('parcel', {}),
                'carrier_accounts': request_data.get('carrier_accounts', []),
            }
            
            cache_string = json.dumps(cache_data, sort_keys=True)
            cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
            
            return f"{self.CACHE_PREFIX}_rates_{cache_hash}"
            
        except Exception as e:
            logger.warning(f"Failed to generate cache key: {e}")
            return f"{self.CACHE_PREFIX}_rates_fallback"


class GoshippoResponseProcessingMiddleware(MiddlewareMixin):
    """
    Middleware to process and transform Goshippo API responses.
    Handles response standardization and error handling.
    """
    
    def process_response(self, request, response):
        """Standardize Goshippo API responses."""
        if not hasattr(request, 'goshippo_client'):
            return response
            
        # Add standard shipping response headers
        response['X-Shipping-Provider'] = 'Goshippo'
        response['X-API-Version'] = '2018-02-08'
        
        # Transform response format if needed
        if (response.status_code == 200 and 
            response.get('Content-Type', '').startswith('application/json')):
            
            try:
                # Add metadata to successful responses
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    response.data['provider'] = 'goshippo'
                    response.data['api_version'] = '2018-02-08'
                    response.data['timestamp'] = self._get_timestamp()
                    
            except Exception as e:
                logger.warning(f"Failed to transform response: {e}")
        
        return response
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'