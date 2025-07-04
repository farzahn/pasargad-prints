from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from promotions.models import PromotionCode, Campaign
from products.models import Category


class Command(BaseCommand):
    help = 'Creates sample promotion codes for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample promotion codes...')
        
        # Create welcome promotion
        welcome_promo, created = PromotionCode.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'description': '10% off for new customers',
                'discount_type': 'percentage',
                'discount_value': 10,
                'usage_type': 'unlimited',
                'usage_limit_per_user': 1,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=365),
                'minimum_order_amount': 25,
                'first_order_only': True,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created promotion: {welcome_promo.code}'))
        
        # Create free shipping promotion
        shipping_promo, created = PromotionCode.objects.get_or_create(
            code='FREESHIP',
            defaults={
                'description': 'Free shipping on orders over $50',
                'discount_type': 'free_shipping',
                'discount_value': 0,
                'usage_type': 'unlimited',
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=90),
                'minimum_order_amount': 50,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created promotion: {shipping_promo.code}'))
        
        # Create fixed discount promotion
        fixed_promo, created = PromotionCode.objects.get_or_create(
            code='SAVE5',
            defaults={
                'description': '$5 off your order',
                'discount_type': 'fixed',
                'discount_value': 5,
                'usage_type': 'limited',
                'usage_limit': 100,
                'usage_limit_per_user': 2,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=30),
                'minimum_order_amount': 30,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created promotion: {fixed_promo.code}'))
        
        # Create category-specific promotion
        category = Category.objects.first()
        if category:
            category_promo, created = PromotionCode.objects.get_or_create(
                code='CAT20OFF',
                defaults={
                    'description': f'20% off {category.name} products',
                    'discount_type': 'percentage',
                    'discount_value': 20,
                    'usage_type': 'unlimited',
                    'valid_from': timezone.now(),
                    'valid_until': timezone.now() + timedelta(days=14),
                    'applicable_to_all': False,
                    'is_active': True
                }
            )
            if created:
                category_promo.applicable_categories.add(category)
                self.stdout.write(self.style.SUCCESS(f'Created promotion: {category_promo.code}'))
        
        # Create VIP promotion (logged in users only)
        vip_promo, created = PromotionCode.objects.get_or_create(
            code='VIP15',
            defaults={
                'description': '15% off for registered users',
                'discount_type': 'percentage',
                'discount_value': 15,
                'usage_type': 'unlimited',
                'usage_limit_per_user': 3,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=60),
                'minimum_order_amount': 40,
                'logged_in_only': True,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created promotion: {vip_promo.code}'))
        
        # Create a campaign
        campaign, created = Campaign.objects.get_or_create(
            name='Summer Sale 2024',
            defaults={
                'description': 'Special summer promotions for our customers',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=90),
                'is_active': True
            }
        )
        if created:
            campaign.promotion_codes.add(shipping_promo, fixed_promo, vip_promo)
            self.stdout.write(self.style.SUCCESS(f'Created campaign: {campaign.name}'))
        
        self.stdout.write(self.style.SUCCESS('Sample promotions created successfully!'))