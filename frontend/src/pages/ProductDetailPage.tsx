import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import type { AppDispatch, RootState } from '../store/index'
import { fetchProductDetail, clearCurrentProduct } from '../store/slices/productsSlice'
import { addToCart } from '../store/slices/cartSlice'
import LoadingSpinner from '../components/LoadingSpinner'
import LazyImage from '../components/LazyImage'
import SEO from '../components/SEO'
import { ProductStructuredData, BreadcrumbStructuredData } from '../components/StructuredData'

const ProductDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { currentProduct, isLoading, error } = useSelector((state: RootState) => state.products)
  const [selectedImage, setSelectedImage] = useState<string>('')
  const [quantity, setQuantity] = useState(1)
  const [showReviewForm, setShowReviewForm] = useState(false)

  useEffect(() => {
    if (id) {
      dispatch(fetchProductDetail(parseInt(id)))
    }

    return () => {
      dispatch(clearCurrentProduct())
    }
  }, [dispatch, id])

  useEffect(() => {
    if (currentProduct?.main_image) {
      setSelectedImage(currentProduct.main_image)
    } else if (currentProduct?.images?.length > 0) {
      setSelectedImage(currentProduct.images[0].image)
    }
  }, [currentProduct])

  const handleAddToCart = () => {
    if (currentProduct) {
      // Check if product is in stock
      if (!currentProduct.is_in_stock) {
        alert('This product is currently out of stock')
        return
      }
      
      // Check if requested quantity is available
      if (quantity > currentProduct.stock_quantity) {
        alert(`Only ${currentProduct.stock_quantity} items available`)
        return
      }
      
      dispatch(addToCart({ product_id: currentProduct.id, quantity }))
    }
  }

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value)
    if (value > 0 && value <= (currentProduct?.stock_quantity || 0)) {
      setQuantity(value)
    }
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (error || !currentProduct) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Product not found'}</p>
          <button
            onClick={() => navigate('/products')}
            className="text-primary-600 hover:text-primary-700"
          >
            Back to Products
          </button>
        </div>
      </div>
    )
  }

  const breadcrumbItems = [
    { name: 'Home', url: '/' },
    { name: 'Products', url: '/products' },
    { name: currentProduct.name, url: `/products/${currentProduct.id}` }
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <SEO 
        title={currentProduct.name}
        description={currentProduct.description || `Shop ${currentProduct.name} at Pasargad Prints. ${currentProduct.category_name} product with high quality and fast shipping.`}
        image={currentProduct.main_image}
        type="product"
      />
      <ProductStructuredData 
        product={{
          name: currentProduct.name,
          description: currentProduct.description || '',
          price: currentProduct.price,
          image: currentProduct.main_image || '',
          sku: currentProduct.sku,
          brand: currentProduct.brand,
          inStock: currentProduct.is_in_stock,
          rating: currentProduct.average_rating,
          reviewCount: currentProduct.review_count
        }}
      />
      <BreadcrumbStructuredData items={breadcrumbItems} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Images */}
        <div>
          <div className="bg-gray-100 rounded-lg overflow-hidden mb-4">
            <LazyImage
              src={selectedImage}
              alt={currentProduct.name}
              className="w-full h-96 lg:h-[500px] object-contain"
            />
          </div>
          
          {/* Image Gallery */}
          {currentProduct.images.length > 1 && (
            <div className="grid grid-cols-4 gap-2">
              {currentProduct.images.map((image) => (
                <button
                  key={image.id}
                  onClick={() => setSelectedImage(image.image)}
                  className={`border-2 rounded overflow-hidden ${
                    selectedImage === image.image ? 'border-primary-600' : 'border-gray-300'
                  }`}
                >
                  <img
                    src={image.image}
                    alt={image.alt_text || currentProduct.name}
                    className="w-full h-20 object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div>
          <h1 className="text-3xl font-bold mb-4">{currentProduct.name}</h1>
          
          <div className="flex items-center mb-4">
            <span className="text-2xl font-bold text-primary-600">${currentProduct.price}</span>
            <span className="ml-4 text-sm text-gray-600">SKU: {currentProduct.sku}</span>
          </div>

          {/* Rating */}
          {currentProduct.review_count > 0 && (
            <div className="flex items-center mb-4">
              <div className="flex text-yellow-400">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`w-5 h-5 ${i < Math.floor(currentProduct.average_rating) ? 'fill-current' : 'stroke-current fill-none'}`}
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                ))}
              </div>
              <span className="ml-2 text-gray-600">
                {currentProduct.average_rating} ({currentProduct.review_count} reviews)
              </span>
            </div>
          )}

          {/* Stock Status */}
          <div className="mb-6">
            {currentProduct.is_in_stock ? (
              <p className="text-green-600">✓ In Stock ({currentProduct.stock_quantity} available)</p>
            ) : (
              <p className="text-red-600">Out of Stock</p>
            )}
          </div>

          {/* Category */}
          <div className="mb-6">
            <span className="text-sm text-gray-600">Category: </span>
            <span className="text-sm font-medium">{currentProduct.category.name}</span>
          </div>

          {/* Description */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Description</h2>
            <p className="text-gray-700">{currentProduct.description}</p>
          </div>

          {/* Product Details */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Product Details</h2>
            <ul className="space-y-1 text-sm text-gray-700">
              <li><span className="font-medium">Material:</span> {currentProduct.material}</li>
              <li><span className="font-medium">Dimensions:</span> {currentProduct.dimensions}</li>
              <li><span className="font-medium">Weight:</span> {currentProduct.weight}g</li>
              <li><span className="font-medium">Print Time:</span> {currentProduct.print_time} minutes</li>
            </ul>
          </div>

          {/* Add to Cart Section */}
          {currentProduct.is_in_stock ? (
            <div className="flex items-center gap-4 mb-8">
              <div>
                <label htmlFor="quantity" className="sr-only">Quantity</label>
                <input
                  type="number"
                  id="quantity"
                  min="1"
                  max={currentProduct.stock_quantity}
                  value={quantity}
                  onChange={handleQuantityChange}
                  className="w-20 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <button
                onClick={handleAddToCart}
                className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-md font-semibold hover:bg-primary-700 transition-colors"
              >
                Add to Cart
              </button>
            </div>
          ) : (
            <div className="mb-8">
              <button
                disabled
                className="w-full bg-gray-300 text-gray-500 py-3 px-6 rounded-md font-semibold cursor-not-allowed"
              >
                Out of Stock
              </button>
              <p className="mt-2 text-sm text-gray-600">
                This product is currently unavailable. Please check back later.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Reviews Section */}
      <div className="mt-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Customer Reviews</h2>
          <button
            onClick={() => setShowReviewForm(!showReviewForm)}
            className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors"
          >
            Write a Review
          </button>
        </div>

        {currentProduct.reviews.length === 0 ? (
          <p className="text-gray-600">No reviews yet. Be the first to review this product!</p>
        ) : (
          <div className="space-y-4">
            {currentProduct.reviews.map((review) => (
              <div key={review.id} className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center mb-2">
                  <div className="flex text-yellow-400">
                    {[...Array(5)].map((_, i) => (
                      <svg
                        key={i}
                        className={`w-4 h-4 ${i < review.rating ? 'fill-current' : 'stroke-current fill-none'}`}
                        viewBox="0 0 24 24"
                      >
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                      </svg>
                    ))}
                  </div>
                  <span className="ml-2 font-medium">{review.user_name}</span>
                  <span className="ml-2 text-sm text-gray-500">
                    {new Date(review.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-gray-700">{review.review_text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProductDetailPage