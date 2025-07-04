from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from decimal import Decimal

User = get_user_model()


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    FULFILLMENT_CHOICES = [
        ('shipping', 'Shipping'),
        ('pickup', 'Local Pickup'),
    ]

    CARRIER_CHOICES = [
        ('usps', 'USPS'),
        ('ups', 'UPS'),
        ('fedex', 'FedEx'),
        ('dhl', 'DHL'),
        ('ontrac', 'OnTrac'),
        ('lasership', 'LaserShip'),
        ('canadapost', 'Canada Post'),
        ('dpd', 'DPD'),
        ('gls', 'GLS'),
        ('purolator', 'Purolator'),
        ('asendia', 'Asendia'),
        ('other', 'Other'),
    ]

    SERVICE_LEVEL_CHOICES = [
        # USPS
        ('usps_priority', 'USPS Priority Mail'),
        ('usps_priority_express', 'USPS Priority Mail Express'),
        ('usps_ground_advantage', 'USPS Ground Advantage'),
        ('usps_first_class', 'USPS First Class'),
        ('usps_media_mail', 'USPS Media Mail'),
        
        # UPS
        ('ups_ground', 'UPS Ground'),
        ('ups_next_day_air', 'UPS Next Day Air'),
        ('ups_next_day_air_saver', 'UPS Next Day Air Saver'),
        ('ups_2nd_day_air', 'UPS 2nd Day Air'),
        ('ups_3_day_select', 'UPS 3 Day Select'),
        
        # FedEx
        ('fedex_ground', 'FedEx Ground'),
        ('fedex_express_saver', 'FedEx Express Saver'),
        ('fedex_2_day', 'FedEx 2Day'),
        ('fedex_standard_overnight', 'FedEx Standard Overnight'),
        ('fedex_priority_overnight', 'FedEx Priority Overnight'),
        
        # DHL
        ('dhl_express', 'DHL Express'),
        ('dhl_express_worldwide', 'DHL Express Worldwide'),
        ('dhl_economy_select', 'DHL Economy Select'),
        
        # Generic
        ('standard', 'Standard'),
        ('express', 'Express'),
        ('overnight', 'Overnight'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, help_text='For guest checkout tracking')
    order_number = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    fulfillment_method = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default='shipping')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Promotion code used
    promotion_code = models.ForeignKey(
        'promotions.PromotionCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Shipping Information
    shipping_name = models.CharField(max_length=100)
    shipping_email = models.EmailField()
    shipping_phone = models.CharField(max_length=20, blank=True)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)
    
    # Billing Information
    billing_name = models.CharField(max_length=100)
    billing_email = models.EmailField()
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    goshippo_order_id = models.CharField(max_length=50, blank=True, help_text='Goshippo order ID')
    goshippo_transaction_id = models.CharField(max_length=50, blank=True, help_text='Goshippo transaction ID')
    goshippo_object_id = models.CharField(max_length=50, blank=True, help_text='Goshippo shipment object ID')
    goshippo_tracking_url = models.URLField(blank=True, help_text='Goshippo tracking URL')
    goshippo_label_url = models.URLField(blank=True, help_text='Goshippo shipping label URL')
    goshippo_rate_id = models.CharField(max_length=50, blank=True, help_text='Goshippo rate ID used for shipping')
    carrier = models.CharField(max_length=50, choices=CARRIER_CHOICES, blank=True, help_text='Shipping carrier')
    service_level = models.CharField(max_length=100, choices=SERVICE_LEVEL_CHOICES, blank=True, help_text='Service level')
    estimated_delivery = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        email = self.user.email if self.user else self.billing_email or 'Guest'
        return f"Order {self.order_number} - {email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = str(uuid.uuid4()).replace('-', '').upper()[:12]
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_weight(self):
        return sum(item.total_weight for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Product snapshot at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    product_weight = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def total_weight(self):
        return self.product_weight * self.quantity

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name
            self.product_sku = self.product.sku
            self.product_weight = self.product.weight
        
        if not self.unit_price:
            self.unit_price = self.product.price
        
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Order Status Histories"

    def __str__(self):
        return f"Order {self.order.order_number} - {self.status}"


class TrackingStatus(models.Model):
    """Model to store detailed tracking status history from Goshippo."""
    
    TRACKING_STATUS_CHOICES = [
        ('UNKNOWN', 'Unknown'),
        ('PRE_TRANSIT', 'Pre Transit'),
        ('TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('RETURNED', 'Returned'),
        ('FAILURE', 'Failure'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_statuses')
    goshippo_tracking_id = models.CharField(max_length=50, blank=True, help_text='Goshippo tracking object ID')
    tracking_number = models.CharField(max_length=100, help_text='Package tracking number')
    carrier = models.CharField(max_length=50, choices=Order.CARRIER_CHOICES, help_text='Shipping carrier')
    
    # Status information
    status = models.CharField(max_length=20, choices=TRACKING_STATUS_CHOICES, default='UNKNOWN')
    status_details = models.TextField(blank=True, help_text='Detailed status message')
    status_date = models.DateTimeField(null=True, blank=True, help_text='When the status occurred')
    
    # Location information
    location_city = models.CharField(max_length=100, blank=True)
    location_state = models.CharField(max_length=100, blank=True)
    location_zip = models.CharField(max_length=20, blank=True)
    location_country = models.CharField(max_length=100, blank=True)
    
    # Goshippo object data
    goshippo_object_created = models.DateTimeField(null=True, blank=True)
    goshippo_object_updated = models.DateTimeField(null=True, blank=True)
    
    # Local timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-status_date', '-created_at']
        verbose_name = 'Tracking Status'
        verbose_name_plural = 'Tracking Statuses'
    
    def __str__(self):
        return f"Tracking {self.tracking_number} - {self.status}"