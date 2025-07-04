"""
Middleware to ensure session persistence for guest users
"""
from django.utils.deprecation import MiddlewareMixin


class SessionPersistenceMiddleware(MiddlewareMixin):
    """
    Ensures that sessions are properly created and persisted for guest users
    who interact with the cart.
    """
    
    def process_request(self, request):
        # Skip for authenticated users
        if request.user.is_authenticated:
            return
        
        # Check if this is a cart-related request
        cart_paths = ['/api/cart/', '/api/orders/create/', '/api/payments/']
        is_cart_request = any(request.path.startswith(path) for path in cart_paths)
        
        if is_cart_request:
            # Ensure session exists
            if not request.session.session_key:
                request.session.create()
                # Mark session as modified to ensure it's saved
                request.session.modified = True
    
    def process_response(self, request, response):
        # Ensure session is saved for cart operations
        if hasattr(request, 'session') and request.session.modified:
            request.session.save()
        
        return response


class CartCleanupMiddleware(MiddlewareMixin):
    """
    Cleans up old guest carts to prevent database bloat
    """
    
    def process_request(self, request):
        # Run cleanup only occasionally (1% of requests)
        import random
        if random.random() > 0.01:
            return
        
        # Clean up old guest carts
        from django.utils import timezone
        from datetime import timedelta
        from cart.models import Cart
        
        # Delete guest carts older than 30 days with no items
        cutoff_date = timezone.now() - timedelta(days=30)
        old_empty_carts = Cart.objects.filter(
            user__isnull=True,
            updated_at__lt=cutoff_date
        ).exclude(items__isnull=False)
        
        count = old_empty_carts.count()
        if count > 0:
            old_empty_carts.delete()
            print(f"Cleaned up {count} old empty guest carts")