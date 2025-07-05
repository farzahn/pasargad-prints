from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import json
import logging

from orders.models import Order
from .models import ShippingRate, ShippingLabel, TrackingEvent
from .serializers import (
    ShippingRateSerializer,
    ShippingLabelSerializer,
    TrackingEventSerializer,
    ShippingRateRequestSerializer,
    PurchaseLabelSerializer,
    TrackingRequestSerializer
)
from .services import shippo_service

logger = logging.getLogger(__name__)


class ShippingRatesView(generics.CreateAPIView):
    """
    Get shipping rates for an order.
    
    POST /api/shipping/rates/
    
    Request Body:
    {
        "order_id": 123
    }
    
    Returns list of available shipping rates for the order.
    """
    serializer_class = ShippingRateRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Get shipping rates for an order."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        order = get_object_or_404(Order, id=order_id)
        
        # Check if user has permission to view this order
        if not request.user.is_staff and order.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get rates from Goshippo
            rates_data = goshippo_service.get_shipping_rates(order)
            
            # Save rates to database
            shipping_rates = []
            for rate_data in rates_data:
                shipping_rate, created = ShippingRate.objects.get_or_create(
                    order=order,
                    goshippo_rate_id=rate_data['id'],
                    defaults={
                        'carrier': rate_data['carrier'],
                        'service_level': rate_data['service_level'],
                        'amount': rate_data['amount'],
                        'currency': rate_data['currency'],
                        'estimated_days': rate_data['estimated_days']
                    }
                )
                shipping_rates.append(shipping_rate)
            
            # Serialize and return rates
            rates_serializer = ShippingRateSerializer(shipping_rates, many=True)
            return Response(rates_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting shipping rates: {e}")
            return Response(
                {'error': 'Failed to get shipping rates'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PurchaseShippingLabelView(generics.CreateAPIView):
    """
    Purchase a shipping label for an order.
    
    POST /api/shipping/labels/
    
    Request Body:
    {
        "rate_id": "goshippo_rate_id",
        "label_file_type": "PDF"
    }
    
    Creates a shipping label and returns label details.
    """
    serializer_class = PurchaseLabelSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Purchase a shipping label."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rate_id = serializer.validated_data['rate_id']
        label_file_type = serializer.validated_data['label_file_type']
        
        # Get the shipping rate
        shipping_rate = get_object_or_404(ShippingRate, goshippo_rate_id=rate_id)
        order = shipping_rate.order
        
        # Check if user has permission to purchase label for this order
        if not request.user.is_staff and order.user != request.user:
            return Response(
                {'error': 'You do not have permission to purchase label for this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if label already exists
        if hasattr(order, 'shipping_label'):
            return Response(
                {'error': 'Shipping label already exists for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create transaction in Goshippo
            transaction = goshippo_service.create_transaction(rate_id, label_file_type)
            
            # Create shipping label record
            shipping_label = ShippingLabel.objects.create(
                order=order,
                goshippo_transaction_id=transaction.object_id,
                goshippo_shipment_id=transaction.rate.shipment,
                goshippo_rate_id=rate_id,
                label_url=transaction.label_url,
                tracking_number=transaction.tracking_number,
                carrier=shipping_rate.carrier,
                service_level=shipping_rate.service_level,
                amount=shipping_rate.amount,
                currency=shipping_rate.currency,
                status=transaction.object_state
            )
            
            # Update order with tracking number
            order.tracking_number = transaction.tracking_number
            order.save()
            
            # Serialize and return label
            label_serializer = ShippingLabelSerializer(shipping_label)
            return Response(label_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error purchasing shipping label: {e}")
            return Response(
                {'error': 'Failed to purchase shipping label'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrackingInfoView(generics.CreateAPIView):
    """
    Get tracking information for a shipment.
    
    POST /api/shipping/track/
    
    Request Body:
    {
        "carrier": "usps",
        "tracking_number": "1Z999AA1234567890"
    }
    
    Returns tracking information for the shipment.
    """
    serializer_class = TrackingRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Get tracking information."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        carrier = serializer.validated_data['carrier']
        tracking_number = serializer.validated_data['tracking_number']
        
        try:
            # Get tracking info from Goshippo
            tracking_info = goshippo_service.get_tracking_info(carrier, tracking_number)
            
            # Return tracking information
            return Response({
                'tracking_number': tracking_info.tracking_number,
                'carrier': tracking_info.carrier,
                'tracking_status': tracking_info.tracking_status,
                'tracking_history': tracking_info.tracking_history
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting tracking info: {e}")
            return Response(
                {'error': 'Failed to get tracking information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderShippingRatesView(generics.ListAPIView):
    """
    Get shipping rates for a specific order.
    
    GET /api/orders/{order_id}/shipping/rates/
    
    Returns list of shipping rates for the order.
    """
    serializer_class = ShippingRateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get shipping rates for the order."""
        order_id = self.kwargs['order_id']
        order = get_object_or_404(Order, id=order_id)
        
        # Check permissions
        if not self.request.user.is_staff and order.user != self.request.user:
            return ShippingRate.objects.none()
        
        return ShippingRate.objects.filter(order=order)


class OrderShippingLabelView(generics.RetrieveAPIView):
    """
    Get shipping label for a specific order.
    
    GET /api/orders/{order_id}/shipping/label/
    
    Returns shipping label details for the order.
    """
    serializer_class = ShippingLabelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Get shipping label for the order."""
        order_id = self.kwargs['order_id']
        order = get_object_or_404(Order, id=order_id)
        
        # Check permissions
        if not self.request.user.is_staff and order.user != self.request.user:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to view this order")
        
        return get_object_or_404(ShippingLabel, order=order)


@method_decorator(csrf_exempt, name='dispatch')
class GoshippoWebhookView(generics.GenericAPIView):
    """
    Handle Goshippo webhook notifications.
    
    POST /api/shipping/webhook/
    
    Receives tracking updates from Goshippo.
    """
    permission_classes = []  # No authentication required for webhooks
    
    def post(self, request):
        """Handle webhook notification."""
        try:
            payload = json.loads(request.body)
            event_type = payload.get('event')
            
            if event_type == 'track_updated':
                self.handle_tracking_update(payload)
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return HttpResponse(status=400)
    
    def handle_tracking_update(self, payload):
        """Handle tracking update webhook."""
        try:
            tracking_data = payload.get('data', {})
            tracking_number = tracking_data.get('tracking_number')
            
            if not tracking_number:
                return
            
            # Find the order by tracking number
            try:
                order = Order.objects.get(tracking_number=tracking_number)
            except Order.DoesNotExist:
                logger.warning(f"Order not found for tracking number: {tracking_number}")
                return
            
            # Create tracking event
            tracking_status = tracking_data.get('tracking_status', {})
            status_code = tracking_status.get('status', 'UNKNOWN')
            
            tracking_event = TrackingEvent.objects.create(
                order=order,
                tracking_number=tracking_number,
                status=status_code,
                status_details=tracking_status.get('status_details', ''),
                status_date=tracking_status.get('status_date'),
                location=tracking_status.get('location', ''),
                webhook_data=payload
            )
            
            # Update order status based on tracking status
            if status_code == 'DELIVERED' and order.status != 'delivered':
                order.status = 'delivered'
                order.save()
            elif status_code == 'TRANSIT' and order.status == 'processing':
                order.status = 'shipped'
                order.save()
            
            logger.info(f"Tracking event created for order {order.order_number}: {status_code}")
            
        except Exception as e:
            logger.error(f"Error handling tracking update: {e}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_tracking_events(request, order_id):
    """
    Get tracking events for a specific order.
    
    GET /api/orders/{order_id}/tracking/events/
    
    Returns list of tracking events for the order.
    """
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not request.user.is_staff and order.user != request.user:
        return Response(
            {'error': 'You do not have permission to view this order'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    tracking_events = TrackingEvent.objects.filter(order=order)
    serializer = TrackingEventSerializer(tracking_events, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)