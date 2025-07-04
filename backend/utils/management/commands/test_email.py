from django.core.management.base import BaseCommand
from django.conf import settings
from utils.email import email_service


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--test-type',
            type=str,
            default='simple',
            choices=['simple', 'order', 'all'],
            help='Type of test email to send'
        )

    def handle(self, *args, **options):
        email = options['email']
        test_type = options['test_type']
        
        self.stdout.write(f"Testing email configuration...")
        self.stdout.write(f"Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Email host: {settings.EMAIL_HOST}")
        self.stdout.write(f"From email: {settings.DEFAULT_FROM_EMAIL}")
        
        if test_type in ['simple', 'all']:
            self.stdout.write(f"\nSending test email to {email}...")
            success = email_service.send_test_email(email)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"✓ Test email sent successfully to {email}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ Failed to send test email to {email}"))
        
        if test_type in ['order', 'all']:
            # Create a mock order for testing
            from orders.models import Order
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Create or get test user
            test_user, _ = User.objects.get_or_create(
                username='test_email_user',
                defaults={
                    'email': email,
                    'first_name': 'Test',
                    'last_name': 'User'
                }
            )
            
            # Create test order
            test_order = Order(
                user=test_user,
                order_number='TEST123456',
                status='processing',
                subtotal=99.99,
                shipping_cost=5.00,
                total_amount=104.99,
                shipping_name='Test User',
                shipping_email=email,
                shipping_address='123 Test Street',
                shipping_city='Test City',
                shipping_state='TS',
                shipping_postal_code='12345',
                shipping_country='US',
                billing_name='Test User',
                billing_email=email,
                billing_address='123 Test Street',
                billing_city='Test City',
                billing_state='TS',
                billing_postal_code='12345',
                billing_country='US'
            )
            
            self.stdout.write(f"\nSending order confirmation email...")
            success = email_service.send_order_confirmation(test_order)
            
            if success:
                self.stdout.write(self.style.SUCCESS("✓ Order confirmation email sent"))
            else:
                self.stdout.write(self.style.ERROR("✗ Failed to send order confirmation"))
            
            # Test guest order
            test_order.user = None
            self.stdout.write(f"\nSending guest order receipt...")
            success = email_service.send_guest_order_receipt(test_order)
            
            if success:
                self.stdout.write(self.style.SUCCESS("✓ Guest order receipt sent"))
            else:
                self.stdout.write(self.style.ERROR("✗ Failed to send guest order receipt"))
        
        # Check email queue
        from utils.email import EmailQueue
        pending_count = EmailQueue.objects.filter(status='pending').count()
        if pending_count > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠ {pending_count} emails in queue pending delivery"))