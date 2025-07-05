import { useSelector, useDispatch } from 'react-redux'
import { Link, useNavigate } from 'react-router-dom'
import type { AppDispatch, RootState } from '../store/index'
import { updateCartItem, removeFromCart, clearCart } from '../store/slices/cartSlice'
import LoadingSpinner from '../components/LoadingSpinner'

const CartPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { cart, isLoading } = useSelector((state: RootState) => state.cart)

  const handleQuantityChange = (itemId: number, quantity: number) => {
    if (quantity === 0) {
      dispatch(removeFromCart(itemId))
    } else {
      dispatch(updateCartItem({ itemId, quantity }))
    }
  }

  const handleRemoveItem = (itemId: number) => {
    dispatch(removeFromCart(itemId))
  }

  const handleClearCart = () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      dispatch(clearCart())
    }
  }

  const handleCheckout = () => {
    // Allow both authenticated and guest users to proceed to checkout
    navigate('/checkout')
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="mb-8">
            <svg className="w-24 h-24 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold mb-4">Your Cart is Empty</h2>
          <p className="text-gray-600 mb-8">Looks like you haven't added any items to your cart yet.</p>
          <Link
            to="/products"
            className="inline-block bg-primary-600 text-white px-6 py-3 rounded-md font-semibold hover:bg-primary-700 transition-colors"
          >
            Start Shopping
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Cart Items ({cart.total_items})</h2>
                <button
                  onClick={handleClearCart}
                  className="text-red-600 hover:text-red-700 text-sm"
                >
                  Clear Cart
                </button>
              </div>

              <div className="space-y-4">
                {cart.items.map((item) => (
                  <div key={item.id} className="border-b pb-4 last:border-0">
                    <div className="flex items-start gap-4">
                      {/* Product Image */}
                      <Link to={`/products/${item.product.id}`} className="flex-shrink-0">
                        {item.product.main_image ? (
                          <img
                            src={item.product.main_image}
                            alt={item.product.name}
                            className="w-20 h-20 sm:w-24 sm:h-24 object-cover rounded"
                          />
                        ) : (
                          <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gray-200 rounded flex items-center justify-center">
                            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          </div>
                        )}
                      </Link>

                      {/* Product Info and Controls */}
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start">
                          {/* Product Details */}
                          <div className="mb-2 sm:mb-0">
                            <Link
                              to={`/products/${item.product.id}`}
                              className="text-base sm:text-lg font-medium hover:text-primary-600 block truncate"
                            >
                              {item.product.name}
                            </Link>
                            <p className="text-sm text-gray-600">{item.product.category_name}</p>
                            <p className="text-primary-600 font-semibold">${item.product.price}</p>
                          </div>

                          {/* Desktop Item Total */}
                          <div className="hidden sm:block text-right">
                            <p className="font-semibold">${item.total_price}</p>
                          </div>
                        </div>

                        {/* Quantity Controls and Actions */}
                        <div className="flex items-center justify-between mt-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                              className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center"
                              aria-label="Decrease quantity"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                              </svg>
                            </button>
                            <span className="w-12 text-center font-medium">{item.quantity}</span>
                            <button
                              onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                              className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center"
                              aria-label="Increase quantity"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                              </svg>
                            </button>
                          </div>

                          {/* Mobile Item Total and Remove */}
                          <div className="flex items-center gap-4">
                            <p className="font-semibold sm:hidden">${item.total_price}</p>
                            <button
                              onClick={() => handleRemoveItem(item.id)}
                              className="text-red-600 hover:text-red-700 text-sm"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-4 sm:p-6 sticky top-20">
            <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-medium">${cart.total_price}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span className="font-medium">Calculated at checkout</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax</span>
                <span className="font-medium">Calculated at checkout</span>
              </div>
            </div>
            
            <div className="border-t pt-4 mb-6">
              <div className="flex justify-between">
                <span className="text-lg font-semibold">Total</span>
                <span className="text-lg font-semibold">${cart.total_price}</span>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-semibold hover:bg-primary-700 transition-colors"
            >
              Proceed to Checkout
            </button>

            <div className="mt-4 text-center">
              <Link to="/products" className="text-primary-600 hover:text-primary-700 text-sm">
                Continue Shopping
              </Link>
            </div>

            {/* Shipping Info */}
            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <h3 className="font-medium mb-2">Shipping Information</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Free shipping on orders over $100</li>
                <li>• Express shipping available</li>
                <li>• Local pickup option available</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CartPage