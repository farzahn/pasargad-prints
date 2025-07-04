from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from .models import Product
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_low_stock():
    """Check for products with low stock and notify admin"""
    low_stock_products = Product.objects.filter(
        is_active=True,
        stock_quantity__gt=0,
        stock_quantity__lte=F('low_stock_threshold')
    )
    
    if low_stock_products.exists():
        product_list = []
        for product in low_stock_products:
            product_list.append(
                f"- {product.name} (SKU: {product.sku}): "
                f"{product.stock_quantity} units remaining"
            )
        
        message = "The following products have low stock:\n\n" + "\n".join(product_list)
        
        send_mail(
            subject='Low Stock Alert - Pasargad Prints',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
        
        logger.info(f"Low stock alert sent for {len(product_list)} products")
    
    return f"Checked {Product.objects.filter(is_active=True).count()} products"

@shared_task
def update_product_search_vectors():
    """Update search vectors for all products"""
    products = Product.objects.filter(is_active=True)
    updated_count = 0
    
    for product in products:
        product.update_search_vector()
        updated_count += 1
    
    logger.info(f"Updated search vectors for {updated_count} products")
    return f"Updated {updated_count} product search vectors"

@shared_task
def process_product_image(product_id, image_id):
    """Process product image for optimization"""
    from .models import ProductImage
    from PIL import Image
    import io
    from django.core.files.base import ContentFile
    
    try:
        product_image = ProductImage.objects.get(id=image_id, product_id=product_id)
        
        if product_image.image:
            # Open and optimize image
            img = Image.open(product_image.image)
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Update the image field
            product_image.image.save(
                product_image.image.name,
                ContentFile(output.read()),
                save=True
            )
            
            logger.info(f"Processed image {image_id} for product {product_id}")
            return True
            
    except ProductImage.DoesNotExist:
        logger.error(f"ProductImage {image_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error processing image {image_id}: {str(e)}")
        return False