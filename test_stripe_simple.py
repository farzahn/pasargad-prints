#!/usr/bin/env python3
"""Simple test to check Stripe import issue"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=== Testing Stripe Module Import ===")

# Test 1: Basic stripe import
try:
    import stripe
    print(f"✓ Stripe module imported successfully")
    print(f"  Version: {getattr(stripe, '__version__', 'unknown')}")
    print(f"  Location: {stripe.__file__}")
except Exception as e:
    print(f"✗ Failed to import stripe: {e}")
    sys.exit(1)

# Test 2: Check _object_classes
print("\n=== Checking _object_classes ===")
print(f"✓ stripe._object_classes exists: {hasattr(stripe, '_object_classes')}")
if hasattr(stripe, '_object_classes'):
    obj_classes = stripe._object_classes
    print(f"  Type: {type(obj_classes)}")
    print(f"  Is None: {obj_classes is None}")
    if obj_classes is not None:
        print(f"  Has 'Secret' attribute: {hasattr(obj_classes, 'Secret')}")

# Test 3: Check checkout module
print("\n=== Testing checkout module ===")
try:
    import stripe.checkout
    print("✓ stripe.checkout imported successfully")
    print(f"  Has Session: {hasattr(stripe.checkout, 'Session')}")
except Exception as e:
    print(f"✗ Failed to import stripe.checkout: {e}")

# Test 4: Direct Session import
print("\n=== Testing Session import ===")
try:
    from stripe.checkout import Session
    print("✓ Session imported successfully")
    print(f"  Session.create exists: {hasattr(Session, 'create')}")
except Exception as e:
    print(f"✗ Failed to import Session: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Reproduce the specific error path
print("\n=== Testing error reproduction ===")
try:
    # Set a dummy API key
    stripe.api_key = "sk_test_dummy"
    
    # Try to access Session.create
    print(f"✓ Can access Session.create: {Session.create}")
except AttributeError as e:
    print(f"✗ AttributeError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ Other error: {type(e).__name__}: {e}")

print("\n=== Test Complete ===")