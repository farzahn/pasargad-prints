"""
Stripe initialization module to ensure proper loading
"""
import stripe
from django.conf import settings

# Initialize stripe with API key
stripe.api_key = settings.STRIPE_SECRET_KEY

# Force load all required modules
import stripe.checkout
import stripe.error

# Export what we need
from stripe.checkout import Session as CheckoutSession
from stripe.error import StripeError, SignatureVerificationError

# Webhook is accessed differently
Webhook = stripe.Webhook

__all__ = ['stripe', 'CheckoutSession', 'StripeError', 'SignatureVerificationError', 'Webhook']