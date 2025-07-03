# Stripe Checkout Implementation Guide

This document describes the Stripe checkout implementation for Pasargad Prints.

## Overview

The checkout system uses Stripe Checkout Sessions for secure payment processing. It supports both authenticated and guest checkout flows.

## Backend Implementation

### API Endpoints

1. **Create Checkout Session** - `POST /api/payments/create-checkout-session/`
   - Creates a Stripe checkout session
   - Calculates shipping and tax
   - Returns checkout URL for redirect

2. **Verify Checkout Session** - `GET /api/payments/verify-checkout-session/`
   - Verifies payment status
   - Creates order if payment successful
   - Returns order details

3. **Stripe Webhook** - `POST /api/payments/stripe-webhook/`
   - Handles Stripe webhook events
   - Processes successful/failed payments
   - Updates order status

### Key Features

- **Order Creation**: Automatically creates orders after successful payment
- **Inventory Management**: Updates product stock after purchase
- **Payment Records**: Stores payment details for auditing
- **Webhook Security**: Verifies webhook signatures
- **Idempotency**: Prevents duplicate order creation

## Frontend Implementation

### Pages

1. **Checkout Page** (`/checkout`)
   - Displays order summary
   - Shows customer information
   - Initiates Stripe checkout

2. **Success Page** (`/checkout/success`)
   - Verifies payment completion
   - Shows order confirmation
   - Clears cart

3. **Cancel Page** (`/checkout/cancel`)
   - Handles cancelled payments
   - Preserves cart items
   - Provides support information

### Features

- **Guest Checkout**: Allows checkout without authentication
- **Session Persistence**: Maintains cart across sessions
- **Error Handling**: Graceful error messages
- **Loading States**: Visual feedback during processing

## Configuration

### Environment Variables

Backend (.env):
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Frontend (.env):
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Stripe Dashboard Setup

1. Add webhook endpoint: `https://yourdomain.com/api/payments/stripe-webhook/`
2. Subscribe to events:
   - `checkout.session.completed`
   - `payment_intent.payment_failed`
3. Copy webhook signing secret

## Testing

### Test Cards

Use these test cards in Stripe's test mode:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Authentication: `4000 0025 0000 3155`

### Local Testing

1. Use Stripe CLI for webhook testing:
   ```bash
   stripe listen --forward-to localhost:8000/api/payments/stripe-webhook/
   ```

2. Test checkout flow:
   - Add items to cart
   - Navigate to checkout
   - Complete payment
   - Verify order creation

## Security Considerations

1. **HTTPS Required**: Always use HTTPS in production
2. **CSRF Exempt**: Webhook endpoint bypasses CSRF for Stripe
3. **Signature Verification**: All webhooks are verified
4. **Session Security**: Cart sessions expire after 10 minutes
5. **PCI Compliance**: Card details never touch your server

## Troubleshooting

### Common Issues

1. **Webhook Failures**
   - Check webhook secret configuration
   - Verify endpoint URL
   - Review webhook logs in Stripe

2. **Order Not Created**
   - Check payment status in Stripe
   - Verify webhook processing
   - Review Django logs

3. **Cart Not Clearing**
   - Ensure success page loads properly
   - Check Redux state updates
   - Verify API responses

### Debug Steps

1. Enable Django debug logging
2. Check browser console for errors
3. Review Stripe dashboard events
4. Test with Stripe CLI

## Future Enhancements

1. **Subscription Support**: Add recurring payments
2. **Multiple Payment Methods**: Support PayPal, Apple Pay
3. **Saved Cards**: Allow customers to save payment methods
4. **Invoice Generation**: Automatic PDF invoices
5. **Email Notifications**: Order confirmation emails