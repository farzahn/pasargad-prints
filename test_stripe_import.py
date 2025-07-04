#!/usr/bin/env python3
"""Test script to reproduce Stripe import error"""

import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')

# Load .env file if exists
try:
    from decouple import config
    print("✓ Decouple imported successfully")
except ImportError:
    print("✗ Failed to import decouple")

# Initialize Django
django.setup()

print("\n=== Testing Stripe Module Import ===")

# Test 1: Basic stripe import
try:
    import stripe
    print(f"✓ Stripe module imported successfully (version: {stripe.__version__ if hasattr(stripe, '__version__') else 'unknown'})")
except Exception as e:
    print(f"✗ Failed to import stripe: {e}")
    sys.exit(1)

# Test 2: Check API key
from django.conf import settings
print(f"\n✓ STRIPE_SECRET_KEY configured: {'Yes' if settings.STRIPE_SECRET_KEY else 'No'}")
if settings.STRIPE_SECRET_KEY:
    print(f"  Key starts with: {settings.STRIPE_SECRET_KEY[:7]}...")

# Test 3: Try stripe_init.py import
print("\n=== Testing stripe_init.py ===")
try:
    from payments.stripe_init import stripe, CheckoutSession, StripeError, SignatureVerificationError, Webhook
    print("✓ All imports from stripe_init.py successful")
except Exception as e:
    print(f"✗ Failed to import from stripe_init.py: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Try creating a test checkout session
print("\n=== Testing CheckoutSession ===")
try:
    # This will fail without valid API key, but we're just testing import
    print(f"✓ CheckoutSession class available: {CheckoutSession}")
    print(f"✓ CheckoutSession.create method available: {hasattr(CheckoutSession, 'create')}")
except Exception as e:
    print(f"✗ Error accessing CheckoutSession: {e}")

# Test 5: Check for the specific error
print("\n=== Checking for '_object_classes' issue ===")
try:
    print(f"✓ stripe._object_classes exists: {hasattr(stripe, '_object_classes')}")
    if hasattr(stripe, '_object_classes'):
        print(f"  Type: {type(stripe._object_classes)}")
        print(f"  Has 'Secret' attribute: {hasattr(stripe._object_classes, 'Secret') if stripe._object_classes else 'N/A (None)'}")
except Exception as e:
    print(f"✗ Error checking _object_classes: {e}")

print("\n=== Import Test Complete ===")