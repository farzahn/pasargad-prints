from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal

from .models import Order, OrderItem, OrderStatusHistory
from products.models import Product, Category

User = get_user_model()


class OrderAPITestCase(APITestCase):
    """Test cases for Order Management API."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        # Create test category and products
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            description='Test description',
            price=Decimal('29.99'),
            stock_quantity=100,
            sku='TEST001',
            weight=Decimal('1.5')
        )
        
        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            status='pending',
            subtotal=Decimal('29.99'),
            tax_amount=Decimal('2.40'),
            shipping_cost=Decimal('5.00'),
            total_amount=Decimal('37.39'),
            shipping_name='Test User',
            shipping_email='testuser@example.com',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='US',
            billing_name='Test User',
            billing_email='testuser@example.com',
            billing_address='123 Test St',
            billing_city='Test City',
            billing_state='TS',
            billing_postal_code='12345',
            billing_country='US'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=self.product.price,
            total_price=self.product.price
        )
        
        # Set up authentication
        self.user_token = RefreshToken.for_user(self.user)
        self.admin_token = RefreshToken.for_user(self.admin_user)
    
    def test_list_orders_authenticated(self):
        """Test listing orders for authenticated user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token.access_token}')
        response = self.client.get('/api/orders/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['order_number'], self.order.order_number)
    
    def test_list_orders_unauthenticated(self):
        """Test listing orders requires authentication."""
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_order_detail_owner(self):
        """Test order detail view for order owner."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token.access_token}')
        response = self.client.get(f'/api/orders/{self.order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], self.order.order_number)
        self.assertEqual(len(response.data['items']), 1)
    
    def test_order_detail_non_owner(self):
        """Test order detail view blocks non-owners."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        other_token = RefreshToken.for_user(other_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token.access_token}')
        response = self.client.get(f'/api/orders/{self.order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_order_detail_admin(self):
        """Test admin can view any order."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        response = self.client.get(f'/api/orders/{self.order.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_order_tracking_public(self):
        """Test public order tracking."""
        # Add tracking number to order
        self.order.tracking_number = 'TEST123456'
        self.order.save()
        
        response = self.client.get(f'/api/orders/track/{self.order.tracking_number}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], self.order.order_number)
        self.assertEqual(len(response.data['items']), 1)
    
    def test_order_status_update_admin_only(self):
        """Test only admin can update order status."""
        # Try as regular user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token.access_token}')
        response = self.client.patch(
            f'/api/orders/{self.order.id}/status/',
            {'status': 'processing', 'notes': 'Processing order'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try as admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        response = self.client.patch(
            f'/api/orders/{self.order.id}/status/',
            {'status': 'processing', 'notes': 'Processing order'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
        
        # Check status history
        history = self.order.status_history.first()
        self.assertIsNotNone(history)
        self.assertEqual(history.status, 'processing')
        self.assertEqual(history.created_by, self.admin_user)
    
    def test_order_status_invalid_transition(self):
        """Test invalid status transitions are blocked."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        # Try invalid transition from pending to delivered
        response = self.client.patch(
            f'/api/orders/{self.order.id}/status/',
            {'status': 'delivered'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition', str(response.data))
    
    def test_order_filtering(self):
        """Test order list filtering."""
        # Create additional order with different status
        Order.objects.create(
            user=self.user,
            status='shipped',
            subtotal=Decimal('50.00'),
            total_amount=Decimal('55.00'),
            shipping_name='Test User 2',
            shipping_email='test2@example.com',
            shipping_address='456 Test Ave',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='US',
            billing_name='Test User 2',
            billing_email='test2@example.com',
            billing_address='456 Test Ave',
            billing_city='Test City',
            billing_state='TS',
            billing_postal_code='12345',
            billing_country='US'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token.access_token}')
        
        # Filter by status
        response = self.client.get('/api/orders/?status=pending')
        self.assertEqual(response.data['count'], 1)
        
        # Search by order number
        response = self.client.get(f'/api/orders/?search={self.order.order_number[:4]}')
        self.assertEqual(response.data['count'], 1)
    
    def test_order_pagination(self):
        """Test order list pagination."""
        # Create multiple orders
        for i in range(15):
            Order.objects.create(
                user=self.user,
                status='pending',
                subtotal=Decimal('10.00'),
                total_amount=Decimal('10.00'),
                shipping_name=f'User {i}',
                shipping_email=f'user{i}@example.com',
                shipping_address=f'{i} Test St',
                shipping_city='Test City',
                shipping_state='TS',
                shipping_postal_code='12345',
                shipping_country='US',
                billing_name=f'User {i}',
                billing_email=f'user{i}@example.com',
                billing_address=f'{i} Test St',
                billing_city='Test City',
                billing_state='TS',
                billing_postal_code='12345',
                billing_country='US'
            )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token.access_token}')
        
        # Test default page size
        response = self.client.get('/api/orders/')
        self.assertEqual(len(response.data['results']), 10)
        
        # Test custom page size
        response = self.client.get('/api/orders/?page_size=5')
        self.assertEqual(len(response.data['results']), 5)