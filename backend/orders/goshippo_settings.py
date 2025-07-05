"""
Goshippo API settings and configuration.
Add these settings to your Django settings.py file.

Goshippo SDK Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""
import os
from decouple import config

# Example settings to add to your Django settings.py file

# Goshippo API Configuration
GOSHIPPO_API_KEY = config('GOSHIPPO_API_KEY', default='')
GOSHIPPO_TEST_MODE = config('GOSHIPPO_TEST_MODE', default=True, cast=bool)

# Business Address Information (required for shipping)
BUSINESS_NAME = config('BUSINESS_NAME', default='Pasargad Prints')
BUSINESS_ADDRESS = config('BUSINESS_ADDRESS', default='123 Main St')
BUSINESS_CITY = config('BUSINESS_CITY', default='New York')
BUSINESS_STATE = config('BUSINESS_STATE', default='NY')
BUSINESS_ZIP = config('BUSINESS_ZIP', default='10001')
BUSINESS_COUNTRY = config('BUSINESS_COUNTRY', default='US')
BUSINESS_PHONE = config('BUSINESS_PHONE', default='')
BUSINESS_EMAIL = config('BUSINESS_EMAIL', default='shipping@pasargadprints.com')

# Default Package Dimensions (in inches)
DEFAULT_PACKAGE_LENGTH = config('DEFAULT_PACKAGE_LENGTH', default=10, cast=int)
DEFAULT_PACKAGE_WIDTH = config('DEFAULT_PACKAGE_WIDTH', default=10, cast=int)
DEFAULT_PACKAGE_HEIGHT = config('DEFAULT_PACKAGE_HEIGHT', default=10, cast=int)

# Supported Carriers (can be customized based on your needs)
SUPPORTED_CARRIERS = [
    'usps',
    'ups',
    'fedex',
    'dhl_express',
    'canada_post',
]

# Default Carrier for Tracking (if not specified)
DEFAULT_TRACKING_CARRIER = config('DEFAULT_TRACKING_CARRIER', default='usps')

# Shipping Options
ENABLE_INTERNATIONAL_SHIPPING = config('ENABLE_INTERNATIONAL_SHIPPING', default=False, cast=bool)
MAX_PACKAGE_WEIGHT = config('MAX_PACKAGE_WEIGHT', default=50, cast=int)  # in pounds

# Add these to your .env file:
"""
# Goshippo Configuration
GOSHIPPO_API_KEY=shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15
GOSHIPPO_TEST_MODE=True

# Business Information
BUSINESS_NAME=Pasargad Prints
BUSINESS_ADDRESS=123 Main Street
BUSINESS_CITY=New York
BUSINESS_STATE=NY
BUSINESS_ZIP=10001
BUSINESS_COUNTRY=US
BUSINESS_PHONE=+1-555-123-4567
BUSINESS_EMAIL=shipping@pasargadprints.com

# Package Defaults
DEFAULT_PACKAGE_LENGTH=10
DEFAULT_PACKAGE_WIDTH=10
DEFAULT_PACKAGE_HEIGHT=10
DEFAULT_TRACKING_CARRIER=usps
ENABLE_INTERNATIONAL_SHIPPING=False
MAX_PACKAGE_WEIGHT=50
"""