"""
Stripe initialization module to ensure proper loading
"""
import stripe
from django.conf import settings

# Initialize stripe with API key and version
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = '2023-10-16'  # Lock API version for consistency

# Set app info for debugging
stripe.set_app_info(
    'pasargad-prints',
    version='1.0.0',
    url='https://pasargadprints.com'
)

# Export stripe module
__all__ = ['stripe']