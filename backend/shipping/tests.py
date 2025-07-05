from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from decimal import Decimal

from orders.models import Order
from .models import ShippingRate, ShippingLabel, TrackingEvent
from .services import shippo_service

User = get_user_model()


class ShippingRateModelTest(TestCase):
    """Test ShippingRate model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            subtotal=Decimal('100.00'),
            total_amount=Decimal('110.00'),
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
    
    def test_shipping_rate_creation(self):
        """Test creating a shipping rate."""
        rate = ShippingRate.objects.create(
            order=self.order,
            goshippo_rate_id='test_rate_123',
            carrier='USPS',
            service_level='Priority',
            amount=Decimal('8.99'),
            estimated_days=3
        )
        
        self.assertEqual(rate.order, self.order)
        self.assertEqual(rate.carrier, 'USPS')
        self.assertEqual(rate.amount, Decimal('8.99'))
        self.assertEqual(str(rate), 'USPS Priority - $8.99')


class ShippingAPITest(APITestCase):
    """Test shipping API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            subtotal=Decimal('100.00'),
            total_amount=Decimal('110.00'),
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
        self.client.force_authenticate(user=self.user)
    
    @patch('shipping.services.goshippo_service.get_shipping_rates')
    def test_get_shipping_rates(self, mock_get_rates):
        """Test getting shipping rates for an order."""
        mock_get_rates.return_value = [
            {
                'id': 'rate_123',
                'carrier': 'USPS',
                'service_level': 'Priority',
                'amount': Decimal('8.99'),
                'currency': 'USD',
                'estimated_days': 3
            }
        ]
        
        url = reverse('shipping:shipping-rates')
        data = {'order_id': self.order.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['carrier'], 'USPS')
        
        # Check that rate was saved to database
        self.assertTrue(ShippingRate.objects.filter(order=self.order).exists())
    
    def test_get_shipping_rates_unauthorized(self):
        """Test getting shipping rates for another user's order."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_order = Order.objects.create(
            user=other_user,
            order_number='OTHER123',
            subtotal=Decimal('50.00'),
            total_amount=Decimal('55.00'),
            shipping_name='Other User',
            shipping_email='other@example.com',
            shipping_address='456 Other St',
            shipping_city='Other City',
            shipping_state='OS',
            shipping_postal_code='67890',
            shipping_country='US',
            billing_name='Other User',
            billing_email='other@example.com',
            billing_address='456 Other St',
            billing_city='Other City',
            billing_state='OS',
            billing_postal_code='67890',
            billing_country='US'
        )
        
        url = reverse('shipping:shipping-rates')
        data = {'order_id': other_order.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('shipping.services.goshippo_service.create_transaction')
    def test_purchase_shipping_label(self, mock_create_transaction):
        """Test purchasing a shipping label."""
        # Create a shipping rate first
        rate = ShippingRate.objects.create(
            order=self.order,
            goshippo_rate_id='test_rate_123',
            carrier='USPS',
            service_level='Priority',
            amount=Decimal('8.99'),
            estimated_days=3
        )
        
        # Mock the transaction response
        mock_transaction = MagicMock()
        mock_transaction.object_id = 'trans_123'
        mock_transaction.rate.shipment = 'shipment_123'
        mock_transaction.label_url = 'https://example.com/label.pdf'
        mock_transaction.tracking_number = '1Z999AA1234567890'
        mock_transaction.object_state = 'VALID'
        mock_create_transaction.return_value = mock_transaction
        
        url = reverse('shipping:purchase-label')
        data = {
            'rate_id': 'test_rate_123',
            'label_file_type': 'PDF'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tracking_number'], '1Z999AA1234567890')
        
        # Check that label was saved to database
        self.assertTrue(ShippingLabel.objects.filter(order=self.order).exists())
        
        # Check that order was updated with tracking number
        self.order.refresh_from_db()
        self.assertEqual(self.order.tracking_number, '1Z999AA1234567890')


class GoshippoServiceTest(TestCase):
    """Test Goshippo service methods."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            order_number='TEST123',
            subtotal=Decimal('100.00'),
            total_amount=Decimal('110.00'),
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
    
    @patch('goshippo.Address.create')
    def test_create_address(self, mock_create):
        """Test creating an address in Goshippo."""
        mock_create.return_value = {'object_id': 'addr_123'}
        
        address_data = {
            'name': 'Test User',
            'street1': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'zip': '12345',
            'country': 'US'
        }
        
        result = goshippo_service.create_address(address_data)
        
        self.assertEqual(result['object_id'], 'addr_123')
        mock_create.assert_called_once_with(**address_data)
    
    @patch('goshippo.Parcel.create')
    def test_create_parcel(self, mock_create):
        """Test creating a parcel in Goshippo."""
        mock_create.return_value = {'object_id': 'parcel_123'}
        
        result = goshippo_service.create_parcel(weight=2.5)
        
        self.assertEqual(result['object_id'], 'parcel_123')
        mock_create.assert_called_once_with(
            length='10',
            width='10',
            height='10',
            weight='2.5',
            distance_unit='in',
            mass_unit='lb'
        )