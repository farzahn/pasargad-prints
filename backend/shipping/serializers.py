from rest_framework import serializers
from .models import ShippingRate, ShippingLabel, TrackingEvent


class ShippingRateSerializer(serializers.ModelSerializer):
    """Serializer for shipping rates."""
    
    class Meta:
        model = ShippingRate
        fields = [
            'id',
            'goshippo_rate_id',
            'carrier',
            'service_level',
            'amount',
            'currency',
            'estimated_days',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShippingLabelSerializer(serializers.ModelSerializer):
    """Serializer for shipping labels."""
    
    class Meta:
        model = ShippingLabel
        fields = [
            'id',
            'goshippo_transaction_id',
            'goshippo_shipment_id',
            'goshippo_rate_id',
            'label_url',
            'tracking_number',
            'carrier',
            'service_level',
            'amount',
            'currency',
            'status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TrackingEventSerializer(serializers.ModelSerializer):
    """Serializer for tracking events."""
    
    class Meta:
        model = TrackingEvent
        fields = [
            'id',
            'tracking_number',
            'status',
            'status_details',
            'status_date',
            'location',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ShippingRateRequestSerializer(serializers.Serializer):
    """Serializer for shipping rate requests."""
    
    order_id = serializers.IntegerField()
    
    def validate_order_id(self, value):
        """Validate that the order exists."""
        from orders.models import Order
        try:
            Order.objects.get(id=value)
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")


class PurchaseLabelSerializer(serializers.Serializer):
    """Serializer for purchasing shipping labels."""
    
    rate_id = serializers.CharField(max_length=100)
    label_file_type = serializers.CharField(max_length=10, default='PDF')
    
    def validate_rate_id(self, value):
        """Validate that the rate exists."""
        try:
            ShippingRate.objects.get(goshippo_rate_id=value)
            return value
        except ShippingRate.DoesNotExist:
            raise serializers.ValidationError("Shipping rate not found")
    
    def validate_label_file_type(self, value):
        """Validate label file type."""
        allowed_types = ['PDF', 'PNG', 'ZPLII']
        if value.upper() not in allowed_types:
            raise serializers.ValidationError(f"Label file type must be one of: {allowed_types}")
        return value.upper()


class TrackingRequestSerializer(serializers.Serializer):
    """Serializer for tracking requests."""
    
    carrier = serializers.CharField(max_length=50)
    tracking_number = serializers.CharField(max_length=100)
    
    def validate_carrier(self, value):
        """Validate carrier name."""
        allowed_carriers = ['usps', 'ups', 'fedex', 'dhl', 'ontrac', 'lasership']
        if value.lower() not in allowed_carriers:
            raise serializers.ValidationError(f"Carrier must be one of: {allowed_carriers}")
        return value.lower()