# Stripe Webhook Setup Guide

To enable webhook support for your Stripe integration, follow these steps:

## 1. Configure Webhook in Stripe Dashboard

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter your webhook URL: `https://yourdomain.com/api/payments/stripe-webhook/`
4. Select the following events to listen for:
   - `checkout.session.completed`
   - `payment_intent.payment_failed`
5. Copy the webhook signing secret

## 2. Update Environment Variables

Add the webhook signing secret to your environment:

```bash
# Backend .env file
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## 3. Test Webhook Locally

For local development, you can use Stripe CLI:

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8000/api/payments/stripe-webhook/

# In another terminal, trigger test events
stripe trigger checkout.session.completed
```

## 4. Webhook Security

The webhook handler includes:
- Signature verification to ensure requests come from Stripe
- Idempotency handling to prevent duplicate processing
- Error logging for debugging

## Important Notes

- The webhook endpoint is exempt from CSRF protection (`@csrf_exempt`)
- All webhook events are stored in the database for auditing
- Failed webhook processing will return 500 to trigger Stripe retry
- Successful processing returns 200 to acknowledge receipt