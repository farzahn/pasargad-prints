from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer


def get_or_create_cart(request):
    """Get or create cart for authenticated user or guest session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


class CartRetrieveView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return get_or_create_cart(self.request)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def add_to_cart(request):
    cart = get_or_create_cart(request)
    serializer = AddToCartSerializer(data=request.data)
    
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        product = get_object_or_404(Product, id=product_id)
        
        # Validate stock availability before adding to cart
        if not product.is_in_stock or product.stock_quantity == 0:
            return Response({
                'error': 'This product is currently out of stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity > product.stock_quantity:
            return Response({
                'error': f'Only {product.stock_quantity} items available in stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update existing item quantity
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock_quantity:
                return Response({
                    'error': f'Cannot add {quantity} more items. Only {product.stock_quantity - cart_item.quantity} available.'
                }, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
            cart_item.save()
        
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([permissions.AllowAny])
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    serializer = UpdateCartItemSerializer(data=request.data)
    if serializer.is_valid():
        quantity = serializer.validated_data['quantity']
        
        if quantity == 0:
            cart_item.delete()
        else:
            # Check stock availability
            if quantity > cart_item.product.stock_quantity:
                return Response({
                    'error': f'Only {cart_item.product.stock_quantity} items available in stock'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = quantity
            cart_item.save()
        
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    
    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])
def clear_cart(request):
    cart = get_or_create_cart(request)
    # Delete all items - this is idempotent (safe to call multiple times)
    cart.items.all().delete()
    
    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def merge_guest_cart(request):
    """Merge guest cart with user cart when user logs in"""
    session_key = request.data.get('session_key')
    if not session_key:
        return Response({'error': 'Session key required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        guest_cart = Cart.objects.get(session_key=session_key)
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Merge items from guest cart to user cart
        for guest_item in guest_cart.items.all():
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=guest_item.product,
                defaults={'quantity': guest_item.quantity}
            )
            
            if not created:
                # Add quantities together, respecting stock limits
                new_quantity = user_item.quantity + guest_item.quantity
                if new_quantity <= guest_item.product.stock_quantity:
                    user_item.quantity = new_quantity
                    user_item.save()
        
        # Delete guest cart
        guest_cart.delete()
        
        cart_serializer = CartSerializer(user_cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)
        
    except Cart.DoesNotExist:
        # No guest cart found, just return user's cart
        user_cart = get_or_create_cart(request)
        cart_serializer = CartSerializer(user_cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)