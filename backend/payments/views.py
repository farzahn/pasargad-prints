import logging
from decimal import Decimal
from datetime import datetime, timezone

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cart.models import Cart
from orders.models import Order, OrderItem
from products.models import Product
from .models import Payment, StripeWebhookEvent
from .stripe_init import stripe

from utils.email import email_service
from utils.decorators import log_payment_operation, log_execution_time
from utils.exceptions import PaymentError

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@log_payment_operation
def create_checkout_session(request):
    """
    Creates a Stripe checkout session based on the user's current cart.
    The session is configured with line items, metadata for order tracking,
    and success/cancel URLs.
    """
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key).first()

        if not cart or not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate stock availability before creating checkout session
        for item in cart.items.all():
            if not item.product.is_in_stock or item.product.stock_quantity == 0:
                return Response({
                    'error': f'{item.product.name} is out of stock. Please remove it from your cart.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if item.quantity > item.product.stock_quantity:
                return Response({
                    'error': f'Only {item.product.stock_quantity} units of {item.product.name} available. You have {item.quantity} in cart.'
                }, status=status.HTTP_400_BAD_REQUEST)

        line_items = _prepare_line_items(cart, request)
        metadata = _prepare_metadata(cart, request)

        # Validate Stripe configuration
        if not settings.STRIPE_SECRET_KEY:
            logger.error("Stripe secret key not configured")
            return Response(
                {'error': 'Payment system not configured. Please contact support.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Use frontend URL for redirects to avoid Docker hostname issues
        frontend_url = 'http://localhost:3000'
        success_url = f'{frontend_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}'
        cancel_url = f'{frontend_url}/checkout/cancel'

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=request.user.email if request.user.is_authenticated else None,
            metadata=metadata,
            shipping_address_collection={'allowed_countries': ['US', 'CA']},
            expires_at=int((datetime.now(timezone.utc).timestamp()) + 3600),  # 1 hour
        )

        logger.info(f"Created Stripe checkout session {checkout_session.id} for cart {cart.id}")
        return Response({
            'checkout_session_id': checkout_session.id,
            'checkout_url': checkout_session.url,
        }, status=status.HTTP_200_OK)

    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error creating checkout session: {e.user_message if hasattr(e, 'user_message') else str(e)}")
        error_message = 'Payment service error. Please try again later.'
        if e.code == 'api_key_expired':
            error_message = 'Payment configuration error. Please contact support.'
        return Response(
            {'error': error_message},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.exception("Unexpected error creating checkout session")
        return Response(
            {'error': 'Failed to create checkout session. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@log_execution_time
def verify_checkout_session(request):
    """
    Verifies a checkout session's status. This endpoint is designed to be polled
    by the frontend after a redirect from Stripe. It does NOT create an order,
    as that responsibility lies with the webhook handler to prevent race conditions.
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Verifying checkout session: {session_id}")
        session = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent'])
        
        # Handle None payment_intent (can happen if session expired or was not completed)
        if not session.payment_intent:
            logger.warning(f"Session {session_id} has no payment intent")
            return Response(
                {'status': 'failed', 'message': 'Payment session expired or was not completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_intent_id = session.payment_intent.id

        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()

        if session.payment_status == 'paid':
            if payment:
                logger.info(f"Payment {payment.id} found for session {session_id}. Status: success.")
                return Response({
                    'status': 'success',
                    'order_id': payment.order.id,
                    'order_number': payment.order.order_number,
                    'email': payment.order.email if payment.order else None,
                }, status=status.HTTP_200_OK)
            else:
                # Payment is successful but order might not be created yet (webhook processing)
                logger.info(f"Payment successful for session {session_id} but order not yet created. Waiting for webhook.")
                return Response({
                    'status': 'pending',
                    'message': 'Payment successful. Order is being processed.',
                }, status=status.HTTP_200_OK)
        elif session.status == 'open':
            logger.warning(f"Session {session_id} is still open. Payment not completed.")
            return Response({'status': 'pending', 'message': 'Payment not completed.'}, status=status.HTTP_200_OK)
        elif session.status == 'complete' and session.payment_status == 'paid':
            # Handle complete status with paid payment
            if payment:
                logger.info(f"Session {session_id} complete. Payment {payment.id} found.")
                return Response({
                    'status': 'success',
                    'order_id': payment.order.id,
                    'order_number': payment.order.order_number,
                    'email': payment.order.email if payment.order else None,
                }, status=status.HTTP_200_OK)
            else:
                logger.info(f"Session {session_id} complete but order not yet created. Waiting for webhook.")
                return Response({
                    'status': 'pending',
                    'message': 'Payment successful. Order is being processed.',
                }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Unhandled session status for {session_id}: {session.status}, payment_status: {session.payment_status}")
            return Response({'status': 'failed', 'message': 'Payment failed or session expired.'}, status=status.HTTP_400_BAD_REQUEST)

    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid session ID {session_id}: {e}")
        return Response(
            {'error': 'Invalid payment session ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except stripe.error.StripeError as e:
        logger.exception(f"Stripe error verifying session {session_id}: {e}")
        return Response(
            {'error': 'Payment service error. Please try again later.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.exception(f"Unexpected error verifying session {session_id}")
        return Response(
            {'error': 'Failed to verify payment session'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(['POST'])
@log_payment_operation
def stripe_webhook(request):
    """
    Handles incoming webhooks from Stripe. This is the single source of truth
    for order creation and payment status updates.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.error("Missing Stripe signature header")
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Invalid webhook signature: {e}")
        return HttpResponse(status=400)

    # Idempotency check
    event_id = event['id']
    if StripeWebhookEvent.objects.filter(stripe_event_id=event_id).exists():
        logger.info(f"Webhook event {event_id} already processed.")
        return HttpResponse(status=200)

    StripeWebhookEvent.objects.create(
        stripe_event_id=event_id,
        event_type=event['type'],
        data=event['data']
    )

    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            logger.info(f"Processing checkout.session.completed for session {session['id']}")
            _handle_successful_payment(session)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            logger.warning(f"Processing payment_intent.payment_failed for PI {payment_intent['id']}")
            _handle_failed_payment(payment_intent)
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")

    except Exception as e:
        logger.exception(f"Error processing webhook event {event_id}")
        # Update event with error message
        StripeWebhookEvent.objects.filter(stripe_event_id=event_id).update(
            processed=False,
            error_message=str(e),
            processed_at=datetime.now(timezone.utc)
        )
        return HttpResponse(status=500)

    # Mark as processed
    StripeWebhookEvent.objects.filter(stripe_event_id=event_id).update(
        processed=True,
        processed_at=datetime.now(timezone.utc)
    )
    return HttpResponse(status=200)


def _handle_successful_payment(session):
    """
    Creates an order atomically from a successful Stripe session.
    This is the primary method for order creation.
    """
    payment_intent_id = session.get('payment_intent')
    if not payment_intent_id:
        raise ValueError("Session is missing payment_intent ID")

    if Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).exists():
        logger.warning(f"Payment for intent {payment_intent_id} already exists. Skipping order creation.")
        return

    metadata = session.get('metadata', {})
    cart_id = metadata.get('cart_id')
    if not cart_id:
        raise ValueError(f"Session {session['id']} is missing cart_id in metadata")
    
    cart = Cart.objects.filter(id=cart_id).first()
    if not cart:
        raise ValueError(f"Cart {cart_id} not found for session {session['id']}")
    
    if not cart.items.exists():
        raise ValueError(f"Cart {cart_id} is empty for session {session['id']}")

    try:
        with transaction.atomic():
            order = _create_order_from_session(session, cart)
            _create_payment_record(session, order)
            cart.items.all().delete()
            logger.info(f"Successfully created order {order.order_number} from session {session['id']}")
            
            # Send email outside transaction to avoid blocking
            try:
                if order.user:
                    email_service.send_order_confirmation(order)
                else:
                    # Send guest order receipt with tracking info
                    email_service.send_guest_order_receipt(order)
            except Exception as email_error:
                logger.error(f"Failed to send order confirmation email for order {order.order_number}: {email_error}")
                # Don't fail the transaction for email errors
    except Exception as e:
        logger.exception(f"Atomic transaction failed for session {session['id']}")
        raise e


def _handle_failed_payment(payment_intent):
    """
    Updates the status of a payment and order upon failure.
    """
    payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent['id']).first()
    if payment and payment.status != 'failed':
        payment.status = 'failed'
        payment.gateway_response = payment_intent
        payment.save()
        payment.order.status = 'cancelled'
        payment.order.save()
        logger.warning(f"Marked order {payment.order.order_number} as cancelled due to failed payment.")


def _create_order_from_session(session, cart):
    """Creates and saves an Order instance from session data."""
    customer_details = session.get('customer_details', {})
    shipping_details = session.get('shipping_details') or session.get('shipping') or customer_details
    
    # Handle nested address structure from Stripe
    if isinstance(shipping_details, dict) and 'address' in shipping_details:
        address = shipping_details.get('address', {})
        shipping_name = shipping_details.get('name', '')
    else:
        address = shipping_details
        shipping_name = customer_details.get('name', '')
    
    user_id = session['metadata'].get('user_id')
    if not user_id and cart.user:
        user_id = cart.user.id
    
    # For guest checkout, we need to handle missing user_id
    user = None
    if user_id:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"User {user_id} not found for order creation")
            user = None

    # Create order with proper null handling for guest checkout
    order_data = {
        'user': user,  # Can be None for guest checkout
        'status': 'processing',
        'subtotal': Decimal(session['amount_subtotal']) / 100,
        'tax_amount': Decimal(session.get('total_details', {}).get('amount_tax', 0)) / 100,
        'shipping_cost': Decimal(session.get('total_details', {}).get('amount_shipping', 0)) / 100,
        'total_amount': Decimal(session['amount_total']) / 100,
        'shipping_name': shipping_name or customer_details.get('name', 'Guest'),
        'shipping_email': customer_details.get('email', ''),
        'shipping_phone': customer_details.get('phone', ''),
        'shipping_address': address.get('line1', ''),
        'shipping_city': address.get('city', ''),
        'shipping_state': address.get('state', ''),
        'shipping_postal_code': address.get('postal_code', ''),
        'shipping_country': address.get('country', ''),
        'billing_name': shipping_name or customer_details.get('name', 'Guest'),
        'billing_email': customer_details.get('email', ''),
        'billing_address': address.get('line1', ''),
        'billing_city': address.get('city', ''),
        'billing_state': address.get('state', ''),
        'billing_postal_code': address.get('postal_code', ''),
        'billing_country': address.get('country', ''),
    }
    
    # Add session info for guest orders
    if not user and cart.session_key:
        order_data['session_key'] = cart.session_key
    
    order = Order.objects.create(**order_data)

    logger.info(f"Created order {order.order_number} in memory.")

    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price,
        )
        product = cart_item.product
        product.stock_quantity -= cart_item.quantity
        product.save(update_fields=['stock_quantity'])

    return order


def _create_payment_record(session, order):
    """Creates and saves a Payment instance."""
    payment_data = {
        'order': order,
        'user': order.user,  # Can be None for guest checkout
        'status': 'completed',
        'payment_method': 'stripe',
        'amount': order.total_amount,
        'currency': session.get('currency', 'usd').lower(),
        'stripe_payment_intent_id': session.get('payment_intent'),
        'stripe_customer_id': session.get('customer'),
        'gateway_response': session,
        'processed_at': datetime.now(timezone.utc),
    }
    
    # For guest checkout without user, we still need to track the payment
    if not order.user:
        # Remove user field for guest checkout
        payment_data.pop('user', None)
        payment_data['transaction_id'] = f"guest_{session.get('payment_intent')}"
    
    Payment.objects.create(**payment_data)


def _prepare_line_items(cart, request):
    """Prepares a list of line items for the Stripe session."""
    line_items = []
    for item in cart.items.all():
        product_data = {'name': item.product.name}
        if item.product.description:
            product_data['description'] = item.product.description[:500]
        if item.product.main_image:
            product_data['images'] = [request.build_absolute_uri(item.product.main_image)]
        
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': product_data,
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    shipping_cost = _calculate_shipping_cost(cart)
    if shipping_cost > 0:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Shipping'},
                'unit_amount': int(shipping_cost * 100),
            },
            'quantity': 1,
        })
    return line_items


def _prepare_metadata(cart, request):
    """Prepares metadata for the Stripe session."""
    metadata = {'cart_id': str(cart.id)}
    if request.user.is_authenticated:
        metadata['user_id'] = str(request.user.id)
    if cart.session_key:
        metadata['session_key'] = cart.session_key
    return metadata


def _calculate_shipping_cost(cart):
    """Calculates shipping cost. Placeholder for more complex logic."""
    if cart.total_price >= Decimal('100.00'):
        return Decimal('0.00')
    return Decimal('5.00') + (cart.total_weight * Decimal('0.50'))
