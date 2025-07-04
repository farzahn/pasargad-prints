from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order, OrderItem, OrderStatusHistory
from products.models import Product, Category

User = get_user_model()


class OrderTrackingTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('29.99'),
            stock_quantity=10,
            weight=Decimal('0.5')
        )
        
        # Create test order with tracking number
        self.order_with_tracking = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            status='shipped',
            tracking_number='TRACK123456',
            subtotal=Decimal('29.99'),
            total_amount=Decimal('34.99'),
            shipping_cost=Decimal('5.00'),
            shipping_name='Test User',
            shipping_email='test@example.com',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='US',
            billing_name='Test User',
            billing_email='test@example.com',
            billing_address='123 Test St',
            billing_city='Test City',
            billing_state='TS',
            billing_postal_code='12345',
            billing_country='US'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=self.order_with_tracking,
            product=self.product,
            quantity=1,
            unit_price=Decimal('29.99'),
            product_name='Test Product'
        )
        
        # Create guest order
        self.guest_order = Order.objects.create(
            user=None,  # Guest order
            order_number='GUEST456',
            status='processing',
            session_key='guest_session_123',
            subtotal=Decimal('59.98'),
            total_amount=Decimal('64.98'),
            shipping_cost=Decimal('5.00'),
            shipping_name='Guest User',
            shipping_email='guest@example.com',
            shipping_address='456 Guest Ave',
            shipping_city='Guest City',
            shipping_state='GS',
            shipping_postal_code='54321',
            shipping_country='US',
            billing_name='Guest User',
            billing_email='guest@example.com',
            billing_address='456 Guest Ave',
            billing_city='Guest City',
            billing_state='GS',
            billing_postal_code='54321',
            billing_country='US'
        )
    
    def test_track_order_by_tracking_number(self):
        """Test tracking order by tracking number"""
        url = reverse('orders:order-tracking', kwargs={'tracking_number': 'TRACK123456'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'TEST123')
        self.assertEqual(response.data['status'], 'shipped')
        self.assertEqual(response.data['tracking_number'], 'TRACK123456')
        self.assertIn('items', response.data)
        
    def test_track_order_by_invalid_tracking_number(self):
        """Test tracking with invalid tracking number"""
        url = reverse('orders:order-tracking', kwargs={'tracking_number': 'INVALID'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_track_order_by_id(self):
        """Test tracking order by order ID"""
        url = reverse('orders:order-tracking-by-id', kwargs={'id': self.order_with_tracking.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'TEST123')
        
    def test_guest_order_tracking_success(self):
        """Test successful guest order tracking"""
        url = reverse('orders:guest-order-tracking')
        data = {
            'order_number': 'GUEST456',
            'email': 'guest@example.com'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'GUEST456')
        self.assertEqual(response.data['status'], 'processing')
        
    def test_guest_order_tracking_case_insensitive(self):
        """Test guest tracking is case insensitive"""
        url = reverse('orders:guest-order-tracking')
        data = {
            'order_number': 'guest456',  # lowercase
            'email': 'GUEST@EXAMPLE.COM'  # uppercase
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'GUEST456')
        
    def test_guest_order_tracking_billing_email(self):
        """Test guest tracking works with billing email"""
        # Create order with different shipping/billing emails
        order = Order.objects.create(
            user=None,
            order_number='BILLING123',
            status='processing',
            subtotal=Decimal('29.99'),
            total_amount=Decimal('29.99'),
            shipping_name='Ship Name',
            shipping_email='shipping@example.com',
            shipping_address='123 Ship St',
            shipping_city='Ship City',
            shipping_state='SS',
            shipping_postal_code='11111',
            shipping_country='US',
            billing_name='Bill Name',
            billing_email='billing@example.com',
            billing_address='456 Bill Ave',
            billing_city='Bill City',
            billing_state='BS',
            billing_postal_code='22222',
            billing_country='US'
        )
        
        url = reverse('orders:guest-order-tracking')
        data = {
            'order_number': 'BILLING123',
            'email': 'billing@example.com'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_number'], 'BILLING123')
        
    def test_guest_order_tracking_invalid_email(self):
        """Test guest tracking with wrong email"""
        url = reverse('orders:guest-order-tracking')
        data = {
            'order_number': 'GUEST456',
            'email': 'wrong@example.com'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['error'])
        
    def test_guest_order_tracking_missing_fields(self):
        """Test guest tracking with missing fields"""
        url = reverse('orders:guest-order-tracking')
        
        # Missing email
        response = self.client.post(url, {'order_number': 'TEST'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Missing order number
        response = self.client.post(url, {'email': 'test@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Empty request
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OrderStatusUpdateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Create test order
        self.order = Order.objects.create(
            user=self.regular_user,
            order_number='UPDATE123',
            status='pending',
            subtotal=Decimal('29.99'),
            total_amount=Decimal('29.99'),
            shipping_name='Test User',
            shipping_email='test@example.com',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='US',
            billing_name='Test User',
            billing_email='test@example.com',
            billing_address='123 Test St',
            billing_city='Test City',
            billing_state='TS',
            billing_postal_code='12345',
            billing_country='US'
        )
        
    def test_admin_can_update_status(self):
        """Test admin can update order status"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('orders:order-status-update', kwargs={'pk': self.order.pk})
        data = {
            'status': 'processing',
            'notes': 'Order is being prepared'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
        
        # Check status history was created
        history = OrderStatusHistory.objects.filter(order=self.order).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.status, 'processing')
        self.assertEqual(history.notes, 'Order is being prepared')
        self.assertEqual(history.created_by, self.admin_user)
        
    def test_regular_user_cannot_update_status(self):
        """Test regular user cannot update order status"""
        self.client.force_authenticate(user=self.regular_user)
        
        url = reverse('orders:order-status-update', kwargs={'pk': self.order.pk})
        data = {'status': 'processing'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_invalid_status_transition(self):
        """Test invalid status transitions are rejected"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Set order to delivered
        self.order.status = 'delivered'
        self.order.save()
        
        # Try to transition back to pending (not allowed)
        url = reverse('orders:order-status-update', kwargs={'pk': self.order.pk})
        data = {'status': 'pending'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transition', str(response.data))
        
    def test_shipped_status_updates_timestamp(self):
        """Test shipped status updates shipped_at timestamp"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Update to processing first
        self.order.status = 'processing'
        self.order.save()
        
        url = reverse('orders:order-status-update', kwargs={'pk': self.order.pk})
        data = {'status': 'shipped'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.shipped_at)