import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store/index'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const CheckoutPage = () => {
  const navigate = useNavigate()
  const { cart } = useSelector((state: RootState) => state.cart)
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [checkoutUrl, setCheckoutUrl] = useState<string | null>(null)

  useEffect(() => {
    // Redirect if cart is empty
    if (!cart || cart.items.length === 0) {
      navigate('/cart')
    }
  }, [cart, navigate])

  const handleCheckout = async () => {
    setIsLoading(true)
    setError(null)
    setCheckoutUrl(null)

    try {
      // Clear any stale browser data that might interfere
      try {
        // Only clear non-essential storage
        const keysToKeep = ['accessToken', 'refreshToken', 'rememberUsername', 'persist:root']
        const allKeys = Object.keys(localStorage)
        allKeys.forEach(key => {
          if (!keysToKeep.some(k => key.includes(k))) {
            localStorage.removeItem(key)
          }
        })
      } catch (e) {
        console.warn('Could not clear storage:', e)
      }

      // Make the API call to create checkout session
      console.log('Creating checkout session...')
      const response = await api.post('/api/payments/create-checkout-session/', {
        success_url: `${window.location.origin}/checkout/success`,
        cancel_url: `${window.location.origin}/checkout/cancel`,
      })

      console.log('Checkout response:', response.data)

      // Check if we got a valid checkout URL
      if (response.data && response.data.checkout_url) {
        const stripeCheckoutUrl = response.data.checkout_url
        
        // Validate the URL
        if (!stripeCheckoutUrl.startsWith('https://checkout.stripe.com/')) {
          throw new Error('Invalid checkout URL received')
        }

        console.log('Redirecting to Stripe checkout:', stripeCheckoutUrl)
        
        // Save the URL in case redirect fails
        setCheckoutUrl(stripeCheckoutUrl)
        
        // Try multiple redirect methods
        try {
          // Method 1: Direct assignment (most reliable)
          window.location.href = stripeCheckoutUrl
        } catch (e1) {
          console.warn('Direct redirect failed, trying replace:', e1)
          try {
            // Method 2: Replace current page
            window.location.replace(stripeCheckoutUrl)
          } catch (e2) {
            console.warn('Replace redirect failed, trying link click:', e2)
            // Method 3: Create and click a link
            const link = document.createElement('a')
            link.href = stripeCheckoutUrl
            link.target = '_self'
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()
            setTimeout(() => document.body.removeChild(link), 100)
          }
        }

        // If we're still here after 3 seconds, show manual redirect option
        setTimeout(() => {
          if (document.location.href === window.location.href) {
            setError('Automatic redirect failed. Please use the link below to continue.')
            setIsLoading(false)
          }
        }, 3000)
        
      } else {
        throw new Error('No checkout URL received from server')
      }
      
    } catch (error: any) {
      console.error('Checkout error:', error)
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText
      })
      
      // User-friendly error messages
      let errorMessage = 'Unable to process checkout. Please try again.'
      
      if (!navigator.onLine) {
        errorMessage = 'No internet connection. Please check your connection and try again.'
      } else if (error.response) {
        switch (error.response.status) {
          case 400:
            errorMessage = error.response.data?.error || 'Invalid request. Please check your cart and try again.'
            break
          case 401:
            errorMessage = 'Session expired. Please refresh the page and try again.'
            break
          case 404:
            errorMessage = 'Checkout service not available. Please try again later.'
            break
          case 422:
            errorMessage = error.response.data?.error || 'Unable to process your cart. Please check your items.'
            break
          case 500:
          case 502:
          case 503:
            errorMessage = 'Server error. Our team has been notified. Please try again in a few minutes.'
            break
          default:
            if (error.response.data?.error) {
              errorMessage = error.response.data.error
            }
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      setError(errorMessage)
      setIsLoading(false)
    }
  }

  if (!cart || cart.items.length === 0) {
    return <LoadingSpinner />
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Order Summary */}
        <div className="order-2 lg:order-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
            
            <div className="space-y-4 mb-6">
              {cart.items.map((item) => (
                <div key={item.id} className="flex items-center gap-4">
                  {item.product.main_image ? (
                    <img
                      src={item.product.main_image}
                      alt={item.product.name}
                      className="w-16 h-16 object-cover rounded"
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gray-200 rounded flex items-center justify-center">
                      <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  )}
                  
                  <div className="flex-1">
                    <h3 className="font-medium">{item.product.name}</h3>
                    <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                  </div>
                  
                  <div className="text-right">
                    <p className="font-medium">${item.total_price}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">${cart.total_price}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span className="font-medium">Calculated at next step</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax</span>
                <span className="font-medium">Calculated at next step</span>
              </div>
              <div className="border-t pt-2 mt-2">
                <div className="flex justify-between">
                  <span className="text-lg font-semibold">Total</span>
                  <span className="text-lg font-semibold">${cart.total_price}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Checkout Info */}
        <div className="order-1 lg:order-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Checkout Information</h2>
            
            <div className="mb-6">
              <h3 className="font-medium mb-2">Customer Information</h3>
              {isAuthenticated && user ? (
                <p className="text-gray-600">{user.email}</p>
              ) : (
                <div className="space-y-3">
                  <p className="text-gray-600 text-sm">Checking out as guest</p>
                  <div className="p-3 bg-blue-50 rounded-md">
                    <p className="text-sm text-blue-700">
                      Want to track your order? 
                      <button
                        onClick={() => navigate('/login', { state: { from: { pathname: '/checkout' } } })}
                        className="ml-1 underline hover:text-blue-800"
                      >
                        Sign in
                      </button>
                      {' '}or{' '}
                      <button
                        onClick={() => navigate('/register', { state: { from: { pathname: '/checkout' } } })}
                        className="underline hover:text-blue-800"
                      >
                        create an account
                      </button>
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="mb-6">
              <h3 className="font-medium mb-2">Payment Method</h3>
              <div className="p-4 border rounded-md bg-gray-50">
                <div className="flex items-center gap-2">
                  <svg className="w-8 h-8" viewBox="0 0 32 32">
                    <path fill="#635BFF" d="M16 0C7.163 0 0 7.163 0 16s7.163 16 16 16 16-7.163 16-16S24.837 0 16 0zm7.451 11.193l-2.893 8.968c-.152.47-.614.81-1.133.81h-.013c-.52-.006-.974-.353-1.119-.828l-1.715-5.624-5.625-1.715c-.475-.145-.822-.6-.828-1.119v-.013c0-.518.34-.98.81-1.133l8.968-2.893c.128-.041.261-.062.394-.062.133 0 .267.021.394.062.376.121.655.4.776.776.041.128.062.261.062.394s-.021.267-.062.394z"/>
                  </svg>
                  <span className="font-medium">Secure Checkout with Stripe</span>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  You'll be redirected to Stripe's secure checkout page
                </p>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="font-medium mb-2">What happens next?</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Click "Proceed to Payment" below</li>
                <li>• You'll be redirected to Stripe's secure checkout</li>
                <li>• Enter your shipping and payment information</li>
                <li>• Review and confirm your order</li>
                <li>• Receive order confirmation via email</li>
              </ul>
            </div>

            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-red-600 text-sm font-medium">{error}</p>
                    {checkoutUrl && (
                      <div className="mt-3">
                        <a 
                          href={checkoutUrl}
                          target="_self"
                          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 underline text-sm font-medium"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          Click here to continue to checkout
                        </a>
                        <details className="mt-2">
                          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-600">
                            Having trouble? Show checkout URL
                          </summary>
                          <div className="mt-2 p-2 bg-gray-100 rounded text-xs break-all select-all font-mono">
                            {checkoutUrl}
                          </div>
                        </details>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={handleCheckout}
              disabled={isLoading}
              className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <span>Proceed to Payment</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </>
              )}
            </button>

            <div className="mt-4 text-center">
              <button
                onClick={() => navigate('/cart')}
                className="text-primary-600 hover:text-primary-700 text-sm inline-flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                </svg>
                Back to Cart
              </button>
            </div>

            {/* Security Badge */}
            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <span>Your payment information is secure and encrypted</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CheckoutPage