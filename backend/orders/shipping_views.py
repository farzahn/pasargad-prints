"""
Shipping views that integrate with Goshippo service to replace ShipStation.
Handles shipping rates, label creation, and tracking through Goshippo API.

Goshippo SDK Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging
import hmac
import hashlib
import json

from .models import Order
from .serializers import OrderDetailSerializer
from .permissions import IsOwnerOrAdmin, IsAdminUser
from utils.goshippo_service import shippo_service

logger = logging.getLogger(__name__)


def verify_goshippo_webhook_signature(payload, signature, secret):
    """
    Verify Goshippo webhook signature for security.
    
    Args:
        payload (bytes): Raw request body
        signature (str): Signature from X-Goshippo-Signature header
        secret (str): Webhook secret from settings
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not secret or not signature:
        return False
    
    try:
        # Goshippo uses HMAC-SHA256 for webhook signatures
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures using constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


class ShippingRatesView(generics.GenericAPIView):
    """
    Get shipping rates for an order using Goshippo.
    
    POST /api/orders/{order_id}/shipping/rates/
    
    Request Body:
    {
        "to_address": {
            "name": "John Doe",
            "street1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "US"
        },
        "parcel": {
            "weight": 1.5,
            "length": 12,
            "width": 9,
            "height": 6
        }
    }
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def post(self, request, order_id):
        """Get shipping rates for an order."""
        order = get_object_or_404(Order, id=order_id)
        
        # Validate request data
        to_address = request.data.get('to_address')
        parcel = request.data.get('parcel')
        
        if not to_address or not parcel:
            return Response(
                {'error': 'to_address and parcel are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get origin address from settings
        from_address = getattr(settings, 'SHIPPING_ORIGIN', {})
        
        if not from_address.get('street1'):
            return Response(
                {'error': 'Shipping origin address not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Calculate parcel weight from order if not provided
        if not parcel.get('weight'):
            parcel['weight'] = max(float(order.total_weight), 1.0)
        
        # Get shipping rates
        try:
            rates_result = goshippo_service.get_shipping_rates(
                from_address=from_address,
                to_address=to_address,
                parcel_details=parcel
            )
            
            if rates_result.get('status') == 'error':
                return Response(
                    {'error': rates_result.get('error', 'Failed to get shipping rates')},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Store shipment ID for later use
            if rates_result.get('shipment_id'):
                order.goshippo_object_id = rates_result['shipment_id']
                order.save(update_fields=['goshippo_object_id'])
            
            return Response(rates_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting shipping rates for order {order_id}: {e}")
            return Response(
                {'error': 'Failed to get shipping rates'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateShippingLabelView(generics.GenericAPIView):
    """
    Create a shipping label for an order using Goshippo.
    
    POST /api/orders/{order_id}/shipping/label/
    
    Request Body:
    {
        "rate_id": "rate_xxxxx",
        "label_format": "PDF"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request, order_id):
        """Create shipping label for an order."""
        order = get_object_or_404(Order, id=order_id)
        
        # Validate request data
        rate_id = request.data.get('rate_id')
        label_format = request.data.get('label_format', 'PDF')
        
        if not rate_id:
            return Response(
                {'error': 'rate_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create shipping label
        try:
            label_result = goshippo_service.create_shipping_label(
                rate_id=rate_id,
                label_format=label_format
            )
            
            if label_result.get('status') == 'error':
                return Response(
                    {'error': label_result.get('error', 'Failed to create shipping label')},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Update order with shipping information
            order.goshippo_transaction_id = label_result.get('transaction_id')
            order.goshippo_rate_id = rate_id
            order.tracking_number = label_result.get('tracking_number')
            order.goshippo_tracking_url = label_result.get('tracking_url')
            order.goshippo_label_url = label_result.get('label_url')
            order.carrier = label_result.get('carrier')
            order.service_level = label_result.get('service')
            
            # Update order status to shipped
            if order.status == 'processing':
                order.status = 'shipped'
                order.shipped_at = timezone.now()
            
            order.save()
            
            # Send shipping notification email
            from orders.utils import send_shipping_notification_email
            try:
                send_shipping_notification_email(order)
            except Exception as e:
                logger.warning(f"Failed to send shipping notification: {e}")
            
            # Return updated order information
            serializer = OrderDetailSerializer(order, context={'request': request})
            return Response({
                'order': serializer.data,
                'label': label_result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating shipping label for order {order_id}: {e}")
            return Response(
                {'error': 'Failed to create shipping label'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrackShipmentView(generics.GenericAPIView):
    """
    Track a shipment using Goshippo.
    
    GET /api/orders/{order_id}/shipping/track/
    or
    GET /api/shipping/track/{tracking_number}/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, order_id=None, tracking_number=None):
        """Track shipment by order ID or tracking number."""
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            tracking_number = order.tracking_number
            carrier = order.carrier
        elif tracking_number:
            # Try to find order by tracking number
            order = Order.objects.filter(tracking_number=tracking_number).first()
            carrier = order.carrier if order else None
        else:
            return Response(
                {'error': 'order_id or tracking_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not tracking_number:
            return Response(
                {'error': 'No tracking number found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Track shipment
        try:
            tracking_result = goshippo_service.track_shipment(
                tracking_number=tracking_number,
                carrier=carrier
            )
            
            if tracking_result.get('status') == 'error':
                return Response(
                    {'error': tracking_result.get('error', 'Failed to track shipment')},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Update order delivery status if needed
            if order and tracking_result.get('tracking_status') == 'DELIVERED':
                if order.status != 'delivered':
                    order.status = 'delivered'
                    order.delivered_at = timezone.now()
                    order.save(update_fields=['status', 'delivered_at'])
            
            return Response(tracking_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error tracking shipment {tracking_number}: {e}")
            return Response(
                {'error': 'Failed to track shipment'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ValidateAddressView(generics.GenericAPIView):
    """
    Validate a shipping address using Goshippo.
    
    POST /api/shipping/validate-address/
    
    Request Body:
    {
        "name": "John Doe",
        "street1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "country": "US"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Validate shipping address."""
        address_data = request.data
        
        # Validate required fields
        required_fields = ['street1', 'city', 'state', 'zip', 'country']
        missing_fields = [field for field in required_fields if not address_data.get(field)]
        
        if missing_fields:
            return Response(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate address
        try:
            validation_result = goshippo_service.validate_address(address_data)
            
            if validation_result.get('status') == 'error':
                return Response(
                    {'error': validation_result.get('error', 'Failed to validate address')},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            return Response(validation_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return Response(
                {'error': 'Failed to validate address'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ShippingWebhookView(generics.GenericAPIView):
    """
    Handle Goshippo webhooks for tracking updates.
    
    POST /api/shipping/webhook/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle Goshippo webhook notifications."""
        try:
            # Verify webhook signature for security
            webhook_secret = getattr(settings, 'GOSHIPPO_WEBHOOK_SECRET', '')
            if webhook_secret:
                signature = request.META.get('HTTP_X_GOSHIPPO_SIGNATURE', '')
                raw_payload = request.body
                
                if not verify_goshippo_webhook_signature(raw_payload, signature, webhook_secret):
                    logger.warning("Invalid Goshippo webhook signature")
                    return Response(
                        {'error': 'Invalid signature'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                    
                logger.info("Goshippo webhook signature verified successfully")
            else:
                # In production, webhook secret should always be configured
                if not settings.DEBUG:
                    logger.warning("Goshippo webhook received without signature verification")
                    return Response(
                        {'error': 'Webhook signature verification required'}, 
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            
            # Parse webhook data
            webhook_data = request.data
            event_type = webhook_data.get('event')
            tracking_number = webhook_data.get('data', {}).get('tracking_number')
            
            if not tracking_number:
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
            
            # Find order by tracking number
            order = Order.objects.filter(tracking_number=tracking_number).first()
            if not order:
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
            
            # Handle different event types
            if event_type == 'track_updated':
                tracking_status = webhook_data.get('data', {}).get('tracking_status')
                
                if tracking_status == 'DELIVERED' and order.status != 'delivered':
                    order.status = 'delivered'
                    order.delivered_at = timezone.now()
                    order.save(update_fields=['status', 'delivered_at'])
                    
                    # Send delivery notification email
                    from orders.utils import send_delivery_notification_email
                    try:
                        send_delivery_notification_email(order)
                    except Exception as e:
                        logger.warning(f"Failed to send delivery notification: {e}")
                
                logger.info(f"Webhook processed: {event_type} for order {order.order_number}")
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing Goshippo webhook: {e}")
            return Response(
                {'error': 'Failed to process webhook'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )