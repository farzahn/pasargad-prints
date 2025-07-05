# Goshippo Integration Documentation

This document outlines the complete integration of Goshippo shipping API to replace ShipStation functionality in the Pasargad Prints application.

## Overview

The integration provides comprehensive shipping functionality including:
- Automated shipment creation and rate calculation
- Label purchasing and tracking
- Address validation
- Background task processing for shipping operations
- Real-time shipment tracking updates

## Architecture

### Components Implemented

1. **Order Model Updates** (`orders/models.py`)
   - Replaced `shipstation_order_id` with comprehensive Goshippo fields
   - Added carrier and service level tracking
   - Included tracking URLs and label URLs

2. **Background Tasks** (`orders/tasks.py`)
   - `create_goshippo_shipment`: Create shipments and get rates
   - `purchase_goshippo_label`: Purchase shipping labels
   - `track_goshippo_shipments`: Update order status from tracking
   - `sync_goshippo_rates`: Sync rates for processing orders
   - `cleanup_old_goshippo_shipments`: Clean up unused shipments
   - `send_shipping_rate_notifications`: Notify customers about shipping options
   - `validate_goshippo_addresses`: Validate shipping addresses

3. **Utility Functions** (`orders/utils.py`)
   - `get_goshippo_shipping_rates`: Get shipping rates for orders
   - `validate_goshippo_address`: Validate shipping addresses
   - `get_goshippo_tracking_info`: Get tracking information
   - `calculate_goshippo_shipping_cost`: Calculate shipping costs
   - `get_goshippo_label_url`: Get shipping label URLs

4. **Admin Interface Updates** (`orders/admin.py`)
   - Updated fieldsets to include Goshippo fields
   - Organized tracking and Goshippo fields separately

5. **API Serializers** (`orders/serializers.py`)
   - Updated to include all Goshippo fields
   - Maintains backward compatibility

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# Goshippo API Configuration
GOSHIPPO_API_KEY=your_goshippo_api_key_here

# Shipping Origin Address
GOSHIPPO_FROM_NAME=Pasargad Prints
GOSHIPPO_FROM_ADDRESS=123 Your Street
GOSHIPPO_FROM_CITY=Your City
GOSHIPPO_FROM_STATE=Your State
GOSHIPPO_FROM_ZIP=12345
GOSHIPPO_FROM_COUNTRY=US
GOSHIPPO_FROM_PHONE=+1234567890
GOSHIPPO_FROM_EMAIL=shipping@pasargadprints.com

# Shipping Options
GOSHIPPO_SIGNATURE_REQUIRED=False

# Default Package Dimensions (inches)
DEFAULT_PACKAGE_LENGTH=12
DEFAULT_PACKAGE_WIDTH=12
DEFAULT_PACKAGE_HEIGHT=6
```

### Celery Configuration

The following scheduled tasks have been configured:

- **Track Shipments**: Every hour - Updates order status from tracking
- **Sync Rates**: Every 30 minutes - Gets rates for processing orders
- **Cleanup Old Shipments**: Daily - Removes unused shipment records
- **Rate Notifications**: Every 2 hours - Notifies customers about shipping options
- **Address Validation**: Every hour - Validates new order addresses

### Task Queues

Goshippo tasks use dedicated queues for better performance:
- High-priority shipping tasks: `shipping` queue
- Regular order tasks: `orders` queue

## Database Migration

Run the migration to update the Order model:

```bash
python manage.py migrate orders 0005_goshippo_integration
```

This migration:
- Removes the old `shipstation_order_id` field
- Adds new Goshippo-specific fields
- Adds carrier and service level tracking

## API Usage

### Creating a Shipment

```python
from orders.tasks import create_goshippo_shipment

# Create shipment for an order
result = create_goshippo_shipment.delay(order_id)
```

### Purchasing a Label

```python
from orders.tasks import purchase_goshippo_label

# Purchase label with specific rate
result = purchase_goshippo_label.delay(order_id, rate_id="rate_xxx")

# Purchase label with cheapest rate
result = purchase_goshippo_label.delay(order_id)
```

### Getting Shipping Rates

```python
from orders.utils import get_goshippo_shipping_rates

rates = get_goshippo_shipping_rates(order)
# Returns list of rates sorted by price
```

### Validating Addresses

```python
from orders.utils import validate_goshippo_address

validation = validate_goshippo_address(order)
if not validation['is_valid']:
    print(f"Address issues: {validation['messages']}")
```

## Order Model Fields

### New Goshippo Fields

- `goshippo_order_id`: Goshippo order identifier
- `goshippo_transaction_id`: Transaction ID for purchased labels
- `goshippo_object_id`: Shipment object ID
- `goshippo_rate_id`: Selected shipping rate ID
- `goshippo_tracking_url`: Carrier tracking URL
- `goshippo_label_url`: Shipping label PDF URL
- `carrier`: Shipping carrier (USPS, FedEx, UPS, etc.)
- `service_level`: Service level (Priority, Ground, etc.)

### Existing Fields Enhanced

- `tracking_number`: Now populated from Goshippo
- `shipping_cost`: Calculated from selected rate
- `estimated_delivery`: Based on carrier estimates

## Error Handling

All Goshippo tasks include comprehensive error handling:
- API failures are logged and tasks return error status
- Network timeouts are handled gracefully
- Invalid data is validated before API calls
- Retry logic for transient failures

## Monitoring

### Logging

All shipping operations are logged with appropriate levels:
- INFO: Successful operations
- WARNING: Address validation issues
- ERROR: API failures and exceptions

### Metrics

Track the following metrics in your monitoring system:
- Shipment creation success rate
- Label purchase success rate
- Tracking update frequency
- Address validation failure rate

## Testing

### Manual Testing

1. Create a test order with valid shipping address
2. Trigger shipment creation: `create_goshippo_shipment.delay(order_id)`
3. Verify rates are retrieved and stored
4. Purchase label: `purchase_goshippo_label.delay(order_id)`
5. Verify tracking number and label URL are stored
6. Test tracking updates: `track_goshippo_shipments.delay()`

### Unit Tests

Add tests for:
- Rate calculation accuracy
- Address validation logic
- Label purchase workflow
- Tracking status updates
- Error handling scenarios

## Deployment

### Prerequisites

1. Goshippo account and API key
2. Configured shipping origin address
3. Celery worker and beat scheduler running
4. Redis/RabbitMQ message broker

### Deployment Steps

1. Update environment variables
2. Run database migrations
3. Restart Django application
4. Restart Celery workers and beat scheduler
5. Monitor logs for successful integration

### Rollback Plan

If issues occur:
1. Stop new shipment creation tasks
2. Revert to manual shipping processes
3. Fix configuration issues
4. Resume automated shipping

## Support

### Common Issues

1. **Invalid API Key**: Verify GOSHIPPO_API_KEY in environment
2. **Address Validation Failures**: Check shipping addresses format
3. **Rate Calculation Errors**: Verify package dimensions and weight
4. **Label Purchase Failures**: Check account balance and shipping rates

### Debugging

Enable debug logging for Goshippo operations:

```python
import logging
logging.getLogger('orders.tasks').setLevel(logging.DEBUG)
logging.getLogger('orders.utils').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Multi-Package Shipments**: Support for orders with multiple packages
2. **International Shipping**: Enhanced customs and international rates
3. **Return Labels**: Automated return label generation
4. **Rate Shopping**: Real-time rate comparison across carriers
5. **Delivery Confirmation**: Enhanced delivery notifications
6. **Analytics Dashboard**: Shipping cost and performance analytics

## References

- [Goshippo API Documentation](https://goshippo.com/docs/)
- [Goshippo Python SDK](https://github.com/goshippo/shippo-python-sdk)
- [Django Celery Documentation](https://docs.celeryproject.org/en/stable/django/)