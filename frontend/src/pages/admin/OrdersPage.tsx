import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useSearchParams } from 'react-router-dom'
import type { RootState, AppDispatch } from '../../store'
import { 
  fetchOrders, 
  updateOrderStatus, 
  updatePaymentStatus,
  updateTrackingNumber 
} from '../../store/slices/adminSlice'
import LoadingSpinner from '../../components/LoadingSpinner'
import type { Order } from '../../types'

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

const paymentStatusColors = {
  pending: 'bg-gray-100 text-gray-800',
  paid: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-orange-100 text-orange-800',
}

export default function OrdersPage() {
  const dispatch = useDispatch<AppDispatch>()
  const [searchParams, setSearchParams] = useSearchParams()
  const { orders, ordersCount, isLoading } = useSelector((state: RootState) => state.admin)
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [trackingNumber, setTrackingNumber] = useState('')

  useEffect(() => {
    const status = searchParams.get('status')
    const payment_status = searchParams.get('payment_status')
    
    dispatch(fetchOrders({
      status: status || undefined,
      payment_status: payment_status || undefined,
    }))
  }, [dispatch, searchParams])

  const handleStatusChange = async (orderId: number, status: Order['status']) => {
    await dispatch(updateOrderStatus({ id: orderId, status }))
    dispatch(fetchOrders())
  }

  const handlePaymentStatusChange = async (orderId: number, payment_status: Order['payment_status']) => {
    await dispatch(updatePaymentStatus({ id: orderId, payment_status }))
    dispatch(fetchOrders())
  }

  const handleTrackingUpdate = async (orderId: number) => {
    if (trackingNumber.trim()) {
      await dispatch(updateTrackingNumber({ id: orderId, tracking_number: trackingNumber }))
      setTrackingNumber('')
      setSelectedOrder(null)
      dispatch(fetchOrders())
    }
  }

  const handleCreateShipment = async (orderId: number) => {
    try {
      const response = await fetch(`/api/orders/${orderId}/shipment/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(`Shipment created successfully! Shipment ID: ${data.shipment_id}`)
        dispatch(fetchOrders())
      } else {
        const error = await response.json()
        alert(`Error creating shipment: ${error.error}`)
      }
    } catch (error) {
      alert('Failed to create shipment')
    }
  }

  const handlePurchaseLabel = async (orderId: number, rateId: string) => {
    try {
      const response = await fetch(`/api/orders/${orderId}/label/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ rate_id: rateId }),
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(`Label purchased successfully! Tracking: ${data.tracking_number}`)
        dispatch(fetchOrders())
      } else {
        const error = await response.json()
        alert(`Error purchasing label: ${error.error}`)
      }
    } catch (error) {
      alert('Failed to purchase label')
    }
  }

  if (isLoading && orders.length === 0) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Orders Management</h1>
          <p className="text-gray-600">Manage and track all customer orders</p>
        </div>
        <div className="mt-4 sm:mt-0">
          <span className="text-sm text-gray-500">Total Orders: {ordersCount}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4">
          <select
            value={searchParams.get('status') || ''}
            onChange={(e) => {
              const newParams = new URLSearchParams(searchParams)
              if (e.target.value) {
                newParams.set('status', e.target.value)
              } else {
                newParams.delete('status')
              }
              setSearchParams(newParams)
            }}
            className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="shipped">Shipped</option>
            <option value="delivered">Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <select
            value={searchParams.get('payment_status') || ''}
            onChange={(e) => {
              const newParams = new URLSearchParams(searchParams)
              if (e.target.value) {
                newParams.set('payment_status', e.target.value)
              } else {
                newParams.delete('payment_status')
              }
              setSearchParams(newParams)
            }}
            className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Payment Statuses</option>
            <option value="pending">Payment Pending</option>
            <option value="paid">Paid</option>
            <option value="failed">Failed</option>
            <option value="refunded">Refunded</option>
          </select>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order #
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {order.order_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>
                      <p className="font-medium">{order.user.first_name} {order.user.last_name}</p>
                      <p className="text-xs text-gray-400">{order.user.email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${order.total_amount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <select
                      value={order.status}
                      onChange={(e) => handleStatusChange(order.id, e.target.value as Order['status'])}
                      className={`text-xs px-2 py-1 rounded-full font-medium ${statusColors[order.status]}`}
                    >
                      <option value="pending">Pending</option>
                      <option value="processing">Processing</option>
                      <option value="shipped">Shipped</option>
                      <option value="delivered">Delivered</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <select
                      value={order.payment_status}
                      onChange={(e) => handlePaymentStatusChange(order.id, e.target.value as Order['payment_status'])}
                      className={`text-xs px-2 py-1 rounded-full font-medium ${paymentStatusColors[order.payment_status]}`}
                    >
                      <option value="pending">Pending</option>
                      <option value="paid">Paid</option>
                      <option value="failed">Failed</option>
                      <option value="refunded">Refunded</option>
                    </select>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <button
                      onClick={() => setSelectedOrder(order)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Order Details Modal */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setSelectedOrder(null)}
            />
            <div className="relative bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Order Details - {selectedOrder.order_number}</h2>
                  <button
                    onClick={() => setSelectedOrder(null)}
                    className="text-gray-400 hover:text-gray-500"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Customer Information */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Customer Information</h3>
                    <div className="bg-gray-50 rounded p-4 space-y-2 text-sm">
                      <p><span className="font-medium">Name:</span> {selectedOrder.user.first_name} {selectedOrder.user.last_name}</p>
                      <p><span className="font-medium">Email:</span> {selectedOrder.user.email}</p>
                      <p><span className="font-medium">Phone:</span> {selectedOrder.user.phone || 'N/A'}</p>
                    </div>
                  </div>

                  {/* Order Information */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Order Information</h3>
                    <div className="bg-gray-50 rounded p-4 space-y-2 text-sm">
                      <p><span className="font-medium">Date:</span> {new Date(selectedOrder.created_at).toLocaleString()}</p>
                      <p><span className="font-medium">Payment Method:</span> {selectedOrder.payment_method}</p>
                      <p><span className="font-medium">Tracking:</span> {selectedOrder.tracking_number || 'Not set'}</p>
                    </div>
                  </div>

                  {/* Shipping Address */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Shipping Address</h3>
                    <div className="bg-gray-50 rounded p-4 text-sm">
                      <p>{selectedOrder.shipping_address.street_address}</p>
                      {selectedOrder.shipping_address.apartment && <p>{selectedOrder.shipping_address.apartment}</p>}
                      <p>{selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state} {selectedOrder.shipping_address.postal_code}</p>
                      <p>{selectedOrder.shipping_address.country}</p>
                    </div>
                  </div>

                  {/* Billing Address */}
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Billing Address</h3>
                    <div className="bg-gray-50 rounded p-4 text-sm">
                      <p>{selectedOrder.billing_address.street_address}</p>
                      {selectedOrder.billing_address.apartment && <p>{selectedOrder.billing_address.apartment}</p>}
                      <p>{selectedOrder.billing_address.city}, {selectedOrder.billing_address.state} {selectedOrder.billing_address.postal_code}</p>
                      <p>{selectedOrder.billing_address.country}</p>
                    </div>
                  </div>
                </div>

                {/* Order Items */}
                <div className="mt-6">
                  <h3 className="font-medium text-gray-900 mb-2">Order Items</h3>
                  <div className="bg-gray-50 rounded overflow-hidden">
                    <table className="min-w-full">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {selectedOrder.items.map((item) => (
                          <tr key={item.id}>
                            <td className="px-4 py-2 text-sm">{item.product.name}</td>
                            <td className="px-4 py-2 text-sm text-right">${item.price}</td>
                            <td className="px-4 py-2 text-sm text-right">{item.quantity}</td>
                            <td className="px-4 py-2 text-sm text-right font-medium">${item.total_price}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot className="bg-gray-100">
                        <tr>
                          <td colSpan={3} className="px-4 py-2 text-sm text-right">Subtotal:</td>
                          <td className="px-4 py-2 text-sm text-right font-medium">${selectedOrder.subtotal}</td>
                        </tr>
                        <tr>
                          <td colSpan={3} className="px-4 py-2 text-sm text-right">Tax:</td>
                          <td className="px-4 py-2 text-sm text-right font-medium">${selectedOrder.tax_amount}</td>
                        </tr>
                        <tr>
                          <td colSpan={3} className="px-4 py-2 text-sm text-right">Shipping:</td>
                          <td className="px-4 py-2 text-sm text-right font-medium">${selectedOrder.shipping_cost}</td>
                        </tr>
                        <tr>
                          <td colSpan={3} className="px-4 py-2 text-sm text-right font-semibold">Total:</td>
                          <td className="px-4 py-2 text-sm text-right font-bold">${selectedOrder.total_amount}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>

                {/* Goshippo Shipping Actions */}
                {selectedOrder.status !== 'cancelled' && selectedOrder.status !== 'delivered' && (
                  <div className="mt-6">
                    <h3 className="font-medium text-gray-900 mb-4">Shipping Actions (Goshippo)</h3>
                    <div className="space-y-3">
                      {selectedOrder.status === 'processing' && !selectedOrder.tracking_number && (
                        <button
                          onClick={() => handleCreateShipment(selectedOrder.id)}
                          className="w-full px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
                        >
                          Create Goshippo Shipment
                        </button>
                      )}
                      
                      {selectedOrder.status === 'processing' && selectedOrder.tracking_number && (
                        <div className="bg-green-50 border border-green-200 rounded-md p-4">
                          <p className="text-sm text-green-800">
                            <strong>Shipment Created:</strong> Order is ready for label purchase
                          </p>
                          <p className="text-xs text-green-600 mt-1">
                            Tracking: {selectedOrder.tracking_number}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Manual Tracking Number (fallback) */}
                {selectedOrder.status === 'shipped' && !selectedOrder.tracking_number && (
                  <div className="mt-6">
                    <h3 className="font-medium text-gray-900 mb-2">Add Tracking Number (Manual)</h3>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={trackingNumber}
                        onChange={(e) => setTrackingNumber(e.target.value)}
                        placeholder="Enter tracking number"
                        className="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <button
                        onClick={() => handleTrackingUpdate(selectedOrder.id)}
                        className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                )}

                {/* Notes */}
                {selectedOrder.notes && (
                  <div className="mt-6">
                    <h3 className="font-medium text-gray-900 mb-2">Order Notes</h3>
                    <div className="bg-yellow-50 rounded p-4">
                      <p className="text-sm">{selectedOrder.notes}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}