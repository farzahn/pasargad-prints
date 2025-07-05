"""
Goshippo shipping service to replace ShipStation integration.
Handles shipping rates, labels, and tracking through Goshippo API.

Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
import logging
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
import shippo
from shippo import security

logger = logging.getLogger(__name__)


class GoshippoShippingService:
    """
    Service class for handling Goshippo shipping operations.
    Provides methods for getting rates, creating labels, and tracking shipments.
    """
    
    def __init__(self):
        """Initialize Goshippo client with API key."""
        self.api_key = getattr(settings, 'GOSHIPPO_API_KEY', 'shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15')
        
        self.client = shippo.Shippo(
            security=security.Security(
                api_key_header=self.api_key
            )
        )
        
        # Cache settings
        self.cache_prefix = 'goshippo_service'
        self.cache_timeout = 300  # 5 minutes
        
    def get_shipping_rates(self, from_address, to_address, parcel_details, carrier_accounts=None):
        """
        Get shipping rates for a shipment.
        
        Args:
            from_address (dict): Origin address details
            to_address (dict): Destination address details
            parcel_details (dict): Package dimensions and weight
            carrier_accounts (list): Optional list of carrier account IDs
            
        Returns:
            dict: Shipping rates and options
        """
        try:
            # Create cache key
            cache_key = self._generate_rates_cache_key(from_address, to_address, parcel_details)
            cached_rates = cache.get(cache_key)
            
            if cached_rates:
                logger.info(f"Cache hit for shipping rates: {cache_key}")
                return cached_rates
            
            # Create addresses
            from_addr = addressfrom.AddressFrom(
                name=from_address.get('name', 'Pasargad Prints'),
                company=from_address.get('company', 'Pasargad Prints'),
                street1=from_address.get('street1', ''),
                street2=from_address.get('street2', ''),
                city=from_address.get('city', ''),
                state=from_address.get('state', ''),
                zip=from_address.get('zip', ''),
                country=from_address.get('country', 'US'),
                phone=from_address.get('phone', ''),
                email=from_address.get('email', ''),
            )
            
            to_addr = addressto.AddressTo(
                name=to_address.get('name', ''),
                company=to_address.get('company', ''),
                street1=to_address.get('street1', ''),
                street2=to_address.get('street2', ''),
                city=to_address.get('city', ''),
                state=to_address.get('state', ''),
                zip=to_address.get('zip', ''),
                country=to_address.get('country', 'US'),
                phone=to_address.get('phone', ''),
                email=to_address.get('email', ''),
            )
            
            # Create parcel
            parcel_obj = parcel.Parcel(
                length=str(parcel_details.get('length', 12)),
                width=str(parcel_details.get('width', 9)),
                height=str(parcel_details.get('height', 6)),
                distance_unit=parcel_details.get('distance_unit', 'in'),
                weight=str(parcel_details.get('weight', 1)),
                mass_unit=parcel_details.get('mass_unit', 'lb'),
            )
            
            # Create shipment
            shipment_obj = shipment.Shipment(
                address_from=from_addr,
                address_to=to_addr,
                parcels=[parcel_obj],
                async_=False,
                carrier_accounts=carrier_accounts or [],
            )
            
            # Get rates
            response = self.client.shipments.create(shipment_obj)
            
            if response.status_code != 201:
                raise SDKError(f"Failed to create shipment: {response.status_code}")
            
            shipment_data = response.shipment
            
            # Process rates
            rates_data = []
            for rate_obj in shipment_data.rates:
                rate_data = {
                    'rate_id': rate_obj.object_id,
                    'carrier': rate_obj.provider,
                    'service': rate_obj.servicelevel.name,
                    'service_code': rate_obj.servicelevel.token,
                    'amount': float(rate_obj.amount),
                    'currency': rate_obj.currency,
                    'estimated_days': rate_obj.estimated_days,
                    'duration_terms': rate_obj.duration_terms,
                    'carrier_account': rate_obj.carrier_account,
                    'test': rate_obj.test,
                }
                rates_data.append(rate_data)
            
            result = {
                'shipment_id': shipment_data.object_id,
                'rates': rates_data,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            # Cache the results
            cache.set(cache_key, result, timeout=self.cache_timeout)
            
            logger.info(f"Retrieved {len(rates_data)} shipping rates")
            return result
            
        except SDKError as e:
            logger.error(f"Goshippo SDK error getting rates: {e}")
            return {'error': str(e), 'status': 'error'}
        except Exception as e:
            logger.error(f"Unexpected error getting rates: {e}")
            return {'error': 'Failed to get shipping rates', 'status': 'error'}
    
    def create_shipping_label(self, rate_id, label_format='PDF'):
        """
        Create a shipping label from a rate.
        
        Args:
            rate_id (str): Rate ID from previous rates request
            label_format (str): Label format (PDF, PNG, etc.)
            
        Returns:
            dict: Label information and tracking details
        """
        try:
            # Create transaction (purchase label)
            transaction_obj = transaction.Transaction(
                rate=rate_id,
                label_file_type=label_format.upper(),
                async_=False,
            )
            
            response = self.client.transactions.create(transaction_obj)
            
            if response.status_code != 201:
                raise SDKError(f"Failed to create transaction: {response.status_code}")
            
            transaction_data = response.transaction
            
            result = {
                'transaction_id': transaction_data.object_id,
                'tracking_number': transaction_data.tracking_number,
                'tracking_url': transaction_data.tracking_url_provider,
                'label_url': transaction_data.label_url,
                'commercial_invoice_url': transaction_data.commercial_invoice_url,
                'status': transaction_data.status,
                'carrier': transaction_data.rate.provider,
                'service': transaction_data.rate.servicelevel.name,
                'amount': float(transaction_data.rate.amount),
                'currency': transaction_data.rate.currency,
                'test': transaction_data.test,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Created shipping label: {transaction_data.tracking_number}")
            return result
            
        except SDKError as e:
            logger.error(f"Goshippo SDK error creating label: {e}")
            return {'error': str(e), 'status': 'error'}
        except Exception as e:
            logger.error(f"Unexpected error creating label: {e}")
            return {'error': 'Failed to create shipping label', 'status': 'error'}
    
    def track_shipment(self, tracking_number, carrier=None):
        """
        Track a shipment by tracking number.
        
        Args:
            tracking_number (str): Tracking number
            carrier (str): Optional carrier code
            
        Returns:
            dict: Tracking information
        """
        try:
            # Get tracking info
            response = self.client.tracks.get(tracking_number, carrier)
            
            if response.status_code != 200:
                raise SDKError(f"Failed to get tracking: {response.status_code}")
            
            tracking_data = response.track
            
            # Process tracking history
            tracking_history = []
            for status in tracking_data.tracking_history:
                history_item = {
                    'status': status.status,
                    'status_date': status.status_date,
                    'status_details': status.status_details,
                    'location': {
                        'city': status.location.city if status.location else None,
                        'state': status.location.state if status.location else None,
                        'zip': status.location.zip if status.location else None,
                        'country': status.location.country if status.location else None,
                    } if status.location else None,
                }
                tracking_history.append(history_item)
            
            result = {
                'tracking_number': tracking_data.tracking_number,
                'carrier': tracking_data.carrier,
                'tracking_status': tracking_data.tracking_status,
                'eta': tracking_data.eta,
                'original_eta': tracking_data.original_eta,
                'tracking_history': tracking_history,
                'address_from': {
                    'city': tracking_data.address_from.city if tracking_data.address_from else None,
                    'state': tracking_data.address_from.state if tracking_data.address_from else None,
                    'zip': tracking_data.address_from.zip if tracking_data.address_from else None,
                    'country': tracking_data.address_from.country if tracking_data.address_from else None,
                } if tracking_data.address_from else None,
                'address_to': {
                    'city': tracking_data.address_to.city if tracking_data.address_to else None,
                    'state': tracking_data.address_to.state if tracking_data.address_to else None,
                    'zip': tracking_data.address_to.zip if tracking_data.address_to else None,
                    'country': tracking_data.address_to.country if tracking_data.address_to else None,
                } if tracking_data.address_to else None,
                'test': tracking_data.test,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Retrieved tracking info for: {tracking_number}")
            return result
            
        except SDKError as e:
            logger.error(f"Goshippo SDK error tracking shipment: {e}")
            return {'error': str(e), 'status': 'error'}
        except Exception as e:
            logger.error(f"Unexpected error tracking shipment: {e}")
            return {'error': 'Failed to track shipment', 'status': 'error'}
    
    def validate_address(self, address_data):
        """
        Validate an address using Goshippo.
        
        Args:
            address_data (dict): Address details to validate
            
        Returns:
            dict: Validation results
        """
        try:
            # Create address for validation
            addr = addressfrom.AddressFrom(
                name=address_data.get('name', ''),
                company=address_data.get('company', ''),
                street1=address_data.get('street1', ''),
                street2=address_data.get('street2', ''),
                city=address_data.get('city', ''),
                state=address_data.get('state', ''),
                zip=address_data.get('zip', ''),
                country=address_data.get('country', 'US'),
                phone=address_data.get('phone', ''),
                email=address_data.get('email', ''),
                validate=True,
            )
            
            response = self.client.addresses.create(addr)
            
            if response.status_code != 201:
                raise SDKError(f"Failed to validate address: {response.status_code}")
            
            address_obj = response.address
            
            result = {
                'is_valid': address_obj.validation_results.is_valid,
                'messages': address_obj.validation_results.messages,
                'address': {
                    'name': address_obj.name,
                    'company': address_obj.company,
                    'street1': address_obj.street1,
                    'street2': address_obj.street2,
                    'city': address_obj.city,
                    'state': address_obj.state,
                    'zip': address_obj.zip,
                    'country': address_obj.country,
                    'phone': address_obj.phone,
                    'email': address_obj.email,
                },
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Validated address: {address_obj.validation_results.is_valid}")
            return result
            
        except SDKError as e:
            logger.error(f"Goshippo SDK error validating address: {e}")
            return {'error': str(e), 'status': 'error'}
        except Exception as e:
            logger.error(f"Unexpected error validating address: {e}")
            return {'error': 'Failed to validate address', 'status': 'error'}
    
    def _generate_rates_cache_key(self, from_address, to_address, parcel_details):
        """Generate cache key for rates request."""
        import hashlib
        import json
        
        cache_data = {
            'from': from_address,
            'to': to_address,
            'parcel': parcel_details,
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"{self.cache_prefix}_rates_{cache_hash}"


# Global service instance
goshippo_service = GoshippoShippingService()