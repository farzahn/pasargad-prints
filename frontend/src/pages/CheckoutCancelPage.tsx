import { Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store/index'

const CheckoutCancelPage = () => {
  const { cart } = useSelector((state: RootState) => state.cart)

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="mb-6">
          <div className="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Cancelled</h1>
          <p className="text-gray-600">Your payment was cancelled and no charges were made.</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <h2 className="font-semibold mb-2">Your items are still in your cart</h2>
          <p className="text-gray-600 text-sm">
            Don't worry! Your cart items are safe and waiting for you whenever you're ready to complete your purchase.
          </p>
          {cart && cart.total_items > 0 && (
            <div className="mt-3 text-sm">
              <span className="text-gray-500">Cart items: </span>
              <span className="font-medium text-gray-900">{cart.total_items} items</span>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <Link
            to="/cart"
            className="block w-full bg-primary-600 text-white py-3 px-4 rounded-md font-semibold hover:bg-primary-700 transition-colors"
          >
            Return to Cart
          </Link>
          <Link
            to="/products"
            className="block w-full border border-gray-300 text-gray-700 py-3 px-4 rounded-md font-semibold hover:bg-gray-50 transition-colors"
          >
            Continue Shopping
          </Link>
        </div>

        <div className="mt-8 p-4 bg-blue-50 rounded-md">
          <h3 className="font-medium text-blue-900 mb-2">Need Help?</h3>
          <p className="text-sm text-blue-700 mb-3">
            If you experienced any issues during checkout or have questions about your order, we're here to help!
          </p>
          <a
            href="mailto:support@pasargadprints.com"
            className="text-sm text-blue-700 underline hover:text-blue-800"
          >
            Contact Support
          </a>
        </div>

        <div className="mt-6 text-sm text-gray-500">
          <p>Common reasons for cancelled payments:</p>
          <ul className="mt-2 space-y-1">
            <li>• Changed your mind during checkout</li>
            <li>• Need to update payment information</li>
            <li>• Want to modify your order</li>
            <li>• Technical issues during payment</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default CheckoutCancelPage