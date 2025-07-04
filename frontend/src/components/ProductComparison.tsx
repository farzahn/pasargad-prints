import { useSelector, useDispatch } from 'react-redux'
import { Link } from 'react-router-dom'
import type { AppDispatch, RootState } from '../store/index'
import {
  selectComparisonProducts,
  selectIsComparisonOpen,
  removeFromComparison,
  clearComparison,
  setComparisonPanelOpen,
} from '../store/slices/comparisonSlice'
import { addToCart } from '../store/slices/cartSlice'
import WishlistButton from './WishlistButton'

const ProductComparison = () => {
  const dispatch = useDispatch<AppDispatch>()
  const products = useSelector(selectComparisonProducts)
  const isOpen = useSelector(selectIsComparisonOpen)

  if (!isOpen || products.length === 0) return null

  const handleAddToCart = (productId: number) => {
    dispatch(addToCart({ product_id: productId, quantity: 1 }))
  }

  const handleRemove = (productId: number) => {
    dispatch(removeFromComparison(productId))
  }

  const handleClear = () => {
    dispatch(clearComparison())
  }

  const handleClose = () => {
    dispatch(setComparisonPanelOpen(false))
  }

  // Get all unique attributes for comparison
  const attributes = [
    { key: 'price', label: 'Price', format: (val: any) => `$${val}` },
    { key: 'category_name', label: 'Category' },
    { key: 'average_rating', label: 'Rating', format: (val: any) => `${val.toFixed(1)} ★` },
    { key: 'review_count', label: 'Reviews' },
    { key: 'is_in_stock', label: 'Availability', format: (val: any) => val ? 'In Stock' : 'Out of Stock' },
  ]

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white shadow-2xl z-40 transform transition-transform duration-300 animate-slide-up">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Compare Products ({products.length})
          </h2>
          <div className="flex items-center gap-4">
            <button
              onClick={handleClear}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Clear All
            </button>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full">
            {/* Product Images and Names */}
            <thead>
              <tr>
                <th className="px-4 py-4 text-left text-sm font-medium text-gray-700 bg-gray-50">
                  Product
                </th>
                {products.map(product => (
                  <th key={product.id} className="px-4 py-4 bg-gray-50">
                    <div className="relative">
                      <button
                        onClick={() => handleRemove(product.id)}
                        className="absolute -top-2 -right-2 bg-white rounded-full p-1 shadow-md hover:shadow-lg z-10"
                      >
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                      <Link to={`/products/${product.id}`} className="block">
                        <div className="aspect-square w-32 mx-auto mb-2 bg-gray-100 rounded-lg overflow-hidden">
                          {product.main_image ? (
                            <img
                              src={product.main_image}
                              alt={product.name}
                              className="w-full h-full object-cover hover:scale-105 transition-transform"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <h3 className="text-sm font-medium text-gray-900 text-center hover:text-primary-600 transition-colors">
                          {product.name}
                        </h3>
                      </Link>
                    </div>
                  </th>
                ))}
                {/* Empty columns for less than 4 products */}
                {[...Array(4 - products.length)].map((_, index) => (
                  <th key={`empty-${index}`} className="px-4 py-4 bg-gray-50">
                    <div className="w-32 h-32 mx-auto border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                      <span className="text-sm text-gray-400">Add Product</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>

            {/* Comparison Attributes */}
            <tbody className="divide-y divide-gray-200">
              {attributes.map((attr, index) => (
                <tr key={attr.key} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-700">
                    {attr.label}
                  </td>
                  {products.map(product => (
                    <td key={product.id} className="px-4 py-3 text-sm text-center text-gray-900">
                      {attr.format
                        ? attr.format((product as any)[attr.key])
                        : (product as any)[attr.key]
                      }
                    </td>
                  ))}
                  {[...Array(4 - products.length)].map((_, index) => (
                    <td key={`empty-${index}`} className="px-4 py-3"></td>
                  ))}
                </tr>
              ))}

              {/* Actions Row */}
              <tr>
                <td className="px-4 py-4 text-sm font-medium text-gray-700">Actions</td>
                {products.map(product => (
                  <td key={product.id} className="px-4 py-4 text-center">
                    <div className="flex flex-col gap-2">
                      {product.is_in_stock ? (
                        <button
                          onClick={() => handleAddToCart(product.id)}
                          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 transition-colors text-sm font-medium"
                        >
                          Add to Cart
                        </button>
                      ) : (
                        <button
                          disabled
                          className="w-full bg-gray-300 text-gray-500 py-2 px-4 rounded-md cursor-not-allowed text-sm font-medium"
                        >
                          Out of Stock
                        </button>
                      )}
                      <WishlistButton product={product} showText size="sm" className="w-full justify-center" />
                    </div>
                  </td>
                ))}
                {[...Array(4 - products.length)].map((_, index) => (
                  <td key={`empty-${index}`} className="px-4 py-4"></td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ProductComparison