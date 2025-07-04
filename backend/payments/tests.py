import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from cart.models import Cart, CartItem
from products.models import Product, Category
from orders.models import Order, OrderItem
from payments.models import Payment, StripeWebhookEvent

User = get_user_model()


class PaymentViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
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
        
    def test_create_checkout_session_empty_cart(self):
        """Test creating checkout session with empty cart"""
        self.client.force_login(self.user)
        
        url = reverse('create_checkout_session')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Cart is empty')
    
    @patch('payments.views.CheckoutSession')
    def test_create_checkout_session_authenticated_user(self, mock_checkout):
        """Test creating checkout session for authenticated user"""
        # Setup mock
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_checkout.create.return_value = mock_session
        
        # Create cart with items
        self.client.force_login(self.user)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        url = reverse('create_checkout_session')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['checkout_session_id'], 'cs_test_123')
        self.assertEqual(data['checkout_url'], 'https://checkout.stripe.com/test')
        
        # Verify checkout session was created with correct parameters
        mock_checkout.create.assert_called_once()
        call_args = mock_checkout.create.call_args[1]
        self.assertEqual(call_args['mode'], 'payment')
        self.assertEqual(len(call_args['line_items']), 1)
        self.assertEqual(call_args['line_items'][0]['quantity'], 2)
        self.assertEqual(call_args['metadata']['cart_id'], str(cart.id))
        self.assertEqual(call_args['metadata']['user_id'], str(self.user.id))
    
    @patch('payments.views.CheckoutSession')
    def test_create_checkout_session_guest_user(self, mock_checkout):
        """Test creating checkout session for guest user"""
        # Setup mock
        mock_session = MagicMock()
        mock_session.id = 'cs_test_456'
        mock_session.url = 'https://checkout.stripe.com/test'
        mock_checkout.create.return_value = mock_session
        
        # Create session and cart
        session = self.client.session
        session.save()
        
        cart = Cart.objects.create(session_key=session.session_key)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        
        url = reverse('create_checkout_session')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['checkout_session_id'], 'cs_test_456')
        
        # Verify guest checkout parameters
        call_args = mock_checkout.create.call_args[1]
        self.assertIsNone(call_args['customer_email'])
        self.assertEqual(call_args['metadata']['cart_id'], str(cart.id))
        self.assertEqual(call_args['metadata']['session_key'], session.session_key)
        self.assertNotIn('user_id', call_args['metadata'])
    
    @patch('payments.views.settings')
    def test_create_checkout_session_no_stripe_key(self, mock_settings):
        """Test handling missing Stripe configuration"""
        mock_settings.STRIPE_SECRET_KEY = ''
        
        self.client.force_login(self.user)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        
        url = reverse('create_checkout_session')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 503)
        self.assertIn('not configured', response.json()['error'])
    
    @patch('payments.views.CheckoutSession')
    def test_verify_checkout_session_success(self, mock_checkout):
        """Test verifying successful checkout session"""
        # Create order and payment
        order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            status='processing',
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
        
        payment = Payment.objects.create(
            order=order,
            user=self.user,
            status='completed',
            payment_method='stripe',
            amount=Decimal('29.99'),
            stripe_payment_intent_id='pi_test_123'
        )
        
        # Mock checkout session
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = 'pi_test_123'
        
        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_session.payment_intent = mock_payment_intent
        mock_checkout.retrieve.return_value = mock_session
        
        url = reverse('verify_checkout_session')
        response = self.client.get(url, {'session_id': 'cs_test_123'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['order_id'], order.id)
        self.assertEqual(data['order_number'], 'TEST123')
    
    def test_verify_checkout_session_no_session_id(self):
        """Test verify endpoint without session ID"""
        url = reverse('verify_checkout_session')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Session ID is required')
    
    def test_stripe_webhook_missing_signature(self):
        """Test webhook endpoint with missing signature"""
        url = reverse('stripe_webhook')
        response = self.client.post(
            url,
            data='{}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('payments.views.stripe.Webhook.construct_event')
    def test_stripe_webhook_duplicate_event(self, mock_construct):
        """Test webhook handling of duplicate events"""
        # Create existing event
        StripeWebhookEvent.objects.create(
            stripe_event_id='evt_test_123',
            event_type='checkout.session.completed',
            processed=True
        )
        
        # Mock event
        mock_event = {
            'id': 'evt_test_123',
            'type': 'checkout.session.completed',
            'data': {'object': {}}
        }
        mock_construct.return_value = mock_event
        
        url = reverse('stripe_webhook')
        response = self.client.post(
            url,
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig'
        )
        
        self.assertEqual(response.status_code, 200)
        # Verify no new event was created
        self.assertEqual(StripeWebhookEvent.objects.count(), 1)
    
    @patch('payments.views.stripe.Webhook.construct_event')
    @patch('payments.views._handle_successful_payment')
    def test_stripe_webhook_checkout_completed(self, mock_handle_payment, mock_construct):
        """Test webhook handling of successful checkout"""
        mock_event = {
            'id': 'evt_test_456',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_789',
                    'payment_intent': 'pi_test_789'
                }
            }
        }
        mock_construct.return_value = mock_event
        
        url = reverse('stripe_webhook')
        response = self.client.post(
            url,
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig'
        )
        
        self.assertEqual(response.status_code, 200)
        mock_handle_payment.assert_called_once()
        
        # Verify event was saved
        event = StripeWebhookEvent.objects.get(stripe_event_id='evt_test_456')
        self.assertTrue(event.processed)
        self.assertIsNotNone(event.processed_at)


class PaymentHelpersTestCase(TestCase):
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
            price=Decimal('29.99'),
            stock_quantity=10,
            weight=Decimal('0.5')
        )
        
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    @patch('payments.views.email_service.send_order_confirmation')
    def test_handle_successful_payment_creates_order(self, mock_email):
        """Test that successful payment creates order correctly"""
        from payments.views import _handle_successful_payment
        
        session = {
            'id': 'cs_test_123',
            'payment_intent': 'pi_test_123',
            'amount_subtotal': 5998,  # $59.98
            'amount_total': 6498,     # $64.98 (with shipping)
            'total_details': {
                'amount_tax': 0,
                'amount_shipping': 500  # $5.00
            },
            'metadata': {
                'cart_id': str(self.cart.id),
                'user_id': str(self.user.id)
            },
            'customer_details': {
                'email': 'test@example.com',
                'phone': '+1234567890'
            },
            'shipping_details': {
                'name': 'Test User',
                'address': {
                    'line1': '123 Test St',
                    'city': 'Test City',
                    'state': 'TS',
                    'postal_code': '12345',
                    'country': 'US'
                }
            }
        }
        
        _handle_successful_payment(session)
        
        # Verify order was created
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'processing')
        self.assertEqual(order.subtotal, Decimal('59.98'))
        self.assertEqual(order.shipping_cost, Decimal('5.00'))
        self.assertEqual(order.total_amount, Decimal('64.98'))
        self.assertEqual(order.shipping_name, 'Test User')
        
        # Verify order items
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal('29.99'))
        
        # Verify payment was created
        payment = Payment.objects.get()
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.stripe_payment_intent_id, 'pi_test_123')
        self.assertEqual(payment.status, 'completed')
        
        # Verify cart was cleared
        self.assertEqual(self.cart.items.count(), 0)
        
        # Verify email was sent
        mock_email.assert_called_once_with(order)
    
    def test_handle_successful_payment_idempotent(self):
        """Test that duplicate payment intents don't create multiple orders"""
        from payments.views import _handle_successful_payment
        
        # Create existing payment
        order = Order.objects.create(
            user=self.user,
            order_number='EXISTING123',
            status='processing',
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
        
        Payment.objects.create(
            order=order,
            user=self.user,
            status='completed',
            payment_method='stripe',
            amount=Decimal('29.99'),
            stripe_payment_intent_id='pi_test_duplicate'
        )
        
        session = {
            'id': 'cs_test_dup',
            'payment_intent': 'pi_test_duplicate',
            'metadata': {'cart_id': str(self.cart.id)}
        }
        
        # Should not create another order
        _handle_successful_payment(session)
        
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)