from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import Cart, CartItem
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_abandoned_carts():
    """
    Process abandoned carts and send reminder emails
    """
    # Find carts that haven't been updated in 24 hours
    cutoff_time = timezone.now() - timedelta(hours=24)
    abandoned_carts = Cart.objects.filter(
        updated_at__lt=cutoff_time,
        items__isnull=False  # Has items
    ).distinct()
    
    processed_count = 0
    for cart in abandoned_carts:
        if cart.user and cart.user.email:
            # Send reminder email
            send_abandoned_cart_reminder.delay(cart.id)
            processed_count += 1
    
    logger.info(f"Processed {processed_count} abandoned carts")
    return f"Processed {processed_count} abandoned carts"

@shared_task
def send_abandoned_cart_reminder(cart_id):
    """
    Send abandoned cart reminder email
    """
    try:
        cart = Cart.objects.get(id=cart_id)
        if not cart.user or not cart.user.email:
            return False
        
        # Get cart items
        items = cart.items.select_related('product').all()
        if not items.exists():
            return False
        
        # Build email content
        item_list = []
        total = 0
        for item in items:
            subtotal = item.quantity * item.product.price
            total += subtotal
            item_list.append(
                f"- {item.product.name} (Quantity: {item.quantity}) - ${subtotal}"
            )
        
        message = f"""
        Hi {cart.user.first_name or 'there'},
        
        You have items waiting in your cart at Pasargad Prints!
        
        Your cart contains:
        {chr(10).join(item_list)}
        
        Total: ${total}
        
        Complete your purchase here: {settings.FRONTEND_URL}/cart
        
        Best regards,
        Pasargad Prints Team
        """
        
        send_mail(
            subject='You have items in your cart - Pasargad Prints',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cart.user.email],
            fail_silently=False,
        )
        
        logger.info(f"Sent abandoned cart reminder for cart {cart_id}")
        return True
        
    except Cart.DoesNotExist:
        logger.error(f"Cart {cart_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending abandoned cart reminder: {str(e)}")
        return False

@shared_task
def cleanup_old_carts():
    """
    Clean up old anonymous carts
    """
    # Delete anonymous carts older than 30 days
    cutoff_time = timezone.now() - timedelta(days=30)
    old_carts = Cart.objects.filter(
        user__isnull=True,
        created_at__lt=cutoff_time
    )
    
    count = old_carts.count()
    old_carts.delete()
    
    logger.info(f"Deleted {count} old anonymous carts")
    return f"Deleted {count} old anonymous carts"

@shared_task
def sync_cart_totals():
    """
    Sync cart totals to ensure consistency
    """
    carts = Cart.objects.all()
    updated_count = 0
    
    for cart in carts:
        old_total = cart.total
        cart.update_total()
        if old_total != cart.total:
            updated_count += 1
    
    logger.info(f"Updated totals for {updated_count} carts")
    return f"Updated {updated_count} cart totals"