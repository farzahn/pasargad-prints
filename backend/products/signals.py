from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category, ProductImage, ProductReview
from .tasks import update_product_search_vectors, process_product_image
from utils.cache import invalidate_product_cache, invalidate_cache
import logging

logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=Product)
def invalidate_product_caches(sender, instance, **kwargs):
    """Invalidate caches when product is saved or deleted"""
    # Invalidate specific product cache
    cache_keys = [
        f'product:{instance.id}',
        f'product:{instance.id}:*',
        'product_list:*',
        'featured_products',
    ]
    
    if instance.category_id:
        cache_keys.append(f'category:{instance.category_id}:products')
    
    invalidate_cache(cache_keys)
    
    # Update search vector asynchronously (only if Celery is available)
    if kwargs.get('created', False) or not instance.search_vector:
        try:
            from django.conf import settings
            if getattr(settings, 'USE_REDIS_CACHE', False):
                update_product_search_vectors.delay()
        except Exception as e:
            logger.warning(f"Could not queue search vector update task: {e}")
    
    logger.info(f"Invalidated cache for product {instance.id}")

@receiver([post_save, post_delete], sender=Category)
def invalidate_category_caches(sender, instance, **kwargs):
    """Invalidate caches when category is saved or deleted"""
    cache_keys = [
        'category_list',
        'category_list:*',
        f'category:{instance.id}:*',
        'product_list:*',  # Products might be filtered by category
    ]
    
    invalidate_cache(cache_keys)
    logger.info(f"Invalidated cache for category {instance.id}")

@receiver(post_save, sender=ProductImage)
def process_new_product_image(sender, instance, created, **kwargs):
    """Process newly uploaded product images"""
    if created and instance.image:
        # Process image asynchronously
        process_product_image.delay(instance.product_id, instance.id)
        
        # Invalidate product cache
        invalidate_product_cache(product_id=instance.product_id)

@receiver([post_save, post_delete], sender=ProductReview)
def invalidate_review_caches(sender, instance, **kwargs):
    """Invalidate caches when review is saved or deleted"""
    # Invalidate product detail cache (includes reviews)
    cache_keys = [
        f'product:{instance.product_id}',
        f'product:{instance.product_id}:reviews',
    ]
    
    invalidate_cache(cache_keys)
    logger.info(f"Invalidated cache for product {instance.product_id} after review change")

@receiver(pre_save, sender=Product)
def track_price_changes(sender, instance, **kwargs):
    """Track price changes for analytics"""
    if instance.pk:
        try:
            old_product = Product.objects.get(pk=instance.pk)
            if old_product.price != instance.price:
                logger.info(
                    f"Product {instance.id} price changed from "
                    f"{old_product.price} to {instance.price}"
                )
                # Could trigger price drop notifications here
        except Product.DoesNotExist:
            pass