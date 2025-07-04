from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer, WishlistItemSerializer
from products.models import Product
import logging

logger = logging.getLogger(__name__)


def get_or_create_wishlist(request):
    """Get or create wishlist for authenticated user or guest."""
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        wishlist, created = Wishlist.objects.get_or_create(session_key=session_key)
    return wishlist


@api_view(['GET'])
@permission_classes([AllowAny])
def get_wishlist(request):
    """Get current wishlist."""
    try:
        wishlist = get_or_create_wishlist(request)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error getting wishlist: {str(e)}")
        return Response(
            {'error': 'Failed to retrieve wishlist'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_wishlist(request):
    """Add product to wishlist."""
    try:
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'Product ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id)
        wishlist = get_or_create_wishlist(request)

        # Check if item already exists
        if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
            return Response(
                {'message': 'Product already in wishlist'},
                status=status.HTTP_200_OK
            )

        # Add item to wishlist
        wishlist_item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=product
        )

        serializer = WishlistItemSerializer(wishlist_item)
        return Response(
            {
                'message': 'Product added to wishlist',
                'item': serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error adding to wishlist: {str(e)}")
        return Response(
            {'error': 'Failed to add product to wishlist'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist."""
    try:
        wishlist = get_or_create_wishlist(request)
        wishlist_item = get_object_or_404(
            WishlistItem,
            wishlist=wishlist,
            product_id=product_id
        )
        wishlist_item.delete()

        return Response(
            {'message': 'Product removed from wishlist'},
            status=status.HTTP_200_OK
        )

    except WishlistItem.DoesNotExist:
        return Response(
            {'error': 'Product not in wishlist'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error removing from wishlist: {str(e)}")
        return Response(
            {'error': 'Failed to remove product from wishlist'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def clear_wishlist(request):
    """Clear all items from wishlist."""
    try:
        wishlist = get_or_create_wishlist(request)
        wishlist.items.all().delete()

        return Response(
            {'message': 'Wishlist cleared'},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Error clearing wishlist: {str(e)}")
        return Response(
            {'error': 'Failed to clear wishlist'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def move_to_cart(request, product_id):
    """Move product from wishlist to cart."""
    try:
        from cart.views import add_to_cart as cart_add
        
        # First add to cart
        cart_response = cart_add(request._request if hasattr(request, '_request') else request)
        
        if cart_response.status_code == 201:
            # Remove from wishlist if added to cart successfully
            wishlist = get_or_create_wishlist(request)
            wishlist_item = WishlistItem.objects.filter(
                wishlist=wishlist,
                product_id=product_id
            ).first()
            
            if wishlist_item:
                wishlist_item.delete()
            
            return Response(
                {'message': 'Product moved to cart'},
                status=status.HTTP_200_OK
            )
        else:
            return cart_response

    except Exception as e:
        logger.error(f"Error moving to cart: {str(e)}")
        return Response(
            {'error': 'Failed to move product to cart'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
