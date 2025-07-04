"""
Goshippo API integration service for managing shipments and tracking.
"""
import logging
from typing import Dict, Optional, Any
from decimal import Decimal
from django.conf import settings
import shippo

logger = logging.getLogger(__name__)


class GoshippoService:
    """Service class for interacting with Goshippo API."""
    
    def __init__(self):
        """Initialize Goshippo with API token from settings."""
        self.api_token = getattr(settings, 'GOSHIPPO_API_KEY', None)
        if not self.api_token:
            logger.error("GOSHIPPO_API_KEY not found in settings")
            raise ValueError("Goshippo API token not configured")
        
        shippo.config.api_key = self.api_token
        # Set to True for live mode, False for test mode
        shippo.config.api_version = getattr(settings, 'GOSHIPPO_API_VERSION', '2018-02-08')
    
    def create_shipment(self, order) -> Optional[Dict[str, Any]]:
        """
        Create a shipment in Goshippo for the given order.
        
        Args:
            order: Order instance to create shipment for
            
        Returns:
            dict: Goshippo shipment object or None if failed
        """
        try:
            # Create address_from (your business address)
            address_from = self._create_address_from()
            
            # Create address_to (customer's shipping address)
            address_to = self._create_address_to(order)
            
            # Create parcel (package dimensions and weight)
            parcel = self._create_parcel(order)
            
            # Create the shipment
            shipment = shippo.Shipment.create(
                address_from=address_from,
                address_to=address_to,
                parcels=[parcel],
                async_=False  # Wait for rates to be calculated
            )
            
            if shipment.status == 'SUCCESS':
                logger.info(f"Created Goshippo shipment {shipment.object_id} for order {order.order_number}")
                return shipment
            else:
                logger.error(f"Failed to create shipment for order {order.order_number}: {shipment.messages}")
                return None
                
        except Exception as e:
            logger.exception(f"Error creating shipment for order {order.order_number}")
            return None
    
    def create_transaction(self, shipment_id: str, rate_id: str) -> Optional[Dict[str, Any]]:
        """
        Create a transaction (purchase a shipping label).
        
        Args:
            shipment_id: Goshippo shipment ID
            rate_id: Rate ID from shipment rates
            
        Returns:
            dict: Transaction object or None if failed
        """
        try:
            transaction = shippo.Transaction.create(
                rate=rate_id,
                label_file_type="PDF",
                async_=False
            )
            
            if transaction.status == 'SUCCESS':
                logger.info(f"Created transaction {transaction.object_id} for shipment {shipment_id}")
                return transaction
            else:
                logger.error(f"Failed to create transaction for shipment {shipment_id}: {transaction.messages}")
                return None
                
        except Exception as e:
            logger.exception(f"Error creating transaction for shipment {shipment_id}")
            return None
    
    def get_tracking_info(self, tracking_number: str, carrier: str = None) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a shipment.
        
        Args:
            tracking_number: Tracking number
            carrier: Carrier name (optional)
            
        Returns:
            dict: Tracking information or None if failed
        """
        try:
            if carrier:
                track = shippo.Track.get_status(carrier, tracking_number)
            else:
                # Try to get tracking info without specifying carrier
                track = shippo.Track.get_status('usps', tracking_number)  # Default to USPS
                
            logger.info(f"Retrieved tracking info for {tracking_number}")
            return track
            
        except Exception as e:
            logger.exception(f"Error retrieving tracking info for {tracking_number}")
            return None
    
    def _create_address_from(self) -> Dict[str, Any]:
        """Create the 'from' address (your business address)."""
        shipping_origin = getattr(settings, 'SHIPPING_ORIGIN', {})
        return {
            "name": shipping_origin.get('name', 'Pasargad Prints'),
            "company": shipping_origin.get('company', 'Pasargad Prints'),
            "street1": shipping_origin.get('street1', '123 Business St'),
            "street2": shipping_origin.get('street2', ''),
            "city": shipping_origin.get('city', 'Los Angeles'),
            "state": shipping_origin.get('state', 'CA'),
            "zip": shipping_origin.get('zip', '90210'),
            "country": shipping_origin.get('country', 'US'),
            "phone": shipping_origin.get('phone', '+1 555 123 4567'),
            "email": shipping_origin.get('email', 'orders@pasargadprints.com')
        }
    
    def _create_address_to(self, order) -> Dict[str, Any]:
        """Create the 'to' address from order shipping information."""
        return {
            "name": order.shipping_name,
            "street1": order.shipping_address,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "zip": order.shipping_postal_code,
            "country": order.shipping_country,
            "phone": order.shipping_phone or '',
            "email": order.shipping_email
        }
    
    def _create_parcel(self, order) -> Dict[str, Any]:
        """Create parcel information from order items."""
        total_weight = float(order.total_weight)
        
        # Default dimensions if not specified
        length = getattr(settings, 'DEFAULT_PACKAGE_LENGTH', 12)
        width = getattr(settings, 'DEFAULT_PACKAGE_WIDTH', 9)
        height = getattr(settings, 'DEFAULT_PACKAGE_HEIGHT', 6)
        
        return {
            "length": str(length),
            "width": str(width),
            "height": str(height),
            "distance_unit": "in",
            "weight": str(max(total_weight, 0.1)),  # Minimum weight 0.1 lbs
            "mass_unit": "lb"
        }
    
    def get_cheapest_rate(self, shipment) -> Optional[Dict[str, Any]]:
        """Get the cheapest shipping rate from a shipment."""
        try:
            if not shipment.rates:
                logger.warning(f"No rates available for shipment {shipment.object_id}")
                return None
            
            # Filter out rates with errors
            valid_rates = [rate for rate in shipment.rates if not rate.messages]
            
            if not valid_rates:
                logger.warning(f"No valid rates for shipment {shipment.object_id}")
                return None
            
            # Sort by amount and return cheapest
            cheapest_rate = min(valid_rates, key=lambda r: float(r.amount))
            logger.info(f"Found cheapest rate: {cheapest_rate.provider} - ${cheapest_rate.amount}")
            return cheapest_rate
            
        except Exception as e:
            logger.exception(f"Error finding cheapest rate for shipment {shipment.object_id}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Goshippo webhook signature.
        
        Args:
            payload: Request payload
            signature: Signature from request headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            webhook_secret = getattr(settings, 'GOSHIPPO_WEBHOOK_SECRET', None)
            if not webhook_secret:
                logger.error("GOSHIPPO_WEBHOOK_SECRET not configured")
                return False
            
            # Use Goshippo's webhook verification
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.exception("Error verifying webhook signature")
            return False
    
    def parse_tracking_status(self, goshippo_status: str) -> str:
        """
        Map Goshippo tracking status to our order status.
        
        Args:
            goshippo_status: Status from Goshippo
            
        Returns:
            str: Mapped order status
        """
        status_mapping = {
            'UNKNOWN': 'processing',
            'PRE_TRANSIT': 'processing',
            'TRANSIT': 'shipped',
            'DELIVERED': 'delivered',
            'RETURNED': 'cancelled',
            'FAILURE': 'cancelled',
            'CANCELLED': 'cancelled'
        }
        
        return status_mapping.get(goshippo_status.upper(), 'processing')