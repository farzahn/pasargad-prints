import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { RootState, AppDispatch } from '../../store'
import { fetchAdminProducts, updateProductStock } from '../../store/slices/adminSlice'
import LoadingSpinner from '../../components/LoadingSpinner'
import type { Product } from '../../types'

export default function ProductsPage() {
  const dispatch = useDispatch<AppDispatch>()
  const { products, productsCount, isLoading } = useSelector((state: RootState) => state.admin)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [stockQuantity, setStockQuantity] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    dispatch(fetchAdminProducts())
  }, [dispatch])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    dispatch(fetchAdminProducts({ search: searchTerm }))
  }

  const handleStockUpdate = async (productId: number) => {
    const quantity = parseInt(stockQuantity)
    if (!isNaN(quantity) && quantity >= 0) {
      await dispatch(updateProductStock({ id: productId, stock_quantity: quantity }))
      setStockQuantity('')
      setSelectedProduct(null)
      dispatch(fetchAdminProducts())
    }
  }

  if (isLoading && products.length === 0) {
    return <LoadingSpinner />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products Management</h1>
          <p className="text-gray-600">Manage your product inventory</p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center gap-4">
          <span className="text-sm text-gray-500">Total Products: {productsCount}</span>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Add Product
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search products..."
            className="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Search
          </button>
        </form>
      </div>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {products.map((product) => (
          <div key={product.id} className="bg-white rounded-lg shadow overflow-hidden">
            {product.main_image && (
              <img
                src={product.main_image}
                alt={product.name}
                className="w-full h-48 object-cover"
              />
            )}
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 mb-1">{product.name}</h3>
              <p className="text-sm text-gray-500 mb-2">{product.category_name}</p>
              <p className="text-lg font-bold text-blue-600 mb-3">${product.price}</p>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Stock:</span>
                  <span className={`font-medium ${product.is_in_stock ? 'text-green-600' : 'text-red-600'}`}>
                    {product.is_in_stock ? 'In Stock' : 'Out of Stock'}
                  </span>
                </div>
                
                {product.is_featured && (
                  <div className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-center">
                    Featured
                  </div>
                )}
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Rating:</span>
                  <div className="flex items-center">
                    <span className="text-yellow-500">★</span>
                    <span className="ml-1">{product.average_rating.toFixed(1)}</span>
                    <span className="text-gray-400 ml-1">({product.review_count})</span>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                <button
                  onClick={() => setSelectedProduct(product)}
                  className="w-full px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
                >
                  Update Stock
                </button>
                <button
                  className="w-full px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
                >
                  Edit Product
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Update Stock Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setSelectedProduct(null)}
            />
            <div className="relative bg-white rounded-lg max-w-md w-full p-6">
              <h2 className="text-xl font-semibold mb-4">Update Stock Quantity</h2>
              <p className="text-gray-600 mb-4">Product: {selectedProduct.name}</p>
              
              <input
                type="number"
                value={stockQuantity}
                onChange={(e) => setStockQuantity(e.target.value)}
                placeholder="Enter new stock quantity"
                min="0"
                className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              />
              
              <div className="flex gap-3">
                <button
                  onClick={() => handleStockUpdate(selectedProduct.id)}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
                >
                  Update Stock
                </button>
                <button
                  onClick={() => {
                    setSelectedProduct(null)
                    setStockQuantity('')
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Product Modal (placeholder for now) */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={() => setShowAddModal(false)}
            />
            <div className="relative bg-white rounded-lg max-w-2xl w-full p-6">
              <h2 className="text-xl font-semibold mb-4">Add New Product</h2>
              <p className="text-gray-600 mb-4">Product creation form will be implemented here.</p>
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}