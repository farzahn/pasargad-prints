import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { AppDispatch, RootState } from '../store/index'
import { fetchProductDetail } from '../store/slices/productsSlice'
import { addToCart } from '../store/slices/cartSlice'
import WishlistButton from './WishlistButton'
import LoadingSpinner from './LoadingSpinner'

interface ProductQuickViewProps {
  productId: number
  isOpen: boolean
  onClose: () => void
}

const ProductQuickView = ({ productId, isOpen, onClose }: ProductQuickViewProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const { currentProduct: productDetail, isLoading: loading, error } = useSelector((state: RootState) => state.products)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (isOpen && productId) {
      dispatch(fetchProductDetail(productId))
    }
  }, [dispatch, isOpen, productId])

  useEffect(() => {
    if (productDetail?.main_image && !selectedImage) {
      setSelectedImage(productDetail.main_image)
    }
  }, [productDetail, selectedImage])

  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true)
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const handleAddToCart = () => {
    if (productDetail) {
      // Check if product is in stock
      if (!productDetail.is_in_stock) {
        alert('This product is currently out of stock')
        return
      }
      
      // Check if requested quantity is available
      if (quantity > productDetail.stock_quantity) {
        alert(`Only ${productDetail.stock_quantity} items available`)
        return
      }
      
      dispatch(addToCart({ product_id: productDetail.id, quantity }))
    }
  }

  const handleQuantityChange = (value: number) => {
    if (value >= 1 && value <= (productDetail?.stock_quantity || 0)) {
      setQuantity(value)
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black bg-opacity-50 z-50 transition-opacity duration-300 ${
          isAnimating ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className={`bg-white rounded-lg shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden pointer-events-auto transform transition-all duration-300 ${
            isAnimating ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 bg-white rounded-full p-2 shadow-md hover:shadow-lg transition-shadow"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {loading ? (
            <div className="flex items-center justify-center h-96">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-96">
              <p className="text-red-600">{error}</p>
            </div>
          ) : productDetail ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 md:p-8 overflow-y-auto max-h-[90vh]">
              {/* Images */}
              <div>
                <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-4">
                  {selectedImage ? (
                    <img
                      src={selectedImage}
                      alt={productDetail.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <svg className="w-24 h-24 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  )}
                </div>

                {/* Thumbnail images */}
                {productDetail.images && productDetail.images.length > 0 && (
                  <div className="grid grid-cols-4 gap-2">
                    {productDetail.images.map((image) => (
                      <button
                        key={image.id}
                        onClick={() => setSelectedImage(image.image)}
                        className={`aspect-square bg-gray-100 rounded overflow-hidden border-2 transition-colors ${
                          selectedImage === image.image ? 'border-primary-600' : 'border-gray-200'
                        }`}
                      >
                        <img
                          src={image.image}
                          alt={image.alt_text}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Product Info */}
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">{productDetail.name}</h2>
                <p className="text-sm text-gray-600 mb-4">{productDetail.category_name}</p>

                {/* Rating */}
                {productDetail.review_count > 0 && (
                  <div className="flex items-center mb-4">
                    <div className="flex text-yellow-400">
                      {[...Array(5)].map((_, i) => (
                        <svg
                          key={i}
                          className={`w-5 h-5 ${
                            i < Math.floor(productDetail.average_rating) ? 'fill-current' : 'stroke-current fill-none'
                          }`}
                          viewBox="0 0 24 24"
                        >
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                      ))}
                    </div>
                    <span className="text-sm text-gray-600 ml-2">
                      {productDetail.average_rating.toFixed(1)} ({productDetail.review_count} reviews)
                    </span>
                  </div>
                )}

                <p className="text-3xl font-bold text-primary-600 mb-6">${productDetail.price}</p>

                <p className="text-gray-700 mb-6">{productDetail.description}</p>

                {/* Product details */}
                <div className="border-t border-gray-200 pt-6 mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Product Details</h3>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">SKU:</dt>
                      <dd className="text-gray-900">{productDetail.sku}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Material:</dt>
                      <dd className="text-gray-900">{productDetail.material}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Dimensions:</dt>
                      <dd className="text-gray-900">{productDetail.dimensions}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Weight:</dt>
                      <dd className="text-gray-900">{productDetail.weight} kg</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Print Time:</dt>
                      <dd className="text-gray-900">{productDetail.print_time} hours</dd>
                    </div>
                  </dl>
                </div>

                {/* Add to cart section */}
                {productDetail.is_in_stock ? (
                  <div className="space-y-4">
                    <div className="flex items-center space-x-4">
                      <label className="text-gray-700 font-medium">Quantity:</label>
                      <div className="flex items-center border border-gray-300 rounded-md">
                        <button
                          onClick={() => handleQuantityChange(quantity - 1)}
                          className="px-3 py-2 hover:bg-gray-100 transition-colors"
                          disabled={quantity <= 1}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                          </svg>
                        </button>
                        <input
                          type="number"
                          value={quantity}
                          onChange={(e) => handleQuantityChange(parseInt(e.target.value) || 1)}
                          className="w-16 text-center border-x border-gray-300 py-2 focus:outline-none"
                          min="1"
                          max={productDetail.stock_quantity}
                        />
                        <button
                          onClick={() => handleQuantityChange(quantity + 1)}
                          className="px-3 py-2 hover:bg-gray-100 transition-colors"
                          disabled={quantity >= productDetail.stock_quantity}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                        </button>
                      </div>
                      <span className="text-sm text-gray-600">
                        {productDetail.stock_quantity} in stock
                      </span>
                    </div>

                    <div className="flex space-x-4">
                      <button
                        onClick={handleAddToCart}
                        className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-md hover:bg-primary-700 transition-colors font-medium"
                      >
                        Add to Cart
                      </button>
                      <WishlistButton 
                        product={{
                          id: productDetail.id,
                          name: productDetail.name,
                          price: productDetail.price,
                          category_name: productDetail.category_name,
                          main_image: productDetail.main_image,
                          is_in_stock: productDetail.is_in_stock,
                          average_rating: productDetail.average_rating,
                          review_count: productDetail.review_count,
                        }} 
                        size="lg" 
                      />
                    </div>
                  </div>
                ) : (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-red-600 font-medium">Out of Stock</p>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </>
  )
}

export default ProductQuickView