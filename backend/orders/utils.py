from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, OrderStatusHistory
import logging
import shippo
from decimal import Decimal

logger = logging.getLogger(__name__)

# Configure Goshippo
shippo.api_key = getattr(settings, 'GOSHIPPO_API_KEY', '')


def send_order_confirmation_email(order):
    """Send order confirmation email to customer."""
    try:
        subject = f'Order Confirmation - {order.order_number}'
        message = f"""
        Thank you for your order!
        
        Order Number: {order.order_number}
        Total: ${order.total_amount}
        
        We'll send you a shipping confirmation when your order ships.
        
        You can track your order at: {settings.FRONTEND_URL}/orders/track/{order.order_number}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.billing_email],
            fail_silently=False,
        )
        logger.info(f"Order confirmation email sent for order {order.order_number}")
    except Exception as e:
        logger.error(f"Failed to send order confirmation email: {str(e)}")


def send_shipping_notification_email(order):
    """Send shipping notification email to customer."""
    try:
        subject = f'Your Order Has Shipped - {order.order_number}'
        message = f"""
        Good news! Your order has shipped.
        
        Order Number: {order.order_number}
        Tracking Number: {order.tracking_number or 'Will be provided soon'}
        
        You can track your package at: {settings.FRONTEND_URL}/orders/track/{order.tracking_number or order.order_number}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.shipping_email],
            fail_silently=False,
        )
        logger.info(f"Shipping notification email sent for order {order.order_number}")
    except Exception as e:
        logger.error(f"Failed to send shipping notification email: {str(e)}")


def update_order_status(order, new_status, user=None, notes=''):
    """
    Update order status and create history entry.
    
    Args:
        order: Order instance
        new_status: New status value
        user: User making the change
        notes: Optional notes about the change
    
    Returns:
        OrderStatusHistory instance
    """
    old_status = order.status
    order.status = new_status
    order.save()
    
    # Create history entry
    history = OrderStatusHistory.objects.create(
        order=order,
        status=new_status,
        notes=notes or f"Status changed from {old_status} to {new_status}",
        created_by=user
    )
    
    # Send notifications based on status
    if new_status == 'shipped':
        send_shipping_notification_email(order)
    
    logger.info(f"Order {order.order_number} status updated from {old_status} to {new_status}")
    
    return history


def calculate_order_totals(order):
    """
    Recalculate order totals based on items.
    
    Args:
        order: Order instance
    
    Returns:
        dict with subtotal, tax_amount, shipping_cost, and total_amount
    """
    from decimal import Decimal
    
    # Calculate subtotal from items
    subtotal = sum(item.total_price for item in order.items.all())
    
    # Calculate tax (example: 8% tax rate)
    tax_rate = Decimal('0.08')
    tax_amount = subtotal * tax_rate
    
    # Calculate shipping (example logic)
    total_weight = order.total_weight
    if total_weight <= 1:
        shipping_cost = Decimal('5.00')
    elif total_weight <= 5:
        shipping_cost = Decimal('10.00')
    else:
        shipping_cost = Decimal('15.00')
    
    # Free shipping for orders over $100
    if subtotal >= Decimal('100.00'):
        shipping_cost = Decimal('0.00')
    
    total_amount = subtotal + tax_amount + shipping_cost
    
    return {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'total_amount': total_amount
    }


def generate_tracking_number(order):
    """
    Generate a tracking number for an order using Goshippo.
    
    Args:
        order: Order instance
    
    Returns:
        str: Tracking number from Goshippo or fallback
    """
    # Try to get tracking number from Goshippo if shipment exists
    if order.goshippo_transaction_id:
        from utils.goshippo_service import shippo_service
        try:
            # Track existing shipment to get tracking number
            tracking_result = goshippo_service.track_shipment(order.tracking_number)
            if tracking_result.get('tracking_number'):
                return tracking_result['tracking_number']
        except Exception as e:
            logger.warning(f"Failed to get Goshippo tracking number: {e}")
    
    # Fallback to local generation
    import uuid
    tracking_prefix = 'PP'  # Pasargad Prints
    tracking_suffix = str(uuid.uuid4()).replace('-', '').upper()[:10]
    return f"{tracking_prefix}{tracking_suffix}"


def create_goshippo_shipment(order, to_address=None):
    """
    Create a Goshippo shipment for an order.
    
    Args:
        order: Order instance
        to_address: Optional custom shipping address
    
    Returns:
        dict: Shipment creation result
    """
    from django.conf import settings
    from utils.goshippo_service import shippo_service
    
    try:
        # Use order shipping address if to_address not provided
        if not to_address:
            to_address = {
                'name': order.shipping_name,
                'street1': order.shipping_address.split('\n')[0] if '\n' in order.shipping_address else order.shipping_address,
                'street2': order.shipping_address.split('\n')[1] if '\n' in order.shipping_address and len(order.shipping_address.split('\n')) > 1 else '',
                'city': order.shipping_city,
                'state': order.shipping_state,
                'zip': order.shipping_postal_code,
                'country': order.shipping_country,
                'phone': order.shipping_phone,
                'email': order.shipping_email,
            }
        
        # Get origin address from settings
        from_address = getattr(settings, 'SHIPPING_ORIGIN', {})
        
        # Calculate parcel details from order
        parcel_details = {
            'weight': max(float(order.total_weight), 1.0),
            'length': 12,  # Default dimensions
            'width': 9,
            'height': 6,
            'distance_unit': 'in',
            'mass_unit': 'lb',
        }
        
        # Get shipping rates
        rates_result = goshippo_service.get_shipping_rates(
            from_address=from_address,
            to_address=to_address,
            parcel_details=parcel_details
        )
        
        if rates_result.get('status') == 'success':
            # Store shipment ID
            order.goshippo_object_id = rates_result.get('shipment_id')
            order.save(update_fields=['goshippo_object_id'])
            
            logger.info(f"Created Goshippo shipment for order {order.order_number}")
            return rates_result
        else:
            logger.error(f"Failed to create Goshippo shipment: {rates_result.get('error')}")
            return rates_result
            
    except Exception as e:
        logger.error(f"Error creating Goshippo shipment for order {order.order_number}: {e}")
        return {'error': str(e), 'status': 'error'}


def send_delivery_notification_email(order):
    """Send delivery notification email to customer."""
    try:
        subject = f'Your Order Has Been Delivered - {order.order_number}'
        message = f"""
        Great news! Your order has been delivered.
        
        Order Number: {order.order_number}
        Tracking Number: {order.tracking_number or 'N/A'}
        
        Thank you for choosing Pasargad Prints!
        
        If you have any questions about your order, please contact us.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.shipping_email],
            fail_silently=False,
        )
        logger.info(f"Delivery notification email sent for order {order.order_number}")
    except Exception as e:
        logger.error(f"Failed to send delivery notification email: {str(e)}")


def get_goshippo_shipping_rates(order):
    """
    Get shipping rates from Goshippo for an order.
    
    Args:
        order: Order instance
    
    Returns:
        list: List of shipping rates
    """
    try:
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
            purpose="QUOTE"
        )
        
        # Format rates for easy consumption
        rates = []
        for rate in shipment.rates:
            rates.append({
                'rate_id': rate.object_id,
                'provider': rate.provider,
                'service': rate.servicelevel.name,
                'amount': float(rate.amount),
                'currency': rate.currency,
                'estimated_days': rate.estimated_days,
                'duration_terms': rate.duration_terms
            })
        
        return sorted(rates, key=lambda x: x['amount'])
        
    except Exception as e:
        logger.error(f"Error getting Goshippo rates for order {order.order_number}: {str(e)}")
        return []


def validate_goshippo_address(order):
    """
    Validate shipping address using Goshippo API.
    
    Args:
        order: Order instance
        
    Returns:
        dict: Validation result
    """
    try:
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
            return {
                'is_valid': validation_result.is_valid,
                'messages': validation_result.messages,
                'suggested_address': {
                    'street1': address_validation.street1,
                    'city': address_validation.city,
                    'state': address_validation.state,
                    'zip': address_validation.zip,
                    'country': address_validation.country
                } if validation_result.is_valid else None
            }
        
        return {'is_valid': True, 'messages': [], 'suggested_address': None}
        
    except Exception as e:
        logger.error(f"Error validating address for order {order.order_number}: {str(e)}")
        return {'is_valid': False, 'messages': [str(e)], 'suggested_address': None}


def get_goshippo_tracking_info(tracking_number, carrier=None):
    """
    Get tracking information from Goshippo.
    
    Args:
        tracking_number: Tracking number
        carrier: Carrier name (optional)
        
    Returns:
        dict: Tracking information
    """
    try:
        if carrier:
            tracking = goshippo.Track.create(
                carrier=carrier,
                tracking_number=tracking_number
            )
        else:
            tracking = goshippo.Track.create(
                tracking_number=tracking_number
            )
        
        if tracking.tracking_status:
            return {
                'status': tracking.tracking_status.status,
                'status_details': tracking.tracking_status.status_details,
                'status_date': tracking.tracking_status.status_date,
                'location': tracking.tracking_status.location,
                'tracking_history': [
                    {
                        'status': event.status,
                        'status_details': event.status_details,
                        'status_date': event.status_date,
                        'location': event.location
                    }
                    for event in tracking.tracking_history
                ]
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting tracking info for {tracking_number}: {str(e)}")
        return None


def calculate_goshippo_shipping_cost(order, rate_id):
    """
    Calculate shipping cost using a specific Goshippo rate.
    
    Args:
        order: Order instance
        rate_id: Goshippo rate ID
        
    Returns:
        Decimal: Shipping cost
    """
    try:
        rates = get_goshippo_shipping_rates(order)
        selected_rate = next((rate for rate in rates if rate['rate_id'] == rate_id), None)
        
        if selected_rate:
            return Decimal(str(selected_rate['amount']))
        
        return Decimal('0.00')
        
    except Exception as e:
        logger.error(f"Error calculating shipping cost for order {order.order_number}: {str(e)}")
        return Decimal('0.00')


def get_goshippo_label_url(order):
    """
    Get shipping label URL from Goshippo.
    
    Args:
        order: Order instance
        
    Returns:
        str: Label URL or None
    """
    try:
        if order.goshippo_transaction_id:
            transaction = goshippo.Transaction.retrieve(order.goshippo_transaction_id)
            return transaction.label_url
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting label URL for order {order.order_number}: {str(e)}")
        return None