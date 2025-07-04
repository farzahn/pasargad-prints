from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q, Count, Avg, F
from django.shortcuts import get_object_or_404
from products.models import Product, Category
from products.serializers import ProductListSerializer
from orders.models import OrderItem
from .models import ProductView, ProductRelationship, UserProductScore
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def track_product_view(request, product):
    """Track when a user views a product."""
    try:
        if request.user.is_authenticated:
            ProductView.objects.create(user=request.user, product=product)
            
            # Update user product score
            score, created = UserProductScore.objects.get_or_create(
                user=request.user,
                product=product
            )
            score.views_count += 1
            score.update_score()
        else:
            session_key = request.session.session_key
            if session_key:
                ProductView.objects.create(session_key=session_key, product=product)
    except Exception as e:
        logger.error(f"Error tracking product view: {str(e)}")


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_recommendations(request, product_id):
    """Get recommendations for a specific product."""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Track the view
        track_product_view(request, product)
        
        recommendations = []
        
        # 1. Get directly related products
        related_products = ProductRelationship.objects.filter(
            product=product
        ).select_related('related_product').order_by('-strength')[:6]
        
        for rel in related_products:
            recommendations.append({
                'product': rel.related_product,
                'reason': f"{rel.get_relationship_type_display()}",
                'score': rel.strength
            })
        
        # 2. Get products from the same category
        if len(recommendations) < 8:
            category_products = Product.objects.filter(
                category=product.category,
                is_active=True
            ).exclude(id=product.id).order_by('-created_at')[:4]
            
            for p in category_products:
                if p not in [r['product'] for r in recommendations]:
                    recommendations.append({
                        'product': p,
                        'reason': 'Same category',
                        'score': 0.5
                    })
        
        # 3. Get frequently bought together products
        if len(recommendations) < 8:
            # Find orders that contain this product
            order_items = OrderItem.objects.filter(
                product=product
            ).values_list('order_id', flat=True)
            
            # Find other products in those orders
            frequently_bought = Product.objects.filter(
                orderitem__order_id__in=order_items
            ).exclude(id=product.id).annotate(
                purchase_count=Count('orderitem')
            ).order_by('-purchase_count')[:4]
            
            for p in frequently_bought:
                if p not in [r['product'] for r in recommendations]:
                    recommendations.append({
                        'product': p,
                        'reason': 'Frequently bought together',
                        'score': 0.7
                    })
        
        # Sort by score and limit
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:8]
        
        # Serialize the products
        result = []
        for rec in recommendations:
            serializer = ProductListSerializer(rec['product'])
            data = serializer.data
            data['recommendation_reason'] = rec['reason']
            result.append(data)
        
        return Response(result)
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting product recommendations: {str(e)}")
        return Response(
            {'error': 'Failed to get recommendations'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_personalized_recommendations(request):
    """Get personalized recommendations for the current user."""
    try:
        recommendations = []
        
        if request.user.is_authenticated:
            # Get user's product scores
            user_scores = UserProductScore.objects.filter(
                user=request.user
            ).select_related('product').order_by('-score')[:20]
            
            if user_scores:
                # Get top scored products
                for score in user_scores[:8]:
                    if score.product.is_active:
                        recommendations.append(score.product)
            
            # If not enough recommendations, get from recent views
            if len(recommendations) < 8:
                recent_views = ProductView.objects.filter(
                    user=request.user
                ).select_related('product').order_by('-viewed_at')[:20]
                
                viewed_categories = set()
                for view in recent_views:
                    viewed_categories.add(view.product.category_id)
                
                # Get products from viewed categories
                if viewed_categories:
                    category_products = Product.objects.filter(
                        category_id__in=viewed_categories,
                        is_active=True
                    ).exclude(
                        id__in=[p.id for p in recommendations]
                    ).order_by('-created_at')[:8]
                    
                    recommendations.extend(category_products)
        
        else:
            # For anonymous users, use session-based recommendations
            session_key = request.session.session_key
            if session_key:
                recent_views = ProductView.objects.filter(
                    session_key=session_key
                ).select_related('product').order_by('-viewed_at')[:10]
                
                viewed_categories = set()
                for view in recent_views:
                    viewed_categories.add(view.product.category_id)
                
                if viewed_categories:
                    recommendations = Product.objects.filter(
                        category_id__in=viewed_categories,
                        is_active=True
                    ).order_by('-created_at')[:8]
        
        # If still not enough, get popular products
        if len(recommendations) < 8:
            # Get products with most views in last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            popular_products = Product.objects.filter(
                is_active=True,
                views__viewed_at__gte=thirty_days_ago
            ).annotate(
                view_count=Count('views')
            ).exclude(
                id__in=[p.id for p in recommendations]
            ).order_by('-view_count')[:8]
            
            recommendations.extend(popular_products)
        
        # Limit to 8 recommendations
        recommendations = list(recommendations)[:8]
        
        serializer = ProductListSerializer(recommendations, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting personalized recommendations: {str(e)}")
        return Response(
            {'error': 'Failed to get recommendations'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_trending_products(request):
    """Get trending products based on recent activity."""
    try:
        # Get products with most views in last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        trending_products = Product.objects.filter(
            is_active=True,
            views__viewed_at__gte=seven_days_ago
        ).annotate(
            recent_views=Count('views', filter=Q(views__viewed_at__gte=seven_days_ago)),
            recent_orders=Count('orderitem', filter=Q(orderitem__order__created_at__gte=seven_days_ago))
        ).annotate(
            trending_score=F('recent_views') + (F('recent_orders') * 5)
        ).order_by('-trending_score')[:12]
        
        serializer = ProductListSerializer(trending_products, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting trending products: {str(e)}")
        return Response(
            {'error': 'Failed to get trending products'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
