#!/usr/bin/env python3

"""
Production Data Cleanup Migration for Pasargad Prints
Cleans up test data, orphaned records, and optimizes database
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta
from django.db import transaction, connection
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, F

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product, Category, ProductImage
from orders.models import Order, OrderItem
from payments.models import Payment
from cart.models import Cart, CartItem
from wishlist.models import Wishlist, WishlistItem
from analytics.models import PageView, UserSession

logger = logging.getLogger(__name__)

def run_migration():
    """
    Main cleanup migration function
    """
    logger.info("Starting production data cleanup migration")
    
    try:
        with transaction.atomic():
            # Remove test data
            remove_test_data()
            
            # Clean up orphaned records
            cleanup_orphaned_records()
            
            # Remove expired sessions and temporary data
            cleanup_expired_data()
            
            # Optimize product data
            optimize_product_data()
            
            # Clean up analytics data
            cleanup_analytics_data()
            
            # Update database statistics
            update_database_statistics()
            
        logger.info("Production data cleanup migration completed successfully")
        
    except Exception as e:
        logger.error(f"Data cleanup migration failed: {str(e)}")
        raise

def remove_test_data():
    """Remove test users, orders, and other test data"""
    logger.info("Removing test data...")
    
    User = get_user_model()
    
    # Remove test users (emails containing 'test', 'example', or 'demo')
    test_patterns = ['test', 'example', 'demo', 'sample', 'fake']
    test_users = User.objects.filter(
        Q(email__icontains='test') |
        Q(email__icontains='example') |
        Q(email__icontains='demo') |
        Q(email__icontains='sample') |
        Q(username__icontains='test') |
        Q(username__icontains='demo')
    ).exclude(is_staff=True)  # Keep staff users
    
    test_user_count = test_users.count()
    
    # Remove associated data first
    test_user_ids = list(test_users.values_list('id', flat=True))
    
    # Remove test orders
    test_orders = Order.objects.filter(user_id__in=test_user_ids)
    test_order_count = test_orders.count()
    test_orders.delete()
    
    # Remove test users
    test_users.delete()
    
    logger.info(f"Removed {test_user_count} test users and {test_order_count} test orders")
    
    # Remove test products
    test_products = Product.objects.filter(
        Q(name__icontains='test') |
        Q(name__icontains='sample') |
        Q(description__icontains='test product')
    )
    test_product_count = test_products.count()
    test_products.delete()
    
    logger.info(f"Removed {test_product_count} test products")

def cleanup_orphaned_records():
    """Remove orphaned records that have no valid foreign key references"""
    logger.info("Cleaning up orphaned records...")
    
    # Remove orphaned cart items
    orphaned_cart_items = CartItem.objects.filter(cart__isnull=True)
    cart_items_count = orphaned_cart_items.count()
    orphaned_cart_items.delete()
    
    # Remove orphaned order items
    orphaned_order_items = OrderItem.objects.filter(order__isnull=True)
    order_items_count = orphaned_order_items.count()
    orphaned_order_items.delete()
    
    # Remove orphaned product images
    orphaned_images = ProductImage.objects.filter(product__isnull=True)
    images_count = orphaned_images.count()
    orphaned_images.delete()
    
    # Remove orphaned wishlist items
    orphaned_wishlist_items = WishlistItem.objects.filter(
        Q(wishlist__isnull=True) | Q(product__isnull=True)
    )
    wishlist_items_count = orphaned_wishlist_items.count()
    orphaned_wishlist_items.delete()
    
    # Remove orphaned payments
    orphaned_payments = Payment.objects.filter(order__isnull=True)
    payments_count = orphaned_payments.count()
    orphaned_payments.delete()
    
    logger.info(f"Removed orphaned records: {cart_items_count} cart items, "
                f"{order_items_count} order items, {images_count} images, "
                f"{wishlist_items_count} wishlist items, {payments_count} payments")

def cleanup_expired_data():
    """Remove expired sessions, carts, and temporary data"""
    logger.info("Cleaning up expired data...")
    
    # Remove old anonymous carts (older than 30 days)
    cart_cutoff = datetime.now() - timedelta(days=30)
    old_carts = Cart.objects.filter(
        user__isnull=True,
        created_at__lt=cart_cutoff
    )
    old_cart_count = old_carts.count()
    old_carts.delete()
    
    # Remove old page views (keep only last 90 days)
    pageview_cutoff = datetime.now() - timedelta(days=90)
    old_pageviews = PageView.objects.filter(timestamp__lt=pageview_cutoff)
    pageview_count = old_pageviews.count()
    old_pageviews.delete()
    
    # Remove old user sessions (keep only last 30 days)
    session_cutoff = datetime.now() - timedelta(days=30)
    old_sessions = UserSession.objects.filter(created_at__lt=session_cutoff)
    session_count = old_sessions.count()
    old_sessions.delete()
    
    # Remove empty carts
    empty_carts = Cart.objects.annotate(
        item_count=Count('items')
    ).filter(item_count=0)
    empty_cart_count = empty_carts.count()
    empty_carts.delete()
    
    # Remove empty wishlists
    empty_wishlists = Wishlist.objects.annotate(
        item_count=Count('items')
    ).filter(item_count=0)
    empty_wishlist_count = empty_wishlists.count()
    empty_wishlists.delete()
    
    logger.info(f"Removed expired data: {old_cart_count} old carts, "
                f"{pageview_count} old page views, {session_count} old sessions, "
                f"{empty_cart_count} empty carts, {empty_wishlist_count} empty wishlists")

def optimize_product_data():
    """Optimize product data and fix inconsistencies"""
    logger.info("Optimizing product data...")
    
    # Remove products with zero or negative prices
    invalid_products = Product.objects.filter(Q(price__lte=0) | Q(price__isnull=True))
    invalid_count = invalid_products.count()
    invalid_products.delete()
    
    # Remove products with no category
    no_category_products = Product.objects.filter(category__isnull=True)
    no_category_count = no_category_products.count()
    
    # Try to assign a default category or remove
    default_category, created = Category.objects.get_or_create(
        name='Uncategorized',
        defaults={'description': 'Products without a specific category'}
    )
    
    no_category_products.update(category=default_category)
    
    # Remove duplicate product images
    duplicate_images = ProductImage.objects.values('product', 'image').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    duplicates_removed = 0
    for duplicate in duplicate_images:
        # Keep the first image, remove the rest
        images_to_remove = ProductImage.objects.filter(
            product=duplicate['product'],
            image=duplicate['image']
        )[1:]  # Skip the first one
        
        duplicates_removed += images_to_remove.count()
        images_to_remove.delete()
    
    # Update product search vectors if available
    try:
        from django.contrib.postgres.search import SearchVector
        Product.objects.update(
            search_vector=SearchVector('name', weight='A') + 
                         SearchVector('description', weight='B')
        )
        logger.info("Updated product search vectors")
    except ImportError:
        logger.info("PostgreSQL search not available, skipping search vector update")
    
    logger.info(f"Optimized product data: removed {invalid_count} invalid products, "
                f"categorized {no_category_count} products, "
                f"removed {duplicates_removed} duplicate images")

def cleanup_analytics_data():
    """Clean up old analytics data and optimize tables"""
    logger.info("Cleaning up analytics data...")
    
    # Keep only last 6 months of detailed analytics
    analytics_cutoff = datetime.now() - timedelta(days=180)
    
    # Remove old page views (keep aggregated data)
    old_analytics = PageView.objects.filter(timestamp__lt=analytics_cutoff)
    analytics_count = old_analytics.count()
    
    # Before deleting, create aggregated data if needed
    # This is a simplified example - you might want more sophisticated aggregation
    
    old_analytics.delete()
    
    logger.info(f"Removed {analytics_count} old analytics records")

def update_database_statistics():
    """Update database statistics for better query performance"""
    logger.info("Updating database statistics...")
    
    try:
        with connection.cursor() as cursor:
            # Update table statistics
            cursor.execute("ANALYZE;")
            
            # Reindex if needed (be careful with this in production)
            # cursor.execute("REINDEX DATABASE pasargad_prints_prod;")
            
            logger.info("Database statistics updated successfully")
            
    except Exception as e:
        logger.warning(f"Could not update database statistics: {str(e)}")

def get_cleanup_stats():
    """Get statistics about what will be cleaned up (for dry-run)"""
    User = get_user_model()
    
    stats = {}
    
    # Test data stats
    test_users = User.objects.filter(
        Q(email__icontains='test') |
        Q(email__icontains='example') |
        Q(email__icontains='demo') |
        Q(username__icontains='test')
    ).exclude(is_staff=True)
    
    stats['test_users'] = test_users.count()
    stats['test_orders'] = Order.objects.filter(user__in=test_users).count()
    
    # Orphaned records stats
    stats['orphaned_cart_items'] = CartItem.objects.filter(cart__isnull=True).count()
    stats['orphaned_order_items'] = OrderItem.objects.filter(order__isnull=True).count()
    stats['orphaned_images'] = ProductImage.objects.filter(product__isnull=True).count()
    
    # Expired data stats
    cart_cutoff = datetime.now() - timedelta(days=30)
    stats['old_carts'] = Cart.objects.filter(
        user__isnull=True, 
        created_at__lt=cart_cutoff
    ).count()
    
    pageview_cutoff = datetime.now() - timedelta(days=90)
    stats['old_pageviews'] = PageView.objects.filter(timestamp__lt=pageview_cutoff).count()
    
    return stats

def rollback_migration():
    """
    This cleanup migration is not easily reversible.
    Log what was removed for potential recovery from backups.
    """
    logger.warning("Cleanup migration is not reversible. "
                  "Use database backups to restore removed data if needed.")
    
    # Could implement some recovery logic here if specific items need to be restored
    # But generally, cleanup migrations should not be rolled back

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Data Cleanup Migration')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned up')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration (limited)')
    args = parser.parse_args()
    
    if args.dry_run:
        stats = get_cleanup_stats()
        print("Cleanup Statistics (DRY RUN):")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif args.rollback:
        rollback_migration()
    else:
        run_migration()