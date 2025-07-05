"""
Django management command to migrate existing ShipStation data to Goshippo format.
This command helps transition from ShipStation to Goshippo by migrating order data.

Goshippo SDK Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from orders.models import Order
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate existing ShipStation order data to Goshippo format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of orders to process in each batch',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting ShipStation to Goshippo migration {'(DRY RUN)' if dry_run else ''}"
            )
        )
        
        # Find orders that might have old ShipStation data
        # Since we've already renamed the field, we'll look for orders with goshippo_order_id
        # that might actually contain ShipStation IDs (typically different format)
        orders_to_check = Order.objects.filter(
            goshippo_order_id__isnull=False
        ).exclude(goshippo_order_id='')
        
        total_orders = orders_to_check.count()
        self.stdout.write(f"Found {total_orders} orders with shipping IDs to check")
        
        if total_orders == 0:
            self.stdout.write(self.style.WARNING("No orders found that need migration"))
            return
        
        migrated_count = 0
        batch_count = 0
        
        # Process orders in batches
        for i in range(0, total_orders, batch_size):
            batch_orders = orders_to_check[i:i+batch_size]
            batch_count += 1
            
            self.stdout.write(f"Processing batch {batch_count}...")
            
            with transaction.atomic():
                for order in batch_orders:
                    if self.should_migrate_order(order):
                        if not dry_run:
                            self.migrate_order(order)
                        migrated_count += 1
                        
                        self.stdout.write(
                            f"{'Would migrate' if dry_run else 'Migrated'} order {order.order_number}"
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would migrate' if dry_run else 'Migrated'} {migrated_count} orders"
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "This was a dry run. Use --no-dry-run to apply changes."
                )
            )
    
    def should_migrate_order(self, order):
        """
        Determine if an order needs migration from ShipStation to Goshippo format.
        
        This is a placeholder function since the actual determination would depend
        on the specific format of your ShipStation IDs vs Goshippo IDs.
        """
        # Example logic: ShipStation IDs might be numeric, Goshippo IDs are alphanumeric
        if order.goshippo_order_id:
            # If it's all numeric, it might be a ShipStation ID
            if order.goshippo_order_id.isdigit():
                return True
            # Add other checks based on your data format
        return False
    
    def migrate_order(self, order):
        """
        Migrate a single order's data from ShipStation to Goshippo format.
        """
        try:
            # Store the old ShipStation ID in notes or a custom field
            old_id = order.goshippo_order_id
            
            # Clear the goshippo_order_id since it contained ShipStation data
            order.goshippo_order_id = ''
            
            # Add a note about the migration
            migration_note = f"Migrated from ShipStation (ID: {old_id})"
            if order.notes:
                order.notes += f"\n{migration_note}"
            else:
                order.notes = migration_note
            
            order.save()
            
            logger.info(f"Migrated order {order.order_number} from ShipStation")
            
        except Exception as e:
            logger.error(f"Error migrating order {order.order_number}: {str(e)}")
            raise