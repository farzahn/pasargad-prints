import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import type { AppDispatch } from '../store/index'
import { addToCart } from '../store/slices/cartSlice'
import WishlistButton from './WishlistButton'
import CompareButton from './CompareButton'
import ProductQuickView from './ProductQuickView'
import LazyImage from './LazyImage'
import type { Product } from '../types'

interface ProductCardProps {
  product: Product
}

const ProductCard = ({ product }: ProductCardProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const [showQuickView, setShowQuickView] = useState(false)

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault()
    
    // Check if product is in stock
    if (!product.is_in_stock) {
      alert('This product is currently out of stock')
      return
    }
    
    dispatch(addToCart({ product_id: product.id, quantity: 1 }))
  }

  const handleQuickView = (e: React.MouseEvent) => {
    e.preventDefault()
    setShowQuickView(true)
  }

  return (
    <>
      <Link to={`/products/${product.id}`} className="group">
        <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-xl transition-shadow">
          {/* Product Image */}
          <div className="aspect-square bg-gray-100 relative overflow-hidden group">
          {product.main_image ? (
            <LazyImage
              src={product.main_image}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          )}
          
          {/* Stock Badge */}
          {!product.is_in_stock && (
            <div className="absolute bottom-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm">
              Out of Stock
            </div>
          )}
          
          
          {/* Action Buttons */}
          <div className="absolute top-2 right-2 flex flex-col gap-2">
            <WishlistButton product={product} size="sm" />
            <CompareButton product={product} size="sm" />
          </div>
          
          {/* Quick View Button - shows on hover */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300 flex items-center justify-center">
            <button
              onClick={handleQuickView}
              className="bg-white text-gray-900 px-4 py-2 rounded-md font-medium opacity-0 group-hover:opacity-100 transform scale-95 group-hover:scale-100 transition-all duration-300 shadow-lg hover:shadow-xl"
            >
              Quick View
            </button>
          </div>
        </div>

        {/* Product Info */}
        <div className="p-4">
          <h3 className="font-semibold text-lg mb-1 group-hover:text-primary-600 transition-colors">
            {product.name}
          </h3>
          
          <p className="text-sm text-gray-600 mb-2">{product.category_name}</p>
          
          {/* Rating */}
          {product.review_count > 0 && (
            <div className="flex items-center mb-2">
              <div className="flex text-yellow-400">
                {[...Array(5)].map((_, i) => (
                  <svg
                    key={i}
                    className={`w-4 h-4 ${i < Math.floor(product.average_rating) ? 'fill-current' : 'stroke-current fill-none'}`}
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                ))}
              </div>
              <span className="text-sm text-gray-600 ml-1">({product.review_count})</span>
            </div>
          )}
          
          {/* Price and Add to Cart */}
          <div className="flex items-center justify-between mt-3">
            <span className="text-xl font-bold text-primary-600">${product.price}</span>
            {product.is_in_stock && (
              <button
                onClick={handleAddToCart}
                className="bg-primary-600 text-white p-2 rounded-md hover:bg-primary-700 transition-colors"
                title="Add to Cart"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </Link>
    
    {/* Quick View Modal */}
    <ProductQuickView
      productId={product.id}
      isOpen={showQuickView}
      onClose={() => setShowQuickView(false)}
    />
    </>
  )
}

export default ProductCard