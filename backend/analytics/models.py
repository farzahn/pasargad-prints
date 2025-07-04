from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from products.models import Product
from orders.models import Order

User = get_user_model()


class PageView(models.Model):
    """Track page views for analytics"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255)
    page_url = models.URLField(max_length=500)
    page_title = models.CharField(max_length=255, blank=True)
    referrer = models.URLField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'analytics_page_views'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['page_url']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.page_url} - {self.timestamp}"


class UserBehavior(models.Model):
    """Track specific user behaviors and interactions"""
    EVENT_TYPES = [
        ('click', 'Click'),
        ('scroll', 'Scroll'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('checkout_start', 'Checkout Start'),
        ('checkout_complete', 'Checkout Complete'),
        ('form_submit', 'Form Submit'),
        ('error', 'Error'),
        ('custom', 'Custom'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_name = models.CharField(max_length=255)
    event_data = models.JSONField(default=dict, blank=True)
    page_url = models.URLField(max_length=500)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'analytics_user_behavior'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['event_type']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type}: {self.event_name} - {self.timestamp}"


class ProductView(models.Model):
    """Track product views for analytics and recommendations"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_product_views')
    session_id = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    view_duration = models.IntegerField(null=True, blank=True, help_text="View duration in seconds")
    source = models.CharField(max_length=100, blank=True, help_text="Source of the view (search, category, recommendation, etc.)")
    
    class Meta:
        db_table = 'analytics_product_views'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['product']),
            models.Index(fields=['session_id']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product.name} viewed by {self.user or 'Anonymous'} at {self.timestamp}"


class CartAbandonment(models.Model):
    """Track cart abandonment for recovery campaigns"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255)
    cart_data = models.JSONField(default=dict)
    cart_value = models.DecimalField(max_digits=10, decimal_places=2)
    abandoned_at = models.DateTimeField(default=timezone.now)
    recovered = models.BooleanField(default=False)
    recovered_at = models.DateTimeField(null=True, blank=True)
    recovery_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_cart_abandonment'
        indexes = [
            models.Index(fields=['abandoned_at']),
            models.Index(fields=['user']),
            models.Index(fields=['recovered']),
        ]
        ordering = ['-abandoned_at']

    def __str__(self):
        return f"Cart abandoned by {self.user or 'Anonymous'} - ${self.cart_value}"


class Conversion(models.Model):
    """Track conversion events and attribution"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    source = models.CharField(max_length=100, blank=True)
    medium = models.CharField(max_length=100, blank=True)
    campaign = models.CharField(max_length=100, blank=True)
    referrer = models.URLField(max_length=500, blank=True, null=True)
    landing_page = models.URLField(max_length=500, blank=True)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    attribution_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'analytics_conversions'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['source', 'medium', 'campaign']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"Conversion: {self.order.order_number} - ${self.conversion_value}"


class ABTestExperiment(models.Model):
    """Define A/B test experiments"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    feature = models.CharField(max_length=100)
    variants = models.JSONField(default=list, help_text="List of variant configurations")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    traffic_percentage = models.IntegerField(default=100, help_text="Percentage of traffic to include in test")
    success_metric = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_ab_experiments'
        ordering = ['-created_at']

    def __str__(self):
        return f"A/B Test: {self.name}"


class ABTestParticipant(models.Model):
    """Track A/B test participants and their variants"""
    experiment = models.ForeignKey(ABTestExperiment, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255)
    variant = models.CharField(max_length=50)
    enrolled_at = models.DateTimeField(default=timezone.now)
    converted = models.BooleanField(default=False)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conversion_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'analytics_ab_participants'
        unique_together = ['experiment', 'user', 'session_id']
        indexes = [
            models.Index(fields=['experiment', 'variant']),
            models.Index(fields=['enrolled_at']),
        ]

    def __str__(self):
        return f"{self.experiment.name} - {self.variant} - {self.user or self.session_id}"


class Report(models.Model):
    """Store generated reports for caching and history"""
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('customer', 'Customer Report'),
        ('product', 'Product Performance'),
        ('marketing', 'Marketing Report'),
        ('financial', 'Financial Report'),
        ('custom', 'Custom Report'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    name = models.CharField(max_length=255)
    parameters = models.JSONField(default=dict)
    data = models.JSONField(default=dict)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(default=timezone.now)
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_reports'
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.name} - {self.generated_at}"
