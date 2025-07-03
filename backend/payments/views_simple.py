import json
import logging
from decimal import Decimal
from datetime import datetime, timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from .models import Payment, StripeWebhookEvent
from products.models import Product

# Configure logging
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for the current cart
    """
    try:
        # Import stripe here to avoid initialization issues
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Get cart for the current user or session
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key).first()
        
        if not cart or not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare line items for Stripe
        line_items = []
        for item in cart.items.all():
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                        'description': item.product.description[:500] if item.product.description else '',
                        'images': [request.build_absolute_uri(item.product.main_image.url)] if item.product.main_image else [],
                    },
                    'unit_amount': int(item.product.price * 100),  # Convert to cents
                },
                'quantity': item.quantity,
            })
        
        # Get shipping information from request
        shipping_data = request.data.get('shipping', {})
        
        # Calculate shipping cost (you can implement your own logic here)
        shipping_cost = calculate_shipping_cost(cart)
        
        # Add shipping as a line item if applicable
        if shipping_cost > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Shipping',
                        'description': 'Standard shipping',
                    },
                    'unit_amount': int(shipping_cost * 100),  # Convert to cents
                },
                'quantity': 1,
            })
        
        # Calculate tax (implement your own tax calculation logic)
        tax_amount = calculate_tax(cart, shipping_data)
        
        # Create metadata for the session
        metadata = {
            'cart_id': str(cart.id),
            'user_id': str(request.user.id) if request.user.is_authenticated else '',
            'session_key': cart.session_key or '',
        }
        
        # Use the request's success/cancel URLs or build default ones
        success_url = request.data.get('success_url', request.build_absolute_uri('/checkout/success?session_id={CHECKOUT_SESSION_ID}'))
        cancel_url = request.data.get('cancel_url', request.build_absolute_uri('/checkout/cancel'))
        
        # Create Stripe checkout session using direct API call
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email if request.user.is_authenticated else None,
            metadata=metadata,
            shipping_address_collection={
                'allowed_countries': ['US', 'CA'],  # Add more countries as needed
            } if not shipping_data else None,
            automatic_tax={
                'enabled': False,  # Set to True if you have Stripe Tax configured
            },
            expires_at=int((datetime.now(timezone.utc).timestamp()) + 3600),  # Expires in 1 hour
        )
        
        return Response({
            'checkout_session_id': checkout_session.id,
            'checkout_url': checkout_session.url,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return Response(
            {'error': 'Failed to create checkout session', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def calculate_shipping_cost(cart):
    """
    Calculate shipping cost based on cart weight and items
    """
    # Basic shipping calculation - you can implement your own logic
    base_cost = Decimal('5.00')
    weight_cost = cart.total_weight * Decimal('0.50')
    
    total_shipping = base_cost + weight_cost
    
    # Free shipping for orders over $100
    if cart.total_price >= Decimal('100.00'):
        return Decimal('0.00')
    
    return total_shipping


def calculate_tax(cart, shipping_data):
    """
    Calculate tax based on shipping address
    """
    # Basic tax calculation - implement your own tax logic
    # This is a simplified example - you should use proper tax calculation
    tax_rate = Decimal('0.08')  # 8% tax
    return cart.total_price * tax_rate