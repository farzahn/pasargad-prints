# Goshippo Integration Guide

This document outlines the Goshippo integration for handling shipping and tracking in the Pasargad Prints application.

## Overview

The integration replaces the previous ShipStation integration with Goshippo's shipping API, providing:

- Automated shipment creation
- Real-time tracking updates via webhooks
- Support for multiple carriers (USPS, FedEx, UPS, DHL)
- Rate shopping for best shipping prices
- Label generation and management

## Components

### 1. GoshippoService (`orders/goshippo_service.py`)

Main service class for interacting with Goshippo API:

- `create_shipment()` - Creates shipments for orders
- `create_transaction()` - Purchases shipping labels
- `get_tracking_info()` - Retrieves tracking information
- `verify_webhook_signature()` - Validates webhook signatures
- `parse_tracking_status()` - Maps Goshippo statuses to order statuses

### 2. Webhook Handler (`orders/views.py`)

Handles incoming webhooks from Goshippo:

- **URL**: `/api/orders/goshippo-webhook/`
- **Events**: 
  - `track_updated` - Updates order status when tracking changes
  - `shipment_created` - Links shipment ID to order
  - `transaction_created` - Updates tracking number and transaction ID

### 3. Database Models

Updated Order model fields:

- `shippo_shipment_id` - Goshippo shipment object ID
- `shippo_transaction_id` - Transaction ID for label purchase
- `carrier` - Shipping carrier (usps, fedex, ups)
- `service_level` - Service level (Priority, Ground, etc.)

TrackingStatus model for detailed tracking history:

- Stores individual tracking events
- Location information
- Status timestamps
- Goshippo object metadata

### 4. Admin Interface

Updated Django admin to show Goshippo fields:

- Shipment and transaction IDs
- Carrier and service level information
- Tracking status inline display

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Goshippo API Configuration
GOSHIPPO_API_KEY=shippo_test_your_api_key_here
GOSHIPPO_WEBHOOK_SECRET=your_webhook_secret_here

# Shipping Origin Address
SHIPPING_ORIGIN_NAME=Pasargad Prints
SHIPPING_ORIGIN_COMPANY=Pasargad Prints
SHIPPING_ORIGIN_STREET1=123 Your Street
SHIPPING_ORIGIN_CITY=Your City
SHIPPING_ORIGIN_STATE=CA
SHIPPING_ORIGIN_ZIP=90210
SHIPPING_ORIGIN_COUNTRY=US
SHIPPING_ORIGIN_PHONE=+1 555 123 4567
SHIPPING_ORIGIN_EMAIL=shipping@yourstore.com
```

### Webhook Setup

1. Log into your Goshippo dashboard
2. Go to Settings > Webhooks
3. Add webhook URL: `https://yourdomain.com/api/orders/goshippo-webhook/`
4. Select events: `track_updated`, `shipment_created`, `transaction_created`
5. Copy the webhook secret to your environment variables

## API Endpoints

### Create Shipment (Admin Only)

```http
POST /api/orders/{order_id}/create-shipment/
Authorization: Bearer {admin_token}
```

Creates a Goshippo shipment for an order and returns available rates.

**Response:**
```json
{
    "shipment_id": "shipment_abc123",
    "status": "SUCCESS",
    "rates_count": 5,
    "cheapest_rate": {
        "provider": "USPS",
        "amount": "5.95",
        "currency": "USD",
        "estimated_days": 3
    }
}
```

### Webhook Endpoint

```http
POST /api/orders/goshippo-webhook/
Content-Type: application/json
X-Goshippo-Signature: {signature}
```

Receives tracking updates and shipment events from Goshippo.

## Migration from ShipStation

The migration replaces:

- `shipstation_order_id` → `shippo_shipment_id` + `shippo_transaction_id`
- ShipStation webhook → Goshippo webhook
- Manual order status updates → Automated tracking updates

### Migration Steps

1. Run database migrations:
   ```bash
   python manage.py migrate orders
   ```

2. Update environment variables with Goshippo credentials

3. Configure Goshippo webhook in dashboard

4. Test with a sample order

## Usage Workflow

### For New Orders

1. Order is created through checkout process
2. Admin creates shipment via API or admin interface
3. Goshippo returns shipping rates
4. Admin selects rate and purchases label
5. Tracking number is automatically assigned
6. Customer receives shipping notification email

### Automatic Tracking Updates

1. Carrier scans package (pickup, transit, delivery)
2. Goshippo receives update from carrier
3. Goshippo sends webhook to your endpoint
4. System updates order status automatically
5. Customer receives status update email

## Testing

### Test Mode

Goshippo provides test API keys for development:

- Use test API key in development environment
- Test shipments don't generate real labels
- Tracking updates can be simulated

### Webhook Testing

Use tools like ngrok to test webhooks locally:

```bash
ngrok http 8000
# Update webhook URL in Goshippo dashboard to ngrok URL
```

## Error Handling

The integration includes comprehensive error handling:

- API failures are logged with details
- Webhook signature verification prevents spoofing
- Graceful degradation when services are unavailable
- Retry logic for transient failures

## Monitoring

Key metrics to monitor:

- Webhook delivery success rate
- API response times
- Failed shipment creations
- Tracking update delays

## Support

For issues with the Goshippo integration:

1. Check logs for error details
2. Verify API credentials and webhook configuration
3. Test with Goshippo's API documentation
4. Contact Goshippo support for API-specific issues