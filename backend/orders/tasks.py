from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging
import shippo
from .models import Order, OrderStatusHistory
from .utils import send_shipping_notification_email, update_order_status

logger = logging.getLogger(__name__)

# Configure Goshippo
shippo.api_key = getattr(settings, 'GOSHIPPO_API_KEY', '')


@shared_task
def create_goshippo_shipment(order_id):
    """
    Create a shipment in Goshippo for an order.
    
    Args:
        order_id (int): Order ID to create shipment for
        
    Returns:
        dict: Shipment details or error information
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # Create shipment address objects
        address_from = {
            "name": getattr(settings, 'GOSHIPPO_FROM_NAME', 'Pasargad Prints'),
            "street1": getattr(settings, 'GOSHIPPO_FROM_ADDRESS', ''),
            "city": getattr(settings, 'GOSHIPPO_FROM_CITY', ''),
            "state": getattr(settings, 'GOSHIPPO_FROM_STATE', ''),
            "zip": getattr(settings, 'GOSHIPPO_FROM_ZIP', ''),
            "country": getattr(settings, 'GOSHIPPO_FROM_COUNTRY', 'US'),
            "phone": getattr(settings, 'GOSHIPPO_FROM_PHONE', ''),
            "email": getattr(settings, 'GOSHIPPO_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        }
        
        address_to = {
            "name": order.shipping_name,
            "street1": order.shipping_address,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "zip": order.shipping_postal_code,
            "country": order.shipping_country,
            "phone": order.shipping_phone,
            "email": order.shipping_email
        }
        
        # Create parcel object
        parcel = {
            "length": str(getattr(settings, 'DEFAULT_PACKAGE_LENGTH', 12)),
            "width": str(getattr(settings, 'DEFAULT_PACKAGE_WIDTH', 12)),
            "height": str(getattr(settings, 'DEFAULT_PACKAGE_HEIGHT', 6)),
            "distance_unit": "in",
            "weight": str(order.total_weight),
            "mass_unit": "lb",
        }
        
        # Create shipment
        shipment = goshippo.Shipment.create(
            address_from=address_from,
            address_to=address_to,
            parcels=[parcel],
            purpose="PURCHASE",
            order_id=order.order_number,
            metadata=f"Order {order.order_number}",
            extra={
                "signature_confirmation": getattr(settings, 'GOSHIPPO_SIGNATURE_REQUIRED', False),
                "insurance": {
                    "amount": str(order.total_amount),
                    "currency": "USD"
                }
            }
        )
        
        # Update order with Goshippo shipment ID
        order.goshippo_object_id = shipment.object_id
        order.save()
        
        logger.info(f"Created Goshippo shipment {shipment.object_id} for order {order.order_number}")
        
        # Get cheapest rate automatically
        cheapest_rate = min(shipment.rates, key=lambda x: float(x.amount))
        
        return {
            'success': True,
            'shipment_id': shipment.object_id,
            'order_number': order.order_number,
            'cheapest_rate': {
                'amount': cheapest_rate.amount,
                'currency': cheapest_rate.currency,
                'provider': cheapest_rate.provider,
                'service': cheapest_rate.servicelevel.name,
                'estimated_days': cheapest_rate.estimated_days
            }
        }
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for Goshippo shipment creation")
        return {'success': False, 'error': 'Order not found'}
    except Exception as e:
        logger.error(f"Error creating Goshippo shipment for order {order_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def purchase_goshippo_label(order_id, rate_id=None):
    """
    Purchase a shipping label through Goshippo for an order.
    
    Args:
        order_id (int): Order ID
        rate_id (str): Specific rate ID to purchase (optional, will use cheapest if not provided)
        
    Returns:
        dict: Transaction details or error information
    """
    try:
        order = Order.objects.get(id=order_id)
        
        if not order.goshippo_object_id:
            # Create shipment first
            shipment_result = create_goshippo_shipment(order_id)
            if not shipment_result.get('success'):
                return shipment_result
        
        # Get shipment details
        shipment = goshippo.Shipment.retrieve(order.goshippo_object_id)
        
        # Select rate (use provided rate_id or cheapest)
        if rate_id:
            selected_rate = next((rate for rate in shipment.rates if rate.object_id == rate_id), None)
            if not selected_rate:
                return {'success': False, 'error': 'Invalid rate ID'}
        else:
            selected_rate = min(shipment.rates, key=lambda x: float(x.amount))
        
        # Purchase label
        transaction = goshippo.Transaction.create(
            rate=selected_rate.object_id,
            label_file_type="PDF",
            async_processing=False
        )
        
        if transaction.status == "SUCCESS":
            # Update order with tracking information
            order.tracking_number = transaction.tracking_number
            order.goshippo_transaction_id = transaction.object_id
            order.goshippo_label_url = transaction.label_url
            order.goshippo_tracking_url = transaction.tracking_url_provider
            order.carrier = selected_rate.provider
            order.service_level = selected_rate.servicelevel.name
            order.shipping_cost = Decimal(selected_rate.amount)
            order.save()
            
            # Update order status to shipped
            update_order_status(order, 'shipped', notes=f'Label purchased via Goshippo. Tracking: {transaction.tracking_number}')
            
            logger.info(f"Purchased Goshippo label for order {order.order_number}, tracking: {transaction.tracking_number}")
            
            return {
                'success': True,
                'transaction_id': transaction.object_id,
                'tracking_number': transaction.tracking_number,
                'label_url': transaction.label_url,
                'order_number': order.order_number,
                'shipping_cost': selected_rate.amount
            }
        else:
            logger.error(f"Failed to purchase Goshippo label for order {order.order_number}: {transaction.messages}")
            return {'success': False, 'error': transaction.messages}
            
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for Goshippo label purchase")
        return {'success': False, 'error': 'Order not found'}
    except Exception as e:
        logger.error(f"Error purchasing Goshippo label for order {order_id}: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def track_goshippo_shipments():
    """
    Track all shipped orders using Goshippo API.
    Updates order status based on tracking information.
    """
    try:
        # Get all shipped orders with tracking numbers
        shipped_orders = Order.objects.filter(
            status='shipped',
            tracking_number__isnull=False,
            goshippo_transaction_id__isnull=False
        ).exclude(tracking_number='')
        
        updated_count = 0
        
        for order in shipped_orders:
            try:
                # Get tracking information
                tracking = goshippo.Track.create(
                    carrier=order.goshippo_transaction_id,
                    tracking_number=order.tracking_number
                )
                
                if tracking.tracking_status:
                    # Map Goshippo status to our order status
                    status_mapping = {
                        'DELIVERED': 'delivered',
                        'RETURNED': 'cancelled',
                        'FAILURE': 'cancelled',
                        'UNKNOWN': 'shipped'  # Keep as shipped if unknown
                    }
                    
                    new_status = status_mapping.get(tracking.tracking_status.status, 'shipped')
                    
                    if new_status != order.status:
                        update_order_status(
                            order, 
                            new_status, 
                            notes=f'Status updated from Goshippo tracking: {tracking.tracking_status.status}'
                        )
                        updated_count += 1
                        
                        # Update delivery timestamp if delivered
                        if new_status == 'delivered' and not order.delivered_at:
                            order.delivered_at = timezone.now()
                            order.save()
                
            except Exception as e:
                logger.error(f"Error tracking order {order.order_number}: {str(e)}")
                continue
        
        logger.info(f"Tracked {shipped_orders.count()} orders, updated {updated_count} statuses")
        return f"Tracked {shipped_orders.count()} orders, updated {updated_count} statuses"
        
    except Exception as e:
        logger.error(f"Error in track_goshippo_shipments: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def sync_goshippo_rates():
    """
    Sync shipping rates for pending orders to get updated pricing.
    """
    try:
        # Get orders that are processing and need shipping rates
        processing_orders = Order.objects.filter(
            status='processing',
            fulfillment_method='shipping',
            goshippo_object_id__isnull=True
        )
        
        synced_count = 0
        
        for order in processing_orders:
            try:
                result = create_goshippo_shipment(order.id)
                if result.get('success'):
                    synced_count += 1
                    
            except Exception as e:
                logger.error(f"Error syncing rates for order {order.order_number}: {str(e)}")
                continue
        
        logger.info(f"Synced shipping rates for {synced_count} orders")
        return f"Synced shipping rates for {synced_count} orders"
        
    except Exception as e:
        logger.error(f"Error in sync_goshippo_rates: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_goshippo_shipments():
    """
    Clean up old Goshippo shipments that were never converted to transactions.
    """
    try:
        # Find orders with shipment IDs but no transaction IDs, older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        old_orders = Order.objects.filter(
            goshippo_object_id__isnull=False,
            goshippo_transaction_id__isnull=True,
            created_at__lt=cutoff_date
        )
        
        cleaned_count = 0
        
        for order in old_orders:
            try:
                # Clear the shipment ID to allow recreation if needed
                order.goshippo_object_id = None
                order.save()
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"Error cleaning up order {order.order_number}: {str(e)}")
                continue
        
        logger.info(f"Cleaned up {cleaned_count} old Goshippo shipments")
        return f"Cleaned up {cleaned_count} old Goshippo shipments"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_goshippo_shipments: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_shipping_rate_notifications():
    """
    Send notifications about shipping rates for orders awaiting customer confirmation.
    """
    try:
        # Get orders that have been in processing status for more than 2 hours
        cutoff_time = timezone.now() - timedelta(hours=2)
        awaiting_orders = Order.objects.filter(
            status='processing',
            fulfillment_method='shipping',
            updated_at__lt=cutoff_time,
            goshippo_object_id__isnull=False
        )
        
        notified_count = 0
        
        for order in awaiting_orders:
            try:
                # Get shipment details
                shipment = goshippo.Shipment.retrieve(order.goshippo_object_id)
                
                if shipment.rates:
                    # Send email with shipping options
                    cheapest_rate = min(shipment.rates, key=lambda x: float(x.amount))
                    
                    subject = f'Shipping Options Available - Order {order.order_number}'
                    message = f"""
                    Your order is ready for shipping!
                    
                    Order Number: {order.order_number}
                    
                    Recommended Shipping Option:
                    - Carrier: {cheapest_rate.provider}
                    - Service: {cheapest_rate.servicelevel.name}
                    - Cost: ${cheapest_rate.amount}
                    - Estimated Delivery: {cheapest_rate.estimated_days} days
                    
                    Visit {settings.FRONTEND_URL}/orders/{order.order_number} to confirm shipping.
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [order.shipping_email],
                        fail_silently=False,
                    )
                    
                    notified_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending shipping notification for order {order.order_number}: {str(e)}")
                continue
        
        logger.info(f"Sent shipping rate notifications for {notified_count} orders")
        return f"Sent shipping rate notifications for {notified_count} orders"
        
    except Exception as e:
        logger.error(f"Error in send_shipping_rate_notifications: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def validate_goshippo_addresses():
    """
    Validate shipping addresses for new orders using Goshippo address validation.
    """
    try:
        # Get recent orders with unvalidated addresses
        recent_orders = Order.objects.filter(
            status='pending',
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        validated_count = 0
        
        for order in recent_orders:
            try:
                # Validate shipping address
                address_validation = goshippo.Address.create(
                    name=order.shipping_name,
                    street1=order.shipping_address,
                    city=order.shipping_city,
                    state=order.shipping_state,
                    zip=order.shipping_postal_code,
                    country=order.shipping_country,
                    validate=True
                )
                
                if address_validation.validation_results:
                    validation_result = address_validation.validation_results
                    
                    # Log validation issues
                    if not validation_result.is_valid:
                        logger.warning(f"Address validation failed for order {order.order_number}: {validation_result.messages}")
                        
                        # Create order status history entry
                        OrderStatusHistory.objects.create(
                            order=order,
                            status=order.status,
                            notes=f"Address validation issues: {validation_result.messages}",
                            created_by=None
                        )
                    else:
                        validated_count += 1
                        
            except Exception as e:
                logger.error(f"Error validating address for order {order.order_number}: {str(e)}")
                continue
        
        logger.info(f"Validated addresses for {validated_count} orders")
        return f"Validated addresses for {validated_count} orders"
        
    except Exception as e:
        logger.error(f"Error in validate_goshippo_addresses: {str(e)}")
        return f"Error: {str(e)}"