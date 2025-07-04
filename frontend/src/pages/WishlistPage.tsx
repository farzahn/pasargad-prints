import { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { Link, useNavigate } from 'react-router-dom'
import type { AppDispatch, RootState } from '../store/index'
import {
  fetchWishlist,
  removeFromWishlist,
  clearWishlist,
  selectWishlistItems,
  selectWishlistLoading,
  selectWishlistError,
} from '../store/slices/wishlistSlice'
import { addToCart } from '../store/slices/cartSlice'
import WishlistButton from '../components/WishlistButton'
import LoadingSpinner from '../components/LoadingSpinner'

const WishlistPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const wishlistItems = useSelector(selectWishlistItems)
  const loading = useSelector(selectWishlistLoading)
  const error = useSelector(selectWishlistError)
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated)

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchWishlist())
    }
  }, [dispatch, isAuthenticated])

  const handleMoveToCart = async (productId: number, itemId: number) => {
    try {
      await dispatch(addToCart({ product_id: productId, quantity: 1 })).unwrap()
      await dispatch(removeFromWishlist({ item_id: itemId })).unwrap()
    } catch (error) {
      console.error('Failed to move item to cart:', error)
    }
  }

  const handleClearWishlist = async () => {
    if (window.confirm('Are you sure you want to clear your wishlist?')) {
      await dispatch(clearWishlist())
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Please Sign In</h2>
          <p className="text-gray-600 mb-8">You need to be signed in to view your wishlist.</p>
          <Link
            to="/login"
            className="bg-primary-600 text-white px-6 py-3 rounded-md hover:bg-primary-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center text-red-600">
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Wishlist</h1>
        {wishlistItems.length > 0 && (
          <button
            onClick={handleClearWishlist}
            className="text-red-600 hover:text-red-800 font-medium transition-colors"
          >
            Clear Wishlist
          </button>
        )}
      </div>

      {wishlistItems.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="w-24 h-24 text-gray-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Your wishlist is empty</h2>
          <p className="text-gray-600 mb-8">Start adding items you love to your wishlist!</p>
          <Link
            to="/products"
            className="bg-primary-600 text-white px-6 py-3 rounded-md hover:bg-primary-700 transition-colors inline-block"
          >
            Browse Products
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {wishlistItems.map((item, index) => (
            <div
              key={item.id}
              className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow animate-slide-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <Link to={`/products/${item.product.id}`} className="block">
                <div className="aspect-square bg-gray-100 relative overflow-hidden">
                  {item.product.main_image ? (
                    <img
                      src={item.product.main_image}
                      alt={item.product.name}
                      className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <svg
                        className="w-16 h-16 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                  )}

                  {!item.product.is_in_stock && (
                    <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm">
                      Out of Stock
                    </div>
                  )}
                </div>
              </Link>

              <div className="p-4">
                <Link to={`/products/${item.product.id}`} className="block mb-3">
                  <h3 className="font-semibold text-lg mb-1 hover:text-primary-600 transition-colors">
                    {item.product.name}
                  </h3>
                  <p className="text-sm text-gray-600">{item.product.category_name}</p>
                  <p className="text-xl font-bold text-primary-600 mt-2">${item.product.price}</p>
                </Link>

                <div className="flex gap-2 mt-4">
                  {item.product.is_in_stock ? (
                    <button
                      onClick={() => handleMoveToCart(item.product.id, item.id)}
                      className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 transition-colors font-medium"
                    >
                      Move to Cart
                    </button>
                  ) : (
                    <button
                      disabled
                      className="flex-1 bg-gray-300 text-gray-500 py-2 px-4 rounded-md cursor-not-allowed font-medium"
                    >
                      Out of Stock
                    </button>
                  )}
                  <WishlistButton product={item.product} size="md" />
                </div>

                <p className="text-xs text-gray-500 mt-3">
                  Added on {new Date(item.added_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default WishlistPage