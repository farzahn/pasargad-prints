"""
Goshippo shipping service integration for order fulfillment.
Replaces the previous ShipStation integration.

Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
import os
import logging
from typing import Dict, Optional, Any
from decimal import Decimal

import shippo
from django.conf import settings
from django.utils import timezone

from .models import Order

logger = logging.getLogger(__name__)


class GoshippoShippingService:
    """
    Service class for integrating with Goshippo API for shipping operations.
    """
    
    def __init__(self):
        """Initialize Goshippo with API key from settings."""
        self.api_key = getattr(settings, 'GOSHIPPO_API_KEY', None)
        if not self.api_key:
            raise ValueError("GOSHIPPO_API_KEY not found in settings")
        
        # Set the API key for the goshippo library
        goshippo.api_key = self.api_key
        
        # Use test mode if specified in settings
        self.test_mode = getattr(settings, 'GOSHIPPO_TEST_MODE', False)
    
    def create_shipment(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Create a shipment in Goshippo for the given order.
        
        Args:
            order: Order instance to create shipment for
            
        Returns:
            Dictionary containing shipment data or None if failed
        """
        try:
            # Create address_from (your business address)
            address_from = goshippo.Address.create(
                name=getattr(settings, 'BUSINESS_NAME', 'Pasargad Prints'),
                street1=getattr(settings, 'BUSINESS_ADDRESS', ''),
                city=getattr(settings, 'BUSINESS_CITY', ''),
                state=getattr(settings, 'BUSINESS_STATE', ''),
                zip=getattr(settings, 'BUSINESS_ZIP', ''),
                country=getattr(settings, 'BUSINESS_COUNTRY', 'US'),
                phone=getattr(settings, 'BUSINESS_PHONE', ''),
                email=getattr(settings, 'BUSINESS_EMAIL', '')
            )
            
            # Create address_to (customer address)
            address_to = goshippo.Address.create(
                name=order.shipping_name,
                street1=order.shipping_address,
                city=order.shipping_city,
                state=order.shipping_state,
                zip=order.shipping_postal_code,
                country=order.shipping_country,
                phone=order.shipping_phone,
                email=order.shipping_email
            )
            
            # Create parcel with order dimensions and weight
            parcel = goshippo.Parcel.create(
                length=str(getattr(settings, 'DEFAULT_PACKAGE_LENGTH', 10)),
                width=str(getattr(settings, 'DEFAULT_PACKAGE_WIDTH', 10)),
                height=str(getattr(settings, 'DEFAULT_PACKAGE_HEIGHT', 10)),
                distance_unit="in",
                weight=str(float(order.total_weight) if order.total_weight else 1.0),
                mass_unit="lb"
            )
            
            # Create shipment
            shipment = goshippo.Shipment.create(
                address_from=address_from,
                address_to=address_to,
                parcels=[parcel],
                extra={
                    'reference_1': order.order_number,
                    'reference_2': f'Order-{order.id}'
                }
            )
            
            logger.info(f"Created Goshippo shipment for order {order.order_number}")
            return shipment
            
        except Exception as e:
            logger.error(f"Error creating Goshippo shipment for order {order.order_number}: {str(e)}")
            return None
    
    def get_shipping_rates(self, order: Order) -> Optional[list]:
        """
        Get available shipping rates for an order.
        
        Args:
            order: Order instance to get rates for
            
        Returns:
            List of shipping rates or None if failed
        """
        try:
            shipment = self.create_shipment(order)
            if not shipment:
                return None
            
            # Get rates from the shipment
            rates = shipment.get('rates', [])
            
            # Filter and format rates
            available_rates = []
            for rate in rates:
                if rate.get('amount') and rate.get('provider'):
                    available_rates.append({
                        'carrier': rate.get('provider'),
                        'service': rate.get('servicelevel', {}).get('name', 'Standard'),
                        'amount': Decimal(rate.get('amount')),
                        'currency': rate.get('currency', 'USD'),
                        'estimated_days': rate.get('estimated_days'),
                        'rate_id': rate.get('object_id')
                    })
            
            return available_rates
            
        except Exception as e:
            logger.error(f"Error getting shipping rates for order {order.order_number}: {str(e)}")
            return None
    
    def create_shipping_label(self, order: Order, rate_id: str) -> Optional[Dict[str, Any]]:
        """
        Create a shipping label for the given order using the specified rate.
        
        Args:
            order: Order instance to create label for
            rate_id: ID of the selected shipping rate
            
        Returns:
            Dictionary containing label data or None if failed
        """
        try:
            # Create transaction (purchase the label)
            transaction = goshippo.Transaction.create(
                rate=rate_id,
                label_file_type="PDF",
                async_process=False
            )
            
            if transaction.get('status') == 'SUCCESS':
                # Update order with tracking information
                order.tracking_number = transaction.get('tracking_number', '')
                order.goshippo_order_id = transaction.get('object_id', '')
                order.status = 'shipped'
                order.shipped_at = timezone.now()
                order.save()
                
                logger.info(f"Created shipping label for order {order.order_number}")
                
                return {
                    'tracking_number': transaction.get('tracking_number'),
                    'label_url': transaction.get('label_url'),
                    'transaction_id': transaction.get('object_id'),
                    'carrier': transaction.get('rate', {}).get('provider'),
                    'service': transaction.get('rate', {}).get('servicelevel', {}).get('name')
                }
            else:
                logger.error(f"Failed to create shipping label for order {order.order_number}: {transaction.get('messages', [])}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating shipping label for order {order.order_number}: {str(e)}")
            return None
    
    def track_shipment(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Track a shipment using its tracking number.
        
        Args:
            tracking_number: The tracking number to track
            
        Returns:
            Dictionary containing tracking data or None if failed
        """
        try:
            # Create tracking object
            tracking = goshippo.Track.create(
                carrier='usps',  # Default carrier, can be made configurable
                tracking_number=tracking_number
            )
            
            if tracking.get('tracking_status'):
                return {
                    'tracking_number': tracking_number,
                    'status': tracking.get('tracking_status', {}).get('status'),
                    'status_details': tracking.get('tracking_status', {}).get('status_details'),
                    'status_date': tracking.get('tracking_status', {}).get('status_date'),
                    'location': tracking.get('tracking_status', {}).get('location'),
                    'tracking_history': tracking.get('tracking_history', [])
                }
            else:
                logger.warning(f"No tracking information found for tracking number: {tracking_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error tracking shipment {tracking_number}: {str(e)}")
            return None
    
    def get_order_tracking_info(self, order: Order) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for an order.
        
        Args:
            order: Order instance to get tracking info for
            
        Returns:
            Dictionary containing tracking data or None if not available
        """
        if not order.tracking_number:
            return None
        
        return self.track_shipment(order.tracking_number)
    
    def validate_address(self, address_data: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Validate a shipping address using Goshippo.
        
        Args:
            address_data: Dictionary containing address fields
            
        Returns:
            Dictionary containing validation results or None if failed
        """
        try:
            address = goshippo.Address.create(**address_data)
            
            return {
                'is_valid': address.get('validation_results', {}).get('is_valid', False),
                'messages': address.get('validation_results', {}).get('messages', []),
                'normalized_address': {
                    'street1': address.get('street1'),
                    'city': address.get('city'),
                    'state': address.get('state'),
                    'zip': address.get('zip'),
                    'country': address.get('country')
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating address: {str(e)}")
            return None


# Convenience functions for common operations
def create_shipping_label_for_order(order: Order, rate_id: str) -> Optional[Dict[str, Any]]:
    """
    Create a shipping label for an order.
    
    Args:
        order: Order instance
        rate_id: Selected shipping rate ID
        
    Returns:
        Label data or None if failed
    """
    service = GoshippoShippingService()
    return service.create_shipping_label(order, rate_id)


def get_shipping_rates_for_order(order: Order) -> Optional[list]:
    """
    Get available shipping rates for an order.
    
    Args:
        order: Order instance
        
    Returns:
        List of shipping rates or None if failed
    """
    service = GoshippoShippingService()
    return service.get_shipping_rates(order)


def track_order_shipment(order: Order) -> Optional[Dict[str, Any]]:
    """
    Track an order's shipment.
    
    Args:
        order: Order instance
        
    Returns:
        Tracking data or None if not available
    """
    service = GoshippoShippingService()
    return service.get_order_tracking_info(order)