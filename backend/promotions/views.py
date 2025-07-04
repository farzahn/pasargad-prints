from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from .models import PromotionCode, PromotionCodeUsage, Campaign
from .serializers import (
    PromotionCodeSerializer, PromotionCodeValidationSerializer,
    PromotionCodeUsageSerializer, CampaignSerializer
)
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_promotion_code(request):
    """Validate a promotion code for the current user."""
    try:
        serializer = PromotionCodeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        order_amount = serializer.validated_data.get('order_amount', 0)
        
        # Try to get the promotion code
        try:
            promotion = PromotionCode.objects.get(code=code.upper())
        except PromotionCode.DoesNotExist:
            return Response(
                {'valid': False, 'message': 'Invalid promotion code'},
                status=status.HTTP_200_OK
            )
        
        # Check if it can be used by this user
        can_use, message = promotion.can_be_used_by(request.user, order_amount)
        
        if can_use:
            # Calculate discount
            discount_amount = promotion.calculate_discount(order_amount)
            
            return Response({
                'valid': True,
                'message': message,
                'promotion': PromotionCodeSerializer(promotion).data,
                'discount_amount': float(discount_amount),
                'discount_type': promotion.discount_type
            })
        else:
            return Response({
                'valid': False,
                'message': message
            })
            
    except Exception as e:
        logger.error(f"Error validating promotion code: {str(e)}")
        return Response(
            {'error': 'Failed to validate promotion code'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def apply_promotion_code(request):
    """Apply a promotion code to calculate discount."""
    try:
        code = request.data.get('code', '').upper()
        cart_items = request.data.get('cart_items', [])
        subtotal = request.data.get('subtotal', 0)
        
        if not code:
            return Response(
                {'error': 'Promotion code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the promotion code
        try:
            promotion = PromotionCode.objects.get(code=code)
        except PromotionCode.DoesNotExist:
            return Response(
                {'error': 'Invalid promotion code'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate
        can_use, message = promotion.can_be_used_by(request.user, subtotal)
        if not can_use:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate applicable items total if promotion is product/category specific
        applicable_items_total = subtotal
        if not promotion.applicable_to_all:
            applicable_items_total = 0
            
            for item in cart_items:
                product_id = item.get('product_id')
                price = item.get('price', 0)
                quantity = item.get('quantity', 1)
                
                # Check if product is applicable
                if promotion.applicable_products.filter(id=product_id).exists():
                    applicable_items_total += price * quantity
                # Check if product's category is applicable
                elif promotion.applicable_categories.filter(products__id=product_id).exists():
                    applicable_items_total += price * quantity
        
        # Calculate discount
        discount_amount = promotion.calculate_discount(subtotal, applicable_items_total)
        
        return Response({
            'success': True,
            'promotion': PromotionCodeSerializer(promotion).data,
            'discount_amount': float(discount_amount),
            'applicable_items_total': float(applicable_items_total),
            'final_total': float(subtotal - discount_amount)
        })
        
    except Exception as e:
        logger.error(f"Error applying promotion code: {str(e)}")
        return Response(
            {'error': 'Failed to apply promotion code'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PromotionCodeListView(generics.ListCreateAPIView):
    """List and create promotion codes (admin only)."""
    queryset = PromotionCode.objects.all()
    serializer_class = PromotionCodeSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        # Generate code if not provided
        if not serializer.validated_data.get('code'):
            serializer.validated_data['code'] = PromotionCode.generate_code()
        serializer.save(created_by=self.request.user)


class PromotionCodeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete promotion codes (admin only)."""
    queryset = PromotionCode.objects.all()
    serializer_class = PromotionCodeSerializer
    permission_classes = [IsAdminUser]


class ActivePromotionsView(generics.ListAPIView):
    """List currently active promotions (public)."""
    serializer_class = PromotionCodeSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        now = timezone.now()
        return PromotionCode.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now,
            logged_in_only=False  # Only show public promotions
        )


class CampaignListView(generics.ListCreateAPIView):
    """List and create campaigns (admin only)."""
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete campaigns (admin only)."""
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAdminUser]


@api_view(['GET'])
@permission_classes([IsAdminUser])
def promotion_analytics(request):
    """Get analytics for promotion code usage."""
    try:
        # Get date range from query params
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Base queryset
        usage_qs = PromotionCodeUsage.objects.all()
        
        if start_date:
            usage_qs = usage_qs.filter(used_at__gte=start_date)
        if end_date:
            usage_qs = usage_qs.filter(used_at__lte=end_date)
        
        # Get promotion statistics
        promotions = PromotionCode.objects.all()
        
        analytics = []
        for promotion in promotions:
            promo_usage = usage_qs.filter(promotion_code=promotion)
            
            analytics.append({
                'code': promotion.code,
                'description': promotion.description,
                'total_uses': promo_usage.count(),
                'total_discount': float(promo_usage.aggregate(
                    total=models.Sum('discount_amount')
                )['total'] or 0),
                'unique_users': promo_usage.values('user').distinct().count(),
                'conversion_rate': f"{(promo_usage.count() / promotion.uses.count() * 100) if promotion.uses.count() > 0 else 0:.2f}%"
            })
        
        # Sort by total uses
        analytics.sort(key=lambda x: x['total_uses'], reverse=True)
        
        return Response({
            'analytics': analytics,
            'total_promotions': len(analytics),
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting promotion analytics: {str(e)}")
        return Response(
            {'error': 'Failed to get analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
