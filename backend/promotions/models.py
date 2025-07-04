from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from products.models import Product, Category
import string
import random

User = get_user_model()


class PromotionCode(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    USAGE_TYPES = [
        ('single', 'Single Use'),
        ('limited', 'Limited Uses'),
        ('unlimited', 'Unlimited Uses'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Usage limits
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES, default='unlimited')
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of times this code can be used"
    )
    usage_limit_per_user = models.PositiveIntegerField(
        default=1,
        help_text="Number of times a single user can use this code"
    )
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Conditions
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum order amount required to use this code"
    )
    
    # Applicable to specific products or categories
    applicable_to_all = models.BooleanField(default=True)
    applicable_products = models.ManyToManyField(Product, blank=True)
    applicable_categories = models.ManyToManyField(Category, blank=True)
    
    # Restrictions
    first_order_only = models.BooleanField(
        default=False,
        help_text="Code can only be used on user's first order"
    )
    logged_in_only = models.BooleanField(
        default=False,
        help_text="Code can only be used by logged-in users"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.description}"
    
    @staticmethod
    def generate_code(length=8):
        """Generate a random promotional code."""
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(characters) for _ in range(length))
            if not PromotionCode.objects.filter(code=code).exists():
                return code
    
    def is_valid(self):
        """Check if the promotion code is currently valid."""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until
        )
    
    def can_be_used_by(self, user, order_amount=0):
        """Check if the code can be used by a specific user."""
        if not self.is_valid():
            return False, "Promotion code is not valid"
        
        # Check minimum order amount
        if order_amount < self.minimum_order_amount:
            return False, f"Minimum order amount of ${self.minimum_order_amount} required"
        
        # Check if logged in only
        if self.logged_in_only and not user.is_authenticated:
            return False, "This code requires you to be logged in"
        
        # Check usage limits
        if self.usage_type == 'single':
            if self.uses.exists():
                return False, "This code has already been used"
        elif self.usage_type == 'limited':
            if self.uses.count() >= self.usage_limit:
                return False, "This code has reached its usage limit"
        
        # Check per-user usage limit
        if user.is_authenticated:
            user_uses = self.uses.filter(user=user).count()
            if user_uses >= self.usage_limit_per_user:
                return False, "You have already used this code the maximum number of times"
        
        # Check first order only
        if self.first_order_only and user.is_authenticated:
            from orders.models import Order
            if Order.objects.filter(user=user).exists():
                return False, "This code is only valid for first-time orders"
        
        return True, "Valid"
    
    def calculate_discount(self, subtotal, applicable_items_total=None):
        """Calculate the discount amount for a given subtotal."""
        if self.discount_type == 'percentage':
            # If specific products/categories, apply percentage only to those items
            base_amount = applicable_items_total if applicable_items_total else subtotal
            return min(base_amount * (self.discount_value / 100), base_amount)
        elif self.discount_type == 'fixed':
            return min(self.discount_value, subtotal)
        elif self.discount_type == 'free_shipping':
            return 0  # Shipping cost will be set to 0
        return 0


class PromotionCodeUsage(models.Model):
    """Track usage of promotion codes."""
    promotion_code = models.ForeignKey(PromotionCode, on_delete=models.CASCADE, related_name='uses')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']
        unique_together = ['promotion_code', 'order']
    
    def __str__(self):
        user_str = self.user.email if self.user else "Guest"
        return f"{self.promotion_code.code} used by {user_str}"


class Campaign(models.Model):
    """Marketing campaigns that can contain multiple promotion codes."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    promotion_codes = models.ManyToManyField(PromotionCode, blank=True, related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def is_running(self):
        """Check if the campaign is currently running."""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
