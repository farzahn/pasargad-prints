from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order, OrderStatusHistory
import logging

logger = logging.getLogger(__name__)


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
    Generate a tracking number for an order.
    
    Args:
        order: Order instance
    
    Returns:
        str: Tracking number
    """
    import uuid
    # Generate a simple tracking number
    # In production, this would integrate with shipping provider
    tracking_prefix = 'PP'  # Pasargad Prints
    tracking_suffix = str(uuid.uuid4()).replace('-', '').upper()[:10]
    return f"{tracking_prefix}{tracking_suffix}"