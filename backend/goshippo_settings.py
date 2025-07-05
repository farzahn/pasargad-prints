"""
Goshippo settings configuration for Pasargad Prints.
Add these settings to your Django settings.py file.

Goshippo SDK Documentation: https://github.com/goshippo/shippo-python-sdk
API Reference: https://docs.goshippo.com/docs/api
"""

# Goshippo API Configuration
GOSHIPPO_API_KEY = 'shippo_test_a273c78ecb97dae87d34dbec6c37cef303c80d15'  # Test API key, replace with your production key
GOSHIPPO_TEST_MODE = True  # Set to False for production

# Shipping origin address (your warehouse/store address)
SHIPPING_FROM_NAME = 'Pasargad Prints'
SHIPPING_FROM_ADDRESS = '123 Main Street'
SHIPPING_FROM_CITY = 'Your City'
SHIPPING_FROM_STATE = 'CA'
SHIPPING_FROM_ZIP = '12345'
SHIPPING_FROM_COUNTRY = 'US'
SHIPPING_FROM_PHONE = '+1-555-123-4567'
SHIPPING_FROM_EMAIL = 'shipping@pasargadprints.com'

# Default shipping preferences
DEFAULT_PARCEL_DIMENSIONS = {
    'length': 10,  # inches
    'width': 10,   # inches  
    'height': 5,   # inches
    'weight': 1,   # pounds
}

# Webhook configuration (optional)
GOSHIPPO_WEBHOOK_URL = 'https://yourdomain.com/api/orders/shipping/webhook/'
GOSHIPPO_WEBHOOK_SECRET = 'your_webhook_secret'