from django.db import models
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()


class ShippingRate(models.Model):
    """Model to store shipping rate quotes from Goshippo."""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipping_rates')
    goshippo_rate_id = models.CharField(max_length=100, unique=True)
    carrier = models.CharField(max_length=50)
    service_level = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    estimated_days = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['amount']
    
    def __str__(self):
        return f"{self.carrier} {self.service_level} - ${self.amount}"


class ShippingLabel(models.Model):
    """Model to store shipping labels from Goshippo."""
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipping_label')
    goshippo_transaction_id = models.CharField(max_length=100, unique=True)
    goshippo_shipment_id = models.CharField(max_length=100)
    goshippo_rate_id = models.CharField(max_length=100)
    
    # Label details
    label_url = models.URLField()
    tracking_number = models.CharField(max_length=100)
    carrier = models.CharField(max_length=50)
    service_level = models.CharField(max_length=100)
    
    # Pricing
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    status = models.CharField(max_length=20, default='QUEUED')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Label for Order {self.order.order_number} - {self.tracking_number}"


class TrackingEvent(models.Model):
    """Model to store tracking events from Goshippo webhooks."""
    
    STATUS_CHOICES = [
        ('UNKNOWN', 'Unknown'),
        ('PRE_TRANSIT', 'Pre Transit'),
        ('TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned'),
        ('FAILURE', 'Failure'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_events')
    tracking_number = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    status_details = models.TextField(blank=True)
    status_date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    
    # Raw webhook data
    webhook_data = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-status_date']
        unique_together = ['tracking_number', 'status_date']
    
    def __str__(self):
        return f"{self.tracking_number} - {self.status} at {self.status_date}"