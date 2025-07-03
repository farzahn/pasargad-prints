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

# Import stripe components from our initialization module
from .stripe_init import stripe, CheckoutSession, StripeError, SignatureVerificationError, Webhook

# Configure logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_stripe_connection(request):
    """Test stripe connection"""
    try:
        import stripe as test_stripe
        test_stripe.api_key = settings.STRIPE_SECRET_KEY
        
        return Response({
            'stripe_module': str(test_stripe),
            'api_key_set': bool(test_stripe.api_key),
            'api_key_length': len(test_stripe.api_key) if test_stripe.api_key else 0,
            'checkout_module': str(test_stripe.checkout),
            'has_Session': hasattr(test_stripe.checkout, 'Session'),
            'settings_key_set': bool(settings.STRIPE_SECRET_KEY),
            'settings_key_length': len(settings.STRIPE_SECRET_KEY) if settings.STRIPE_SECRET_KEY else 0,
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'type': type(e).__name__
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def create_checkout_session(request):
    """
    Create a Stripe checkout session for the current cart
    """
    try:
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
        
        # Create Stripe checkout session
        checkout_session = CheckoutSession.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/checkout/success?session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=request.build_absolute_uri('/checkout/cancel'),
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


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_checkout_session(request):
    """
    Verify a checkout session and create order if successful
    """
    session_id = request.GET.get('session_id')
    
    if not session_id:
        return Response(
            {'error': 'Session ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Retrieve the session from Stripe
        session = CheckoutSession.retrieve(
            session_id,
            expand=['line_items', 'customer_details', 'payment_intent']
        )
        
        if session.payment_status == 'paid':
            # Check if order already exists
            existing_payment = Payment.objects.filter(
                stripe_payment_intent_id=session.payment_intent.id
            ).first()
            
            if existing_payment:
                return Response({
                    'status': 'success',
                    'order_id': existing_payment.order.id,
                    'order_number': existing_payment.order.order_number,
                }, status=status.HTTP_200_OK)
            
            # Create order from the session
            order = create_order_from_session(session)
            
            return Response({
                'status': 'success',
                'order_id': order.id,
                'order_number': order.order_number,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'pending',
                'message': 'Payment is still being processed',
            }, status=status.HTTP_200_OK)
            
    except StripeError as e:
        logger.error(f"Stripe error verifying session: {str(e)}")
        return Response(
            {'error': 'Failed to verify payment'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error verifying session: {str(e)}")
        return Response(
            {'error': 'An error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(['POST'])
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        return HttpResponse(status=400)
    
    try:
        # Verify webhook signature
        event = Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload")
        return HttpResponse(status=400)
    except SignatureVerificationError:
        logger.error("Invalid signature")
        return HttpResponse(status=400)
    
    # Store webhook event
    webhook_event, created = StripeWebhookEvent.objects.get_or_create(
        stripe_event_id=event['id'],
        defaults={
            'event_type': event['type'],
            'data': event['data'],
        }
    )
    
    if not created and webhook_event.processed:
        return HttpResponse(status=200)
    
    try:
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_successful_payment(session)
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            handle_failed_payment(payment_intent)
        
        # Mark event as processed
        webhook_event.processed = True
        webhook_event.processed_at = datetime.now(timezone.utc)
        webhook_event.save()
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        webhook_event.error_message = str(e)
        webhook_event.save()
        return HttpResponse(status=500)
    
    return HttpResponse(status=200)


def handle_successful_payment(session):
    """
    Handle successful payment from Stripe webhook
    """
    # Check if order already exists
    existing_payment = Payment.objects.filter(
        stripe_payment_intent_id=session['payment_intent']
    ).first()
    
    if existing_payment:
        return
    
    # Create order from session
    create_order_from_session(session)


def handle_failed_payment(payment_intent):
    """
    Handle failed payment from Stripe webhook
    """
    payment = Payment.objects.filter(
        stripe_payment_intent_id=payment_intent['id']
    ).first()
    
    if payment:
        payment.status = 'failed'
        payment.gateway_response = payment_intent
        payment.save()
        
        # Update order status
        payment.order.status = 'cancelled'
        payment.order.save()


def create_order_from_session(session):
    """
    Create an order from a Stripe checkout session
    """
    metadata = session.get('metadata', {})
    cart_id = metadata.get('cart_id')
    user_id = metadata.get('user_id')
    
    # Get the cart
    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        raise ValueError(f"Cart {cart_id} not found")
    
    # Get customer details
    customer_details = session.get('customer_details', {})
    shipping_details = session.get('shipping_details') or customer_details
    
    # Create order
    order = Order.objects.create(
        user_id=user_id if user_id else cart.user_id,
        status='processing',
        fulfillment_method='shipping',
        subtotal=Decimal(str(session['amount_subtotal'] / 100)),
        tax_amount=Decimal(str(session.get('total_details', {}).get('amount_tax', 0) / 100)),
        shipping_cost=Decimal(str(session.get('total_details', {}).get('amount_shipping', 0) / 100)),
        total_amount=Decimal(str(session['amount_total'] / 100)),
        # Shipping information
        shipping_name=shipping_details.get('name', ''),
        shipping_email=customer_details.get('email', ''),
        shipping_phone=customer_details.get('phone', ''),
        shipping_address=shipping_details.get('address', {}).get('line1', ''),
        shipping_city=shipping_details.get('address', {}).get('city', ''),
        shipping_state=shipping_details.get('address', {}).get('state', ''),
        shipping_postal_code=shipping_details.get('address', {}).get('postal_code', ''),
        shipping_country=shipping_details.get('address', {}).get('country', ''),
        # Billing information (same as shipping for now)
        billing_name=shipping_details.get('name', ''),
        billing_email=customer_details.get('email', ''),
        billing_address=shipping_details.get('address', {}).get('line1', ''),
        billing_city=shipping_details.get('address', {}).get('city', ''),
        billing_state=shipping_details.get('address', {}).get('state', ''),
        billing_postal_code=shipping_details.get('address', {}).get('postal_code', ''),
        billing_country=shipping_details.get('address', {}).get('country', ''),
    )
    
    # Create order items from cart items
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price,
            total_price=cart_item.total_price,
        )
        
        # Update product inventory
        cart_item.product.stock_quantity -= cart_item.quantity
        cart_item.product.save()
    
    # Create payment record
    Payment.objects.create(
        order=order,
        user_id=order.user_id,
        status='completed',
        payment_method='stripe',
        amount=order.total_amount,
        currency='USD',
        stripe_payment_intent_id=session.get('payment_intent'),
        stripe_customer_id=session.get('customer'),
        gateway_response=session,
        processed_at=datetime.now(timezone.utc),
    )
    
    # Clear the cart
    cart.items.all().delete()
    
    return order


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
