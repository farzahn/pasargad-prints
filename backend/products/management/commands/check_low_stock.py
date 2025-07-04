from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import F
from products.models import Product
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for low stock products and send alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send alerts to (default: admin emails)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get low stock products
        low_stock_products = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0,
            stock_quantity__lte=F('low_stock_threshold')
        ).order_by('stock_quantity')
        
        out_of_stock_products = Product.objects.filter(
            is_active=True,
            stock_quantity=0
        ).order_by('name')
        
        if not low_stock_products.exists() and not out_of_stock_products.exists():
            self.stdout.write(self.style.SUCCESS('No stock alerts needed.'))
            return
        
        # Prepare alert data
        alert_data = {
            'low_stock_products': [],
            'out_of_stock_products': []
        }
        
        for product in low_stock_products:
            alert_data['low_stock_products'].append({
                'name': product.name,
                'sku': product.sku,
                'current_stock': product.stock_quantity,
                'threshold': product.low_stock_threshold
            })
        
        for product in out_of_stock_products:
            alert_data['out_of_stock_products'].append({
                'name': product.name,
                'sku': product.sku
            })
        
        # Log the alerts
        self.stdout.write(self.style.WARNING(f'Found {low_stock_products.count()} low stock products'))
        self.stdout.write(self.style.WARNING(f'Found {out_of_stock_products.count()} out of stock products'))
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run - no emails sent'))
            self.stdout.write('Low Stock Products:')
            for item in alert_data['low_stock_products']:
                self.stdout.write(f"  - {item['name']} (SKU: {item['sku']}): {item['current_stock']} units")
            
            self.stdout.write('\nOut of Stock Products:')
            for item in alert_data['out_of_stock_products']:
                self.stdout.write(f"  - {item['name']} (SKU: {item['sku']})")
            return
        
        # Determine recipients
        if options['email']:
            recipients = [options['email']]
        else:
            # Get all admin users
            recipients = list(User.objects.filter(
                is_staff=True, is_active=True
            ).values_list('email', flat=True))
        
        if not recipients:
            self.stdout.write(self.style.ERROR('No recipients found for stock alerts'))
            return
        
        # Send email alert
        try:
            subject = 'Pasargad Prints - Stock Alert'
            
            # Create email content
            html_message = self._create_html_message(alert_data)
            plain_message = self._create_plain_message(alert_data)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=False
            )
            
            self.stdout.write(self.style.SUCCESS(f'Stock alerts sent to {len(recipients)} recipients'))
            
        except Exception as e:
            logger.error(f'Failed to send stock alert emails: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Failed to send emails: {str(e)}'))
    
    def _create_html_message(self, alert_data):
        """Create HTML email message."""
        html = '''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #e74c3c;">Stock Alert - Pasargad Prints</h2>
            
            <h3 style="color: #f39c12;">Low Stock Products</h3>
            <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Product</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">SKU</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Current Stock</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Threshold</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for item in alert_data['low_stock_products']:
            html += f'''
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px;">{item['name']}</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px;">{item['sku']}</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #f39c12; font-weight: bold;">{item['current_stock']}</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{item['threshold']}</td>
                    </tr>
            '''
        
        if not alert_data['low_stock_products']:
            html += '''
                    <tr>
                        <td colspan="4" style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #6c757d;">No low stock products</td>
                    </tr>
            '''
        
        html += '''
                </tbody>
            </table>
            
            <h3 style="color: #e74c3c;">Out of Stock Products</h3>
            <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Product</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">SKU</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for item in alert_data['out_of_stock_products']:
            html += f'''
                    <tr>
                        <td style="border: 1px solid #dee2e6; padding: 8px;">{item['name']}</td>
                        <td style="border: 1px solid #dee2e6; padding: 8px;">{item['sku']}</td>
                    </tr>
            '''
        
        if not alert_data['out_of_stock_products']:
            html += '''
                    <tr>
                        <td colspan="2" style="border: 1px solid #dee2e6; padding: 8px; text-align: center; color: #6c757d;">No out of stock products</td>
                    </tr>
            '''
        
        html += '''
                </tbody>
            </table>
            
            <p style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #007bff;">
                Please log in to the admin panel to update stock levels.
            </p>
        </body>
        </html>
        '''
        
        return html
    
    def _create_plain_message(self, alert_data):
        """Create plain text email message."""
        message = 'STOCK ALERT - Pasargad Prints\n\n'
        
        message += 'LOW STOCK PRODUCTS:\n'
        message += '-' * 50 + '\n'
        for item in alert_data['low_stock_products']:
            message += f"- {item['name']} (SKU: {item['sku']}): {item['current_stock']} units (threshold: {item['threshold']})\n"
        
        if not alert_data['low_stock_products']:
            message += 'No low stock products\n'
        
        message += '\n\nOUT OF STOCK PRODUCTS:\n'
        message += '-' * 50 + '\n'
        for item in alert_data['out_of_stock_products']:
            message += f"- {item['name']} (SKU: {item['sku']})\n"
        
        if not alert_data['out_of_stock_products']:
            message += 'No out of stock products\n'
        
        message += '\n\nPlease log in to the admin panel to update stock levels.'
        
        return message