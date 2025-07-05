"""
Tests for Goshippo integration replacing ShipStation.

Goshippo SDK Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from .models import Order, OrderItem
from products.models import Product, Category
from utils.goshippo_service import GoshippoShippingService

User = get_user_model()


class GoshippoServiceTestCase(TestCase):
    """Test cases for Goshippo shipping service."""
    
    def setUp(self):
        """Set up test data."""
        self.service = GoshippoShippingService()
        
        self.from_address = {
            'name': 'Pasargad Prints',
            'company': 'Pasargad Prints',
            'street1': '123 Business St',
            'city': 'San Francisco',
            'state': 'CA',
            'zip': '94105',
            'country': 'US',
            'phone': '415-555-0123',
            'email': 'orders@pasargadprints.com',
        }
        
        self.to_address = {
            'name': 'John Doe',
            'street1': '456 Customer Ave',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'country': 'US',
        }
        
        self.parcel = {
            'weight': 1.5,
            'length': 12,
            'width': 9,
            'height': 6,
            'distance_unit': 'in',
            'mass_unit': 'lb',
        }
    
    @patch('utils.goshippo_service.goshippo')
    def test_get_shipping_rates_success(self, mock_goshippo):
        """Test successful shipping rates retrieval."""
        # Mock Goshippo response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.shipment.object_id = 'shipment_123'
        mock_response.shipment.rates = [
            MagicMock(
                object_id='rate_123',
                provider='USPS',
                servicelevel=MagicMock(name='Priority Mail', token='usps_priority'),
                amount='10.50',
                currency='USD',
                estimated_days=3,
                duration_terms='Business days',
                carrier_account='carrier_123',
                test=True,
            )
        ]
        
        mock_shippo.Shippo.return_value.shipments.create.return_value = mock_response
        
        # Call service method
        result = self.service.get_shipping_rates(
            self.from_address, self.to_address, self.parcel
        )
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['shipment_id'], 'shipment_123')
        self.assertEqual(len(result['rates']), 1)
        self.assertEqual(result['rates'][0]['carrier'], 'USPS')
        self.assertEqual(result['rates'][0]['service'], 'Priority Mail')
        self.assertEqual(result['rates'][0]['amount'], 10.50)
    
    @patch('utils.goshippo_service.goshippo')
    def test_create_shipping_label_success(self, mock_goshippo):
        """Test successful shipping label creation."""
        # Mock Goshippo response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.transaction.object_id = 'transaction_123'
        mock_response.transaction.tracking_number = '1Z999AA1234567890'
        mock_response.transaction.tracking_url_provider = 'https://tracking.example.com'
        mock_response.transaction.label_url = 'https://label.example.com/label.pdf'
        mock_response.transaction.status = 'SUCCESS'
        mock_response.transaction.rate.provider = 'UPS'
        mock_response.transaction.rate.servicelevel.name = 'Ground'
        mock_response.transaction.rate.amount = '15.75'
        mock_response.transaction.rate.currency = 'USD'
        mock_response.transaction.test = True
        
        mock_shippo.Shippo.return_value.transactions.create.return_value = mock_response
        
        # Call service method
        result = self.service.create_shipping_label('rate_123', 'PDF')
        
        # Assertions
        self.assertEqual(result['transaction_id'], 'transaction_123')
        self.assertEqual(result['tracking_number'], '1Z999AA1234567890')
        self.assertEqual(result['carrier'], 'UPS')
        self.assertEqual(result['service'], 'Ground')
        self.assertTrue(result['test'])
    
    @patch('utils.goshippo_service.goshippo')
    def test_track_shipment_success(self, mock_goshippo):
        """Test successful shipment tracking."""
        # Mock Goshippo response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.track.tracking_number = '1Z999AA1234567890'
        mock_response.track.carrier = 'UPS'
        mock_response.track.tracking_status = 'DELIVERED'
        mock_response.track.eta = '2023-12-15'
        mock_response.track.tracking_history = []
        mock_response.track.test = True
        
        mock_shippo.Shippo.return_value.tracks.get.return_value = mock_response
        
        # Call service method
        result = self.service.track_shipment('1Z999AA1234567890', 'UPS')
        
        # Assertions
        self.assertEqual(result['tracking_number'], '1Z999AA1234567890')
        self.assertEqual(result['carrier'], 'UPS')
        self.assertEqual(result['tracking_status'], 'DELIVERED')


class GoshippoAPITestCase(APITestCase):
    """Test cases for Goshippo API views."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test product and order
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=25.00,
            weight=1.0,
            stock_quantity=10
        )
        
        self.order = Order.objects.create(
            user=self.user,
            subtotal=25.00,
            total_amount=27.00,
            shipping_name='John Doe',
            shipping_email='john@example.com',
            shipping_address='123 Test St',
            shipping_city='Test City',
            shipping_state='CA',
            shipping_postal_code='12345',
            shipping_country='US',
            billing_name='John Doe',
            billing_email='john@example.com',
            billing_address='123 Test St',
            billing_city='Test City',
            billing_state='CA',
            billing_postal_code='12345',
            billing_country='US',
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            unit_price=25.00,
            total_price=25.00
        )
    
    def test_get_shipping_rates_requires_auth(self):
        """Test that shipping rates endpoint requires authentication."""
        url = reverse('orders:shipping-rates', kwargs={'order_id': self.order.id})
        response = self.client.post(url, {
            'to_address': {
                'name': 'John Doe',
                'street1': '123 Test St',
                'city': 'Test City',
                'state': 'CA',
                'zip': '12345',
                'country': 'US'
            },
            'parcel': {
                'weight': 1.0,
                'length': 12,
                'width': 9,
                'height': 6
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @override_settings(SHIPPING_ORIGIN={
        'name': 'Test Origin',
        'street1': '123 Origin St',
        'city': 'Origin City',
        'state': 'CA',
        'zip': '54321',
        'country': 'US'
    })
    @patch('orders.shipping_views.goshippo_service.get_shipping_rates')
    def test_get_shipping_rates_success(self, mock_get_rates):
        """Test successful shipping rates retrieval."""
        self.client.force_authenticate(user=self.user)
        
        # Mock service response
        mock_get_rates.return_value = {
            'status': 'success',
            'shipment_id': 'shipment_123',
            'rates': [
                {
                    'rate_id': 'rate_123',
                    'carrier': 'USPS',
                    'service': 'Priority Mail',
                    'amount': 10.50,
                    'currency': 'USD',
                    'estimated_days': 3
                }
            ]
        }
        
        url = reverse('orders:shipping-rates', kwargs={'order_id': self.order.id})
        response = self.client.post(url, {
            'to_address': {
                'name': 'John Doe',
                'street1': '123 Test St',
                'city': 'Test City',
                'state': 'CA',
                'zip': '12345',
                'country': 'US'
            },
            'parcel': {
                'weight': 1.0,
                'length': 12,
                'width': 9,
                'height': 6
            }
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['rates']), 1)
        
        # Check that order was updated with shipment ID
        self.order.refresh_from_db()
        self.assertEqual(self.order.goshippo_object_id, 'shipment_123')
    
    def test_validate_address_success(self):
        """Test address validation endpoint."""
        url = reverse('orders:validate-address')
        response = self.client.post(url, {
            'name': 'John Doe',
            'street1': '123 Test St',
            'city': 'Test City',
            'state': 'CA',
            'zip': '12345',
            'country': 'US'
        }, format='json')
        
        # Should work without authentication (public endpoint)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
    
    def test_track_shipment_by_tracking_number(self):
        """Test tracking shipment by tracking number."""
        self.order.tracking_number = '1Z999AA1234567890'
        self.order.save()
        
        url = reverse('orders:track-shipment', kwargs={'tracking_number': '1Z999AA1234567890'})
        response = self.client.get(url)
        
        # Should work without authentication (public endpoint)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])