#!/usr/bin/env python3

"""
Sample Data Migration Script for Pasargad Prints
This template can be copied and modified for specific data migration needs
"""

import os
import sys
import django
import logging
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order

logger = logging.getLogger(__name__)

def run_migration():
    """
    Main migration function - implement your data migration logic here
    This is a sample migration that demonstrates best practices
    """
    logger.info("Starting sample data migration")
    
    try:
        with transaction.atomic():
            # Sample migration: Update product categories
            update_product_categories()
            
            # Sample migration: Fix user data
            fix_user_data()
            
            # Sample migration: Update order statuses
            update_order_statuses()
            
        logger.info("Sample data migration completed successfully")
        
    except Exception as e:
        logger.error(f"Data migration failed: {str(e)}")
        raise

def update_product_categories():
    """Sample: Update product categories based on new business rules"""
    logger.info("Updating product categories...")
    
    # Example: Move products from old category to new category
    old_category_name = "Old Category"
    new_category_name = "New Category"
    
    try:
        old_category = Category.objects.get(name=old_category_name)
        new_category, created = Category.objects.get_or_create(
            name=new_category_name,
            defaults={'description': 'New category for migrated products'}
        )
        
        if created:
            logger.info(f"Created new category: {new_category_name}")
        
        # Update products
        products_updated = Product.objects.filter(category=old_category).update(category=new_category)
        logger.info(f"Updated {products_updated} products to new category")
        
        # Optionally delete old category if empty
        if not Product.objects.filter(category=old_category).exists():
            old_category.delete()
            logger.info(f"Deleted empty category: {old_category_name}")
            
    except Category.DoesNotExist:
        logger.warning(f"Category '{old_category_name}' not found, skipping category migration")

def fix_user_data():
    """Sample: Fix user data inconsistencies"""
    logger.info("Fixing user data...")
    
    User = get_user_model()
    
    # Example: Fix users with missing email domains
    users_without_proper_email = User.objects.filter(email__icontains='@example')
    
    for user in users_without_proper_email:
        # Generate a proper email based on username
        new_email = f"{user.username}@pasargadprints.com"
        
        # Check if email already exists
        if not User.objects.filter(email=new_email).exists():
            user.email = new_email
            user.save()
            logger.info(f"Updated email for user {user.username}")
        else:
            logger.warning(f"Email {new_email} already exists, skipping user {user.username}")

def update_order_statuses():
    """Sample: Update order statuses based on new business logic"""
    logger.info("Updating order statuses...")
    
    # Example: Update old 'processing' status to 'confirmed'
    orders_updated = Order.objects.filter(status='processing').update(status='confirmed')
    logger.info(f"Updated {orders_updated} orders from 'processing' to 'confirmed'")
    
    # Example: Mark old orders as completed
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=30)
    
    old_orders = Order.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['shipped', 'delivered']
    )
    
    completed_count = 0
    for order in old_orders:
        if order.status in ['shipped', 'delivered']:
            order.status = 'completed'
            order.save()
            completed_count += 1
    
    logger.info(f"Marked {completed_count} old orders as completed")

def rollback_migration():
    """
    Optional: Implement rollback logic if the migration needs to be reversed
    """
    logger.info("Starting rollback of sample data migration")
    
    try:
        with transaction.atomic():
            # Implement rollback logic here
            # This should reverse the changes made in run_migration()
            pass
            
        logger.info("Rollback completed successfully")
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        raise

if __name__ == '__main__':
    # Allow running the script directly
    import argparse
    
    parser = argparse.ArgumentParser(description='Sample Data Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        run_migration()