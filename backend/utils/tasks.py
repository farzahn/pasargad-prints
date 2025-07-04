from celery import shared_task
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_sessions():
    """Clean up expired database sessions"""
    expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired_sessions.count()
    expired_sessions.delete()
    
    logger.info(f"Cleaned up {count} expired sessions")
    return f"Deleted {count} expired sessions"

@shared_task
def clear_cache_pattern(pattern):
    """Clear cache entries matching a pattern"""
    try:
        if hasattr(cache._cache.get_client(), 'delete_pattern'):
            deleted = cache._cache.get_client().delete_pattern(pattern)
            logger.info(f"Cleared cache pattern '{pattern}', deleted {deleted} keys")
            return f"Deleted {deleted} cache keys"
        else:
            logger.warning("Cache backend doesn't support pattern deletion")
            return "Pattern deletion not supported"
    except Exception as e:
        logger.error(f"Error clearing cache pattern: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def send_async_email(subject, message, recipient_list, html_message=None):
    """Send email asynchronously"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

@shared_task
def warm_cache():
    """Warm up cache with frequently accessed data"""
    from products.models import Product, Category
    from products.serializers import ProductListSerializer, CategorySerializer
    
    try:
        # Cache categories
        categories = Category.objects.filter(is_active=True)
        category_data = CategorySerializer(categories, many=True).data
        cache.set('category_list:all', category_data, timeout=3600)
        
        # Cache recent products (replacing featured products functionality)
        recent_products = Product.objects.filter(
            is_active=True
        ).select_related('category').prefetch_related('images').order_by('-created_at')[:10]
        recent_data = ProductListSerializer(recent_products, many=True).data
        cache.set('recent_products', recent_data, timeout=3600)
        
        logger.info("Cache warmed up successfully")
        return "Cache warmed successfully"
        
    except Exception as e:
        logger.error(f"Error warming cache: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def cleanup_old_logs():
    """Clean up old log files"""
    import os
    from datetime import datetime, timedelta
    
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    cutoff_date = datetime.now() - timedelta(days=30)  # Keep 30 days of logs
    
    cleaned_count = 0
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_modified < cutoff_date:
                os.remove(filepath)
                cleaned_count += 1
                logger.info(f"Removed old log file: {filename}")
    
    return f"Cleaned up {cleaned_count} old log files"