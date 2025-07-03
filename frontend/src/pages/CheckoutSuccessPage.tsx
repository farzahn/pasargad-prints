import { useEffect, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { clearCart } from '../store/slices/cartSlice'
import type { AppDispatch } from '../store/index'

interface OrderInfo {
  order_id: number
  order_number: string
}

const CheckoutSuccessPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const [isLoading, setIsLoading] = useState(true)
  const [orderInfo, setOrderInfo] = useState<OrderInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const sessionId = searchParams.get('session_id')
    
    if (!sessionId) {
      navigate('/')
      return
    }

    verifyPayment(sessionId)
  }, [searchParams, navigate])

  const verifyPayment = async (sessionId: string) => {
    try {
      const response = await api.get(`/api/payments/verify-checkout-session/?session_id=${sessionId}`)
      
      if (response.data.status === 'success') {
        setOrderInfo({
          order_id: response.data.order_id,
          order_number: response.data.order_number,
        })
        
        // Clear the cart after successful payment
        dispatch(clearCart())
      } else if (response.data.status === 'pending') {
        // Payment is still processing
        setTimeout(() => verifyPayment(sessionId), 2000) // Check again in 2 seconds
        return
      }
    } catch (error: any) {
      console.error('Error verifying payment:', error)
      setError('Failed to verify payment. Please contact support.')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-gray-600">Verifying your payment...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="mb-4">
            <svg className="w-16 h-16 text-red-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold mb-2">Payment Verification Failed</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link
            to="/"
            className="inline-block bg-primary-600 text-white px-6 py-3 rounded-md font-semibold hover:bg-primary-700 transition-colors"
          >
            Return to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="mb-6">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
          <p className="text-gray-600">Thank you for your order</p>
        </div>

        {orderInfo && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h2 className="font-semibold mb-2">Order Details</h2>
            <p className="text-gray-600">Order Number: <span className="font-medium text-gray-900">{orderInfo.order_number}</span></p>
            <p className="text-sm text-gray-500 mt-2">
              You will receive an email confirmation shortly with your order details and tracking information.
            </p>
          </div>
        )}

        <div className="space-y-3">
          <Link
            to="/profile"
            className="block w-full bg-primary-600 text-white py-3 px-4 rounded-md font-semibold hover:bg-primary-700 transition-colors"
          >
            View Order Details
          </Link>
          <Link
            to="/products"
            className="block w-full border border-gray-300 text-gray-700 py-3 px-4 rounded-md font-semibold hover:bg-gray-50 transition-colors"
          >
            Continue Shopping
          </Link>
        </div>

        <div className="mt-8 p-4 bg-blue-50 rounded-md">
          <h3 className="font-medium text-blue-900 mb-2">What's Next?</h3>
          <ul className="text-sm text-blue-700 space-y-1 text-left">
            <li>• You'll receive an order confirmation email</li>
            <li>• We'll notify you when your order ships</li>
            <li>• Track your order in your account</li>
            <li>• Contact support if you have any questions</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default CheckoutSuccessPage