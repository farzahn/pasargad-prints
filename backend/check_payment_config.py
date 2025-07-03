import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')
django.setup()

from django.conf import settings

print("💳 Payment Configuration Check:\n")

print("Stripe Configuration:")
print(f"Publishable Key: {settings.STRIPE_PUBLISHABLE_KEY[:20]}...")
print(f"Secret Key: {'✓ Set' if settings.STRIPE_SECRET_KEY else '✗ Not set'}")
print(f"Webhook Secret: {'✓ Set' if settings.STRIPE_WEBHOOK_SECRET else '✗ Not set (OK for testing)'}")

print("\n📧 Email Configuration:")
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"Email User: {settings.EMAIL_HOST_USER}")

print("\n🛒 Test Checkout Information:")
print("Use these Stripe test card numbers:")
print("• Success: 4242 4242 4242 4242")
print("• Decline: 4000 0000 0000 0002")
print("• Requires Auth: 4000 0025 0000 3155")
print("\nExpiry: Any future date (e.g., 12/34)")
print("CVC: Any 3 digits (e.g., 123)")
print("ZIP: Any 5 digits (e.g., 12345)")