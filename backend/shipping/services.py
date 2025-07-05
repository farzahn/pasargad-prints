"""
Goshippo API service for shipping operations.

Goshippo SDK Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""

import shippo
from django.conf import settings
from decimal import Decimal
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GoshippoService:
    """Service class for interacting with Goshippo API."""
    
    def __init__(self):
        """Initialize Goshippo client with API key."""
        self.api_key = getattr(settings, 'GOSHIPPO_API_KEY', 'shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15')
        self.client = shippo.Shippo(
            security=goshippo.Security(
                api_key_header=self.api_key
            )
        )
        self.test_mode = getattr(settings, 'GOSHIPPO_TEST_MODE', True)
        
    def create_address(self, address_data: Dict) -> Dict:
        """
        Create an address object in Goshippo.
        
        Args:
            address_data: Dictionary containing address information
            
        Returns:
            Dictionary containing Goshippo address object
        """
        try:
            address = shippo.Address.create(**address_data)
            return address
        except Exception as e:
            logger.error(f"Error creating address: {e}")
            raise
    
    def create_parcel(self, weight: float, length: float = 10, width: float = 10, height: float = 10) -> Dict:
        """
        Create a parcel object in Goshippo.
        
        Args:
            weight: Weight in pounds
            length: Length in inches (default: 10)
            width: Width in inches (default: 10)
            height: Height in inches (default: 10)
            
        Returns:
            Dictionary containing Goshippo parcel object
        """
        try:
            parcel = shippo.Parcel.create(
                length=str(length),
                width=str(width),
                height=str(height),
                weight=str(weight),
                distance_unit="in",
                mass_unit="lb"
            )
            return parcel
        except Exception as e:
            logger.error(f"Error creating parcel: {e}")
            raise
    
    def create_shipment(self, address_from: Dict, address_to: Dict, parcels: List[Dict]) -> Dict:
        """
        Create a shipment in Goshippo to get shipping rates.
        
        Args:
            address_from: Origin address dictionary
            address_to: Destination address dictionary
            parcels: List of parcel dictionaries
            
        Returns:
            Dictionary containing Goshippo shipment object with rates
        """
        try:
            shipment = shippo.Shipment.create(
                address_from=address_from,
                address_to=address_to,
                parcels=parcels,
                async_=False  # Wait for rates to be calculated
            )
            return shipment
        except Exception as e:
            logger.error(f"Error creating shipment: {e}")
            raise
    
    def get_shipping_rates(self, order) -> List[Dict]:
        """
        Get shipping rates for an order.
        
        Args:
            order: Order instance
            
        Returns:
            List of shipping rates
        """
        try:
            # Create address objects
            address_from = self.create_address({
                'name': getattr(settings, 'COMPANY_NAME', 'Pasargad Prints'),
                'street1': getattr(settings, 'COMPANY_ADDRESS_1', '123 Main St'),
                'street2': getattr(settings, 'COMPANY_ADDRESS_2', ''),
                'city': getattr(settings, 'COMPANY_CITY', 'San Francisco'),
                'state': getattr(settings, 'COMPANY_STATE', 'CA'),
                'zip': getattr(settings, 'COMPANY_ZIP', '94105'),
                'country': getattr(settings, 'COMPANY_COUNTRY', 'US'),
                'phone': getattr(settings, 'COMPANY_PHONE', ''),
                'email': getattr(settings, 'COMPANY_EMAIL', 'info@pasargadprints.com')
            })
            
            address_to = self.create_address({
                'name': order.shipping_name,
                'street1': order.shipping_address.split('\\n')[0],
                'street2': order.shipping_address.split('\\n')[1] if len(order.shipping_address.split('\\n')) > 1 else '',
                'city': order.shipping_city,
                'state': order.shipping_state,
                'zip': order.shipping_postal_code,
                'country': order.shipping_country,
                'phone': order.shipping_phone,
                'email': order.shipping_email
            })
            
            # Create parcel (simplified - assuming one parcel per order)
            total_weight = float(order.total_weight)
            parcel = self.create_parcel(weight=total_weight)
            
            # Create shipment to get rates
            shipment = self.create_shipment(
                address_from=address_from,
                address_to=address_to,
                parcels=[parcel]
            )
            
            # Extract rates from shipment
            rates = []
            for rate in shipment.rates:
                if rate.object_state == 'VALID':
                    rates.append({
                        'id': rate.object_id,
                        'carrier': rate.provider,
                        'service_level': rate.servicelevel.name,
                        'amount': Decimal(rate.amount),
                        'currency': rate.currency,
                        'estimated_days': rate.estimated_days,
                        'duration_terms': rate.duration_terms
                    })
            
            return rates
        except Exception as e:
            logger.error(f"Error getting shipping rates: {e}")
            raise
    
    def create_transaction(self, rate_id: str, label_file_type: str = 'PDF') -> Dict:
        """
        Create a transaction (purchase shipping label) in Goshippo.
        
        Args:
            rate_id: Goshippo rate ID
            label_file_type: Label file type (PDF, PNG, etc.)
            
        Returns:
            Dictionary containing Goshippo transaction object
        """
        try:
            transaction = shippo.Transaction.create(
                rate=rate_id,
                label_file_type=label_file_type,
                async_=False
            )
            return transaction
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    def get_tracking_info(self, carrier: str, tracking_number: str) -> Dict:
        """
        Get tracking information for a shipment.
        
        Args:
            carrier: Carrier name (e.g., 'usps', 'ups', 'fedex')
            tracking_number: Tracking number
            
        Returns:
            Dictionary containing tracking information
        """
        try:
            track = shippo.Track.get(carrier, tracking_number)
            return track
        except Exception as e:
            logger.error(f"Error getting tracking info: {e}")
            raise
    
    def register_webhook(self, webhook_url: str, event_type: str = 'track_updated') -> Dict:
        """
        Register a webhook for tracking updates.
        
        Args:
            webhook_url: URL to receive webhook notifications
            event_type: Type of event to track
            
        Returns:
            Dictionary containing webhook registration response
        """
        try:
            webhook = shippo.Webhook.create(
                url=webhook_url,
                event_types=[event_type],
                active=True
            )
            return webhook
        except Exception as e:
            logger.error(f"Error registering webhook: {e}")
            raise


# Singleton instance
goshippo_service = GoshippoService()