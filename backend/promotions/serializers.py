from rest_framework import serializers
from .models import PromotionCode, PromotionCodeUsage, Campaign
from products.serializers import ProductListSerializer, CategorySerializer


class PromotionCodeSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)
    applicable_products = ProductListSerializer(many=True, read_only=True)
    applicable_categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = PromotionCode
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'usage_type', 'usage_limit', 'usage_limit_per_user',
            'valid_from', 'valid_until', 'is_active', 'is_valid',
            'minimum_order_amount', 'applicable_to_all',
            'applicable_products', 'applicable_categories',
            'first_order_only', 'logged_in_only',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_valid']


class PromotionCodeValidationSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)


class PromotionCodeUsageSerializer(serializers.ModelSerializer):
    promotion_code = serializers.StringRelatedField()
    user = serializers.StringRelatedField()
    
    class Meta:
        model = PromotionCodeUsage
        fields = ['id', 'promotion_code', 'user', 'order', 'discount_amount', 'used_at']
        read_only_fields = ['id', 'used_at']


class CampaignSerializer(serializers.ModelSerializer):
    promotion_codes = PromotionCodeSerializer(many=True, read_only=True)
    is_running = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'start_date', 'end_date',
            'is_active', 'is_running', 'promotion_codes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_running']