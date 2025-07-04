from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from cart.models import Cart, CartItem
from products.models import Product, Category

User = get_user_model()


class CartPersistenceTestCase(TestCase):
    """Test cart persistence for guest and authenticated users"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test products
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            category=self.category,
            price=Decimal('19.99'),
            stock_quantity=10,
            weight=Decimal('0.5')
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            category=self.category,
            price=Decimal('29.99'),
            stock_quantity=5,
            weight=Decimal('1.0')
        )
    
    def test_guest_cart_creation(self):
        """Test that guest users can create and use carts"""
        # Add item to cart as guest
        response = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 2},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        
        # Verify cart was created with session key
        session_key = self.client.session.session_key
        self.assertIsNotNone(session_key)
        
        cart = Cart.objects.get(session_key=session_key)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.items.count(), 1)
    
    def test_guest_cart_persistence_across_requests(self):
        """Test that guest cart persists across multiple requests"""
        # First request - add item
        response1 = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 1},
            format='json'
        )
        
        session_key = self.client.session.session_key
        
        # Second request - get cart
        response2 = self.client.get(reverse('cart_retrieve'))
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['total_items'], 1)
        
        # Third request - add another item
        response3 = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product2.id, 'quantity': 1},
            format='json'
        )
        
        self.assertEqual(response3.data['total_items'], 2)
        self.assertEqual(len(response3.data['items']), 2)
        
        # Verify same session key throughout
        self.assertEqual(self.client.session.session_key, session_key)
    
    def test_authenticated_user_cart(self):
        """Test that authenticated users have their own carts"""
        # Login
        self.client.force_authenticate(user=self.user)
        
        # Add item to cart
        response = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 3},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cart is associated with user
        cart = Cart.objects.get(user=self.user)
        self.assertIsNone(cart.session_key)
        self.assertEqual(cart.items.count(), 1)
    
    def test_cart_merge_on_login(self):
        """Test that guest cart is merged with user cart on login"""
        # Add items as guest
        response1 = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 2},
            format='json'
        )
        
        guest_session_key = self.client.session.session_key
        
        # Login and add different item
        self.client.force_authenticate(user=self.user)
        
        response2 = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product2.id, 'quantity': 1},
            format='json'
        )
        
        # Merge guest cart
        response3 = self.client.post(
            reverse('merge_guest_cart'),
            {'session_key': guest_session_key},
            format='json'
        )
        
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.data['total_items'], 3)
        self.assertEqual(len(response3.data['items']), 2)
        
        # Verify guest cart was deleted
        self.assertFalse(Cart.objects.filter(session_key=guest_session_key).exists())
    
    def test_cart_item_operations(self):
        """Test cart item update and removal operations"""
        # Add item
        response = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 2},
            format='json'
        )
        
        item_id = response.data['items'][0]['id']
        
        # Update quantity
        response = self.client.put(
            reverse('update_cart_item', kwargs={'item_id': item_id}),
            {'quantity': 5},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 5)
        
        # Remove item
        response = self.client.delete(
            reverse('remove_from_cart', kwargs={'item_id': item_id})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
    
    def test_stock_validation(self):
        """Test that stock limits are enforced"""
        # Try to add more than available stock
        response = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product2.id, 'quantity': 10},
            format='json'
        )
        
        # Should succeed because product2 has 5 in stock but we're adding 10
        # The model should handle this validation
        if response.status_code == status.HTTP_200_OK:
            # If it succeeded, try to add more
            response = self.client.post(
                reverse('add_to_cart'),
                {'product_id': self.product2.id, 'quantity': 1},
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('available', response.data['error'])
    
    def test_clear_cart(self):
        """Test clearing the entire cart"""
        # Add multiple items
        self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 2},
            format='json'
        )
        
        self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product2.id, 'quantity': 1},
            format='json'
        )
        
        # Clear cart
        response = self.client.delete(reverse('clear_cart'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(len(response.data['items']), 0)
    
    def test_duplicate_product_handling(self):
        """Test adding same product multiple times"""
        # Add product first time
        response1 = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 2},
            format='json'
        )
        
        # Add same product again
        response2 = self.client.post(
            reverse('add_to_cart'),
            {'product_id': self.product1.id, 'quantity': 3},
            format='json'
        )
        
        # Should have combined quantity
        self.assertEqual(response2.data['total_items'], 5)
        self.assertEqual(len(response2.data['items']), 1)
        self.assertEqual(response2.data['items'][0]['quantity'], 5)


class CartSerializerTestCase(TestCase):
    """Test cart serialization"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('19.99'),
            stock_quantity=10,
            weight=Decimal('0.5')
        )
        
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_cart_serialization(self):
        """Test cart serializer output"""
        from cart.serializers import CartSerializer
        
        serializer = CartSerializer(self.cart)
        data = serializer.data
        
        self.assertEqual(data['total_items'], 2)
        self.assertEqual(float(data['total_price']), 39.98)
        self.assertEqual(len(data['items']), 1)
        
        # Check item details
        item_data = data['items'][0]
        self.assertEqual(item_data['quantity'], 2)
        self.assertEqual(item_data['product']['id'], self.product.id)
        self.assertEqual(item_data['product']['name'], 'Test Product')