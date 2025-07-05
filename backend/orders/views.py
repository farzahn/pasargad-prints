from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
import json
import logging

from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    OrderSerializer,
    OrderDetailSerializer,
    OrderStatusUpdateSerializer,
    OrderTrackingSerializer
)
from .permissions import IsOwnerOrAdmin, IsAdminUser
from .pagination import OrderPagination
from .filters import OrderFilter
# Import goshippo service conditionally to avoid CI issues
try:
    from utils.goshippo_service import goshippo_service
except ImportError:
    # Create a dummy service for CI/testing environments
    class DummyGoshippoService:
        def track_shipment(self, tracking_number):
            return {'tracking_status': 'unknown', 'eta': None, 'tracking_history': []}
        def get_shipping_rates(self, order):
            return []
        def get_transaction_status(self, transaction_id):
            return None
        def process_order_shipment(self, order, rate_object_id):
            return {'success': False, 'error': 'Service not available in CI'}
    goshippo_service = DummyGoshippoService()


class OrderListView(generics.ListAPIView):
    """
    List all orders for the authenticated user.
    
    GET /api/orders/
    
    Query Parameters:
    - status: Filter by order status (pending, processing, shipped, delivered, cancelled, refunded)
    - ordering: Sort results (-created_at, created_at, -total_amount, total_amount)
    - search: Search by order number or recipient name
    - page: Page number for pagination
    - page_size: Number of items per page (default: 10, max: 100)
    
    Returns paginated list of user's orders with basic information.
    Admin users see all orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    search_fields = ['order_number', 'shipping_name', 'shipping_email']
    
    def get_queryset(self):
        """Return orders based on user permissions."""
        user = self.request.user
        
        if user.is_staff:
            # Admin users can see all orders
            queryset = Order.objects.all()
        else:
            # Regular users can only see their own orders
            queryset = Order.objects.filter(user=user)
        
        # Additional filtering by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.select_related('user').prefetch_related('items')


class OrderDetailView(generics.RetrieveAPIView):
    """
    Retrieve detailed information about a specific order.
    
    GET /api/orders/{id}/
    
    Returns comprehensive order details including:
    - All order information
    - Order items with product details
    - Status history
    - Shipping and billing information
    
    Access restricted to order owner or admin users.
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Order.objects.all()
    
    def get_queryset(self):
        """Optimize query with related data."""
        return super().get_queryset().select_related('user').prefetch_related(
            'items__product',
            'items__product__images',
            'status_history__created_by'
        )


class OrderTrackingView(generics.RetrieveAPIView):
    """
    Public endpoint for order tracking by tracking number.
    
    GET /api/orders/track/{tracking_number}/
    
    Returns limited order information for public tracking.
    No authentication required.
    """
    serializer_class = OrderTrackingSerializer
    permission_classes = [AllowAny]
    lookup_field = 'tracking_number'
    
    def get_object(self):
        """Get order by tracking number."""
        tracking_number = self.kwargs.get('tracking_number')
        
        if not tracking_number:
            raise NotFound("Tracking number is required")
        
        try:
            return Order.objects.get(tracking_number=tracking_number)
        except Order.DoesNotExist:
            raise NotFound("Order not found with this tracking number")
    
    def retrieve(self, request, *args, **kwargs):
        """Enhanced retrieve with real-time tracking from Goshippo."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Get real-time tracking info from Goshippo if tracking number exists
        if instance.tracking_number:
            try:
                tracking_info = goshippo_service.track_shipment(instance.tracking_number)
                data['goshippo_tracking'] = {
                    'tracking_status': tracking_info.get('tracking_status'),
                    'eta': tracking_info.get('eta'),
                    'tracking_history': tracking_info.get('tracking_history', [])
                }
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to fetch Goshippo tracking info: {e}")
                data['goshippo_tracking'] = None
        
        return Response(data)


class OrderTrackingByIdView(generics.RetrieveAPIView):
    """
    Public endpoint for order tracking by order ID.
    
    GET /api/orders/track/id/{order_id}/
    
    Returns limited order information for public tracking.
    No authentication required.
    """
    serializer_class = OrderTrackingSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    queryset = Order.objects.all()


class GuestOrderTrackingView(generics.GenericAPIView):
    """
    Track guest orders by order number and email.
    
    POST /api/orders/track/guest/
    
    Request Body:
    {
        "order_number": "ABC123",
        "email": "guest@example.com"
    }
    
    Returns order tracking information if order number and email match.
    """
    permission_classes = [AllowAny]
    serializer_class = OrderTrackingSerializer
    
    def post(self, request):
        """Validate and return guest order information."""
        order_number = request.data.get('order_number', '').upper()
        email = request.data.get('email', '').lower()
        
        if not order_number or not email:
            return Response(
                {'error': 'Order number and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try matching shipping email first, then billing email
            order = Order.objects.filter(
                Q(order_number=order_number) & 
                (Q(shipping_email__iexact=email) | Q(billing_email__iexact=email))
            ).first()
            
            if not order:
                return Response(
                    {'error': 'Order not found. Please check your order number and email.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.serializer_class(order)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': 'Error retrieving order information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderStatusUpdateView(generics.UpdateAPIView):
    """
    Update order status (admin only).
    
    PATCH /api/orders/{id}/status/
    
    Request Body:
    {
        "status": "processing|shipped|delivered|cancelled|refunded",
        "notes": "Optional notes about the status change"
    }
    
    Creates a status history entry and updates relevant timestamps.
    Validates status transitions based on business rules.
    """
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.all()
    
    def perform_update(self, serializer):
        """Save the status update with additional logging."""
        order = serializer.save()
        
        # Log the status change
        print(f"Order {order.order_number} status updated to {order.status} by {self.request.user}")
        
        # Trigger additional actions based on status
        from utils.email import email_service
        
        if order.status == 'processing':
            # When order is processing, get shipping rates from Goshippo
            try:
                rates = goshippo_service.get_shipping_rates(order)
                print(f"Retrieved {len(rates)} shipping rates for order {order.order_number}")
                # Store rates or use the cheapest/fastest rate automatically
                # This is where business logic for rate selection would go
            except Exception as e:
                print(f"Failed to get shipping rates: {e}")
        
        elif order.status == 'shipped':
            # Send shipping notification email
            try:
                email_service.send_order_shipped_notification(order)
            except Exception as e:
                print(f"Failed to send shipping notification: {e}")
                
            # Update tracking information from Goshippo if transaction exists
            try:
                if order.goshippo_transaction_id:
                    transaction_status = goshippo_service.get_transaction_status(order.goshippo_transaction_id)
                    if transaction_status:
                        print(f"Transaction status for order {order.order_number}: {transaction_status['status']}")
            except Exception as e:
                print(f"Failed to get transaction status: {e}")
        
        elif order.status == 'delivered':
            # Send delivery confirmation email
            try:
                email_service.send_order_delivered_notification(order)
            except Exception as e:
                print(f"Failed to send delivery notification: {e}")
        
        elif order.status == 'cancelled':
            # Restore inventory quantities
            try:
                for item in order.items.all():
                    product = item.product
                    product.stock_quantity += item.quantity
                    product.save(update_fields=['stock_quantity'])
                print(f"Restored inventory for cancelled order {order.order_number}")
            except Exception as e:
                print(f"Failed to restore inventory: {e}")
    
    def update(self, request, *args, **kwargs):
        """Override update to return detailed order data after status update."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return detailed order data after update
        detail_serializer = OrderDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)


class OrderStatisticsView(generics.GenericAPIView):
    """
    Get order statistics for admin dashboard.
    
    GET /api/orders/statistics/
    
    Returns aggregate data about orders (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Calculate and return order statistics."""
        from django.db.models import Count, Sum, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        # Get date range from query params or default to last 30 days
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        orders = Order.objects.filter(created_at__gte=start_date)
        
        # Calculate statistics
        stats = {
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'average_order_value': orders.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'orders_by_status': orders.values('status').annotate(count=Count('id')),
            'orders_by_day': orders.extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(count=Count('id')).order_by('day'),
        }
        
        return Response(stats)


class OrderShippingRatesView(generics.GenericAPIView):
    """
    Get shipping rates for an order using Goshippo.
    
    GET /api/orders/{id}/shipping-rates/
    
    Returns available shipping rates for the order.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.all()
    
    def get(self, request, pk):
        """Get shipping rates for the order."""
        try:
            order = self.get_object()
                
            rates = goshippo_service.get_shipping_rates(order)
            
            return Response({
                'order_number': order.order_number,
                'rates': rates
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get shipping rates: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderCreateShipmentView(generics.GenericAPIView):
    """
    Create a shipment for an order using Goshippo.
    
    POST /api/orders/{id}/create-shipment/
    
    Request Body:
    {
        "rate_object_id": "goshippo_rate_id"
    }
    
    Creates a shipping transaction and updates the order with tracking information.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.all()
    
    def post(self, request, pk):
        """Create shipment for the order."""
        try:
            order = self.get_object()
            rate_object_id = request.data.get('rate_object_id')
            
            if not rate_object_id:
                return Response(
                    {'error': 'rate_object_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
                
            result = goshippo_service.process_order_shipment(order, rate_object_id)
            
            if result['success']:
                # Update order status to shipped
                order.status = 'shipped'
                order.save()
                
                # Create status history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status='shipped',
                    notes=f"Shipment created via Goshippo. Tracking: {result['tracking_number']}",
                    created_by=request.user
                )
                
                return Response({
                    'success': True,
                    'message': 'Shipment created successfully',
                    'tracking_number': result['tracking_number'],
                    'tracking_url': result.get('tracking_url'),
                    'label_url': result.get('label_url')
                })
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to create shipment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderTrackingUpdateView(generics.GenericAPIView):
    """
    Update tracking information for an order using Goshippo.
    
    POST /api/orders/{id}/update-tracking/
    
    Updates the order with latest tracking information from Goshippo.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.all()
    
    def post(self, request, pk):
        """Update tracking information for the order."""
        try:
            order = self.get_object()
            
            if not order.goshippo_transaction_id:
                return Response(
                    {'error': 'Order does not have a Goshippo transaction ID'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
                
            transaction_status = goshippo_service.get_transaction_status(order.goshippo_transaction_id)
            
            if transaction_status:
                return Response({
                    'order_number': order.order_number,
                    'tracking_number': transaction_status['tracking_number'],
                    'tracking_url': transaction_status['tracking_url'],
                    'status': transaction_status['status'],
                    'eta': transaction_status['eta']
                })
            else:
                return Response(
                    {'error': 'Failed to get tracking information'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'Failed to update tracking: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

