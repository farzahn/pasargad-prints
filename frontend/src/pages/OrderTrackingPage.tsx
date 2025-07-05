import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

interface OrderItem {
  product_name: string;
  quantity: number;
}

interface OrderTrackingData {
  order_number: string;
  status: string;
  status_display: string;
  tracking_number?: string;
  estimated_delivery?: string;
  created_at: string;
  shipped_at?: string;
  delivered_at?: string;
  items: OrderItem[];
  goshippo_tracking?: {
    tracking_status?: string;
    eta?: string;
    tracking_history?: Array<{
      status: string;
      status_details: string;
      status_date: string;
      location: string;
    }>;
  };
}

const OrderTrackingPage = () => {
  const [searchParams] = useSearchParams();
  const [order, setOrder] = useState<OrderTrackingData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trackingMethod, setTrackingMethod] = useState<'tracking' | 'guest'>('tracking');
  
  // Form fields
  const [trackingNumber, setTrackingNumber] = useState(
    searchParams.get('tracking_number') || ''
  );
  const [orderNumber, setOrderNumber] = useState(
    searchParams.get('order_number') || searchParams.get('order') || ''
  );
  const [email, setEmail] = useState(
    searchParams.get('email') || ''
  );

  // Auto-track if params are provided
  useEffect(() => {
    const hasOrderNumber = searchParams.get('order_number') || searchParams.get('order');
    if (hasOrderNumber && searchParams.get('email')) {
      setTrackingMethod('guest');
      handleGuestTrack();
    } else if (searchParams.get('tracking_number')) {
      handleTrackOrder();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleTrackOrder = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!trackingNumber) {
      setError('Please enter a tracking number.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOrder(null);

    try {
      const response = await api.get(`/api/orders/track/${trackingNumber}/`);
      setOrder(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Order not found.');
    }
    setIsLoading(false);
  };

  const handleGuestTrack = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!orderNumber || !email) {
      setError('Please enter both order number and email.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setOrder(null);

    try {
      const response = await api.post('/api/orders/track/guest/', {
        order_number: orderNumber,
        email: email,
      });
      setOrder(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Order not found. Please check your order number and email.');
    }
    setIsLoading(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'processing':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'shipped':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
          </svg>
        );
      case 'delivered':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      case 'shipped':
        return 'text-purple-600 bg-purple-100';
      case 'delivered':
        return 'text-green-600 bg-green-100';
      case 'cancelled':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold">Track Your Order</h1>
        <p className="text-gray-600 mt-2">
          Track your order using your tracking number or order details.
        </p>
      </div>

      {/* Tracking Method Tabs */}
      <div className="flex justify-center mb-8">
        <div className="bg-gray-100 p-1 rounded-lg inline-flex">
          <button
            onClick={() => setTrackingMethod('tracking')}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              trackingMethod === 'tracking'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Track by Number
          </button>
          <button
            onClick={() => setTrackingMethod('guest')}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              trackingMethod === 'guest'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Guest Order
          </button>
        </div>
      </div>

      {/* Tracking Forms */}
      {trackingMethod === 'tracking' ? (
        <form onSubmit={handleTrackOrder} className="max-w-lg mx-auto mb-12">
          <div className="space-y-4">
            <div>
              <label htmlFor="tracking" className="block text-sm font-medium text-gray-700 mb-1">
                Tracking Number
              </label>
              <div className="flex gap-4">
                <input
                  id="tracking"
                  type="text"
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  placeholder="Enter tracking number"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-primary-600 text-white px-6 py-3 rounded-md font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Tracking...' : 'Track'}
                </button>
              </div>
            </div>
          </div>
        </form>
      ) : (
        <form onSubmit={handleGuestTrack} className="max-w-lg mx-auto mb-12">
          <div className="space-y-4">
            <div>
              <label htmlFor="orderNumber" className="block text-sm font-medium text-gray-700 mb-1">
                Order Number
              </label>
              <input
                id="orderNumber"
                type="text"
                value={orderNumber}
                onChange={(e) => setOrderNumber(e.target.value)}
                placeholder="Enter order number (e.g., ABC123)"
                className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email used for order"
                className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-600 text-white px-6 py-3 rounded-md font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Tracking...' : 'Track Order'}
            </button>
          </div>
        </form>
      )}

      {error && (
        <div className="max-w-lg mx-auto mb-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {isLoading && <LoadingSpinner />}

      {order && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Order Header */}
          <div className="bg-gray-50 px-6 py-4 border-b">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-semibold">Order #{order.order_number}</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Placed on {formatDate(order.created_at)}
                </p>
              </div>
              <div className={`px-4 py-2 rounded-full flex items-center gap-2 ${getStatusColor(order.status)}`}>
                {getStatusIcon(order.status)}
                <span className="font-medium">{order.status_display}</span>
              </div>
            </div>
          </div>

          {/* Order Progress */}
          <div className="px-6 py-6 border-b">
            <h3 className="text-lg font-semibold mb-4">Order Progress</h3>
            <div className="relative">
              <div className="absolute top-5 left-5 right-5 h-0.5 bg-gray-200"></div>
              <div className="relative flex justify-between">
                {['pending', 'processing', 'shipped', 'delivered'].map((step, index) => {
                  const stepStatuses = ['pending', 'processing', 'shipped', 'delivered'];
                  const currentIndex = stepStatuses.indexOf(order.status);
                  const stepIndex = stepStatuses.indexOf(step);
                  const isCompleted = stepIndex <= currentIndex;
                  const isCurrent = stepIndex === currentIndex;

                  return (
                    <div key={step} className="flex flex-col items-center">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center z-10 ${
                          isCompleted
                            ? isCurrent
                              ? 'bg-primary-600 text-white'
                              : 'bg-green-600 text-white'
                            : 'bg-gray-200 text-gray-400'
                        }`}
                      >
                        {isCompleted && !isCurrent ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <span className="text-sm font-medium">{index + 1}</span>
                        )}
                      </div>
                      <span className={`mt-2 text-xs font-medium ${isCompleted ? 'text-gray-900' : 'text-gray-400'}`}>
                        {step.charAt(0).toUpperCase() + step.slice(1)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Order Details */}
          <div className="px-6 py-6 border-b">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {order.tracking_number && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Tracking Number</p>
                  <p className="mt-1 text-lg font-medium text-gray-900">{order.tracking_number}</p>
                </div>
              )}
              {order.estimated_delivery && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Estimated Delivery</p>
                  <p className="mt-1 text-lg font-medium text-gray-900">{order.estimated_delivery}</p>
                </div>
              )}
              {order.shipped_at && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Shipped On</p>
                  <p className="mt-1 text-lg font-medium text-gray-900">{formatDate(order.shipped_at)}</p>
                </div>
              )}
              {order.delivered_at && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Delivered On</p>
                  <p className="mt-1 text-lg font-medium text-gray-900">{formatDate(order.delivered_at)}</p>
                </div>
              )}
            </div>
          </div>

          {/* Order Items */}
          <div className="px-6 py-6 border-b">
            <h3 className="text-lg font-semibold mb-4">Order Items</h3>
            <ul className="space-y-4">
              {order.items.map((item, index) => (
                <li key={index} className="flex justify-between items-center py-3 border-b last:border-0">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{item.product_name}</p>
                    <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Goshippo Tracking History */}
          {order.goshippo_tracking && order.goshippo_tracking.tracking_history && order.goshippo_tracking.tracking_history.length > 0 && (
            <div className="px-6 py-6 border-b">
              <h3 className="text-lg font-semibold mb-4">Detailed Tracking History</h3>
              <div className="space-y-4">
                {order.goshippo_tracking.tracking_history.map((event, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-3 h-3 bg-blue-500 rounded-full mt-2"></div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{event.status}</p>
                          <p className="text-sm text-gray-600">{event.status_details}</p>
                          {event.location && (
                            <p className="text-xs text-gray-500 mt-1">{event.location}</p>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 whitespace-nowrap ml-4">
                          {new Date(event.status_date).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Enhanced Tracking Info */}
          {order.goshippo_tracking && (
            <div className="px-6 py-6 border-b">
              <h3 className="text-lg font-semibold mb-4">Live Tracking Status</h3>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {order.goshippo_tracking.tracking_status && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Current Status</p>
                      <p className="mt-1 text-lg font-medium text-blue-900">{order.goshippo_tracking.tracking_status}</p>
                    </div>
                  )}
                  {order.goshippo_tracking.eta && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Estimated Delivery (Updated)</p>
                      <p className="mt-1 text-lg font-medium text-blue-900">
                        {new Date(order.goshippo_tracking.eta).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Help Section */}
          <div className="bg-gray-50 px-6 py-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Need help with your order?{' '}
                <a href="mailto:support@pasargadprints.com" className="text-primary-600 hover:text-primary-700 font-medium">
                  Contact Support
                </a>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Section */}
      {!order && !isLoading && (
        <div className="max-w-2xl mx-auto mt-12">
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">How to Find Your Tracking Information</h3>
            <div className="space-y-2 text-sm text-blue-700">
              <p>
                <strong>Tracking Number:</strong> You'll find this in your shipping confirmation email once your order has been dispatched.
              </p>
              <p>
                <strong>Order Number:</strong> This was provided in your order confirmation email and looks like "ABC123456".
              </p>
              <p>
                <strong>Email Address:</strong> Use the email address you provided during checkout.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderTrackingPage;