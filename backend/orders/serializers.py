from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items with product details."""
    
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_sku',
            'product_weight',
            'product_image',
            'quantity',
            'unit_price',
            'total_price',
            'total_weight'
        ]
        read_only_fields = ['product_name', 'product_sku', 'product_weight', 'total_weight']
    
    def get_product_image(self, obj):
        """Get the primary product image URL."""
        if obj.product and obj.product.images.filter(is_primary=True).exists():
            primary_image = obj.product.images.filter(is_primary=True).first()
            request = self.context.get('request')
            if request and primary_image.image:
                return request.build_absolute_uri(primary_image.image.url)
        return None


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history tracking."""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id',
            'status',
            'notes',
            'created_at',
            'created_by',
            'created_by_name'
        ]
        read_only_fields = ['created_at', 'created_by_name']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for order list view with basic information."""
    
    total_items = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'fulfillment_method',
            'total_amount',
            'total_items',
            'tracking_number',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single order view with all information."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_weight = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fulfillment_display = serializers.CharField(source='get_fulfillment_method_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'fulfillment_method',
            'fulfillment_display',
            
            # Pricing
            'subtotal',
            'tax_amount',
            'shipping_cost',
            'total_amount',
            
            # Shipping Information
            'shipping_name',
            'shipping_email',
            'shipping_phone',
            'shipping_address',
            'shipping_city',
            'shipping_state',
            'shipping_postal_code',
            'shipping_country',
            
            # Billing Information
            'billing_name',
            'billing_email',
            'billing_address',
            'billing_city',
            'billing_state',
            'billing_postal_code',
            'billing_country',
            
            # Tracking
            'tracking_number',
            'shipstation_order_id',
            'estimated_delivery',
            
            # Computed fields
            'total_items',
            'total_weight',
            
            # Related data
            'items',
            'status_history',
            
            # Timestamps
            'created_at',
            'updated_at',
            'shipped_at',
            'delivered_at'
        ]
        read_only_fields = [
            'order_number',
            'subtotal',
            'tax_amount',
            'shipping_cost',
            'total_amount',
            'total_items',
            'total_weight',
            'created_at',
            'updated_at'
        ]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status (admin only)."""
    
    notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        """Validate status transitions."""
        if self.instance:
            current_status = self.instance.status
            
            # Define allowed status transitions
            allowed_transitions = {
                'pending': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered', 'cancelled'],
                'delivered': ['refunded'],
                'cancelled': ['pending'],  # Allow reactivation
                'refunded': []  # Terminal state
            }
            
            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from '{current_status}' to '{value}'"
                )
        
        return value
    
    def update(self, instance, validated_data):
        """Update order status and create history record."""
        notes = validated_data.pop('notes', '')
        new_status = validated_data.get('status')
        
        # Update the order
        instance = super().update(instance, validated_data)
        
        # Create status history entry
        if new_status:
            OrderStatusHistory.objects.create(
                order=instance,
                status=new_status,
                notes=notes,
                created_by=self.context['request'].user
            )
            
            # Update timestamp fields based on status
            if new_status == 'shipped' and not instance.shipped_at:
                from django.utils import timezone
                instance.shipped_at = timezone.now()
                instance.save()
            elif new_status == 'delivered' and not instance.delivered_at:
                from django.utils import timezone
                instance.delivered_at = timezone.now()
                instance.save()
        
        return instance


class OrderTrackingSerializer(serializers.ModelSerializer):
    """Public serializer for order tracking by tracking number."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_number',
            'status',
            'status_display',
            'tracking_number',
            'estimated_delivery',
            'created_at',
            'shipped_at',
            'delivered_at',
            'items'
        ]
    
    def get_items(self, obj):
        """Return simplified item information for tracking."""
        return [
            {
                'product_name': item.product_name,
                'quantity': item.quantity
            }
            for item in obj.items.all()
        ]