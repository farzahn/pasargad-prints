from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    PageView, UserBehavior, ProductView, CartAbandonment, 
    Conversion, ABTestExperiment, ABTestParticipant, Report
)
from products.serializers import ProductListSerializer
from orders.serializers import OrderSerializer

User = get_user_model()


class PageViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageView
        fields = [
            'id', 'user', 'session_id', 'page_url', 'page_title',
            'referrer', 'timestamp', 'ip_address', 'user_agent',
            'device_type', 'browser', 'os', 'country', 'city'
        ]
        read_only_fields = ['id', 'timestamp']


class UserBehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBehavior
        fields = [
            'id', 'user', 'session_id', 'event_type', 'event_name',
            'event_data', 'page_url', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ProductViewSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = ProductView
        fields = [
            'id', 'user', 'session_id', 'product', 'product_details',
            'timestamp', 'view_duration', 'source'
        ]
        read_only_fields = ['id', 'timestamp']


class CartAbandonmentSerializer(serializers.ModelSerializer):
    recovery_order_details = OrderSerializer(source='recovery_order', read_only=True)
    
    class Meta:
        model = CartAbandonment
        fields = [
            'id', 'user', 'session_id', 'cart_data', 'cart_value',
            'abandoned_at', 'recovered', 'recovered_at', 'recovery_order',
            'recovery_order_details', 'email_sent', 'email_sent_at'
        ]
        read_only_fields = ['id', 'abandoned_at']


class ConversionSerializer(serializers.ModelSerializer):
    order_details = OrderSerializer(source='order', read_only=True)
    
    class Meta:
        model = Conversion
        fields = [
            'id', 'user', 'session_id', 'order', 'order_details',
            'source', 'medium', 'campaign', 'referrer', 'landing_page',
            'conversion_value', 'timestamp', 'attribution_data'
        ]
        read_only_fields = ['id', 'timestamp']


class ABTestExperimentSerializer(serializers.ModelSerializer):
    participant_count = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ABTestExperiment
        fields = [
            'id', 'name', 'description', 'feature', 'variants',
            'start_date', 'end_date', 'is_active', 'traffic_percentage',
            'success_metric', 'created_at', 'updated_at',
            'participant_count', 'conversion_rate'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_conversion_rate(self, obj):
        participants = obj.participants.all()
        if not participants:
            return 0
        converted = participants.filter(converted=True).count()
        return (converted / participants.count()) * 100


class ABTestParticipantSerializer(serializers.ModelSerializer):
    experiment_name = serializers.CharField(source='experiment.name', read_only=True)
    
    class Meta:
        model = ABTestParticipant
        fields = [
            'id', 'experiment', 'experiment_name', 'user', 'session_id',
            'variant', 'enrolled_at', 'converted', 'conversion_value',
            'conversion_data'
        ]
        read_only_fields = ['id', 'enrolled_at']


class ReportSerializer(serializers.ModelSerializer):
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'name', 'parameters', 'data',
            'generated_by', 'generated_by_username', 'generated_at',
            'file_path'
        ]
        read_only_fields = ['id', 'generated_at']


# Admin-specific serializers with more details
class AdminPageViewSerializer(PageViewSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta(PageViewSerializer.Meta):
        fields = PageViewSerializer.Meta.fields + ['username']


class AdminUserBehaviorSerializer(UserBehaviorSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta(UserBehaviorSerializer.Meta):
        fields = UserBehaviorSerializer.Meta.fields + ['username']


class AdminProductViewSerializer(ProductViewSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta(ProductViewSerializer.Meta):
        fields = ProductViewSerializer.Meta.fields + ['username']


class AdminCartAbandonmentSerializer(CartAbandonmentSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta(CartAbandonmentSerializer.Meta):
        fields = CartAbandonmentSerializer.Meta.fields + ['username', 'user_email']


class AdminConversionSerializer(ConversionSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta(ConversionSerializer.Meta):
        fields = ConversionSerializer.Meta.fields + ['username']


# Analytics Dashboard Serializers
class DashboardMetricsSerializer(serializers.Serializer):
    """Serializer for dashboard metrics"""
    total_page_views = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    cart_abandonment_rate = serializers.FloatField()
    top_products = serializers.ListField()
    revenue_by_day = serializers.ListField()
    traffic_sources = serializers.DictField()


class ProductPerformanceSerializer(serializers.Serializer):
    """Serializer for product performance metrics"""
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    views = serializers.IntegerField()
    add_to_cart_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_view_duration = serializers.FloatField()


class CustomerAnalyticsSerializer(serializers.Serializer):
    """Serializer for customer analytics"""
    customer_id = serializers.IntegerField()
    customer_email = serializers.EmailField()
    total_orders = serializers.IntegerField()
    lifetime_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_order_date = serializers.DateTimeField()
    favorite_categories = serializers.ListField()