import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useSearchParams } from 'react-router-dom'
import type { AppDispatch, RootState } from '../store/index'
import { fetchProducts, fetchCategories, setFilters } from '../store/slices/productsSlice'
import ProductCard from '../components/ProductCard'
import LoadingSpinner from '../components/LoadingSpinner'

const ProductsPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const [searchParams, setSearchParams] = useSearchParams()
  const { products, categories, isLoading, filters } = useSelector((state: RootState) => state.products)
  
  const [localFilters, setLocalFilters] = useState({
    category: searchParams.get('category') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    in_stock: searchParams.get('in_stock') === 'true',
    search: searchParams.get('search') || '',
    ordering: searchParams.get('ordering') || '-created_at',
  })

  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    dispatch(fetchCategories())
  }, [dispatch])

  useEffect(() => {
    const params: any = {}
    if (localFilters.category) params.category = localFilters.category
    if (localFilters.min_price) params.min_price = localFilters.min_price
    if (localFilters.max_price) params.max_price = localFilters.max_price
    if (localFilters.in_stock) params.in_stock = 'true'
    if (localFilters.search) params.search = localFilters.search
    if (localFilters.ordering) params.ordering = localFilters.ordering

    dispatch(setFilters(params))
    dispatch(fetchProducts(params))
    
    // Update URL
    const newSearchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value) newSearchParams.set(key, value.toString())
    })
    setSearchParams(newSearchParams)
  }, [localFilters, dispatch, setSearchParams])

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    
    setLocalFilters(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const clearFilters = () => {
    setLocalFilters({
      category: '',
      min_price: '',
      max_price: '',
      in_stock: false,
      search: '',
      ordering: '-created_at',
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Our Products</h1>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Filters Sidebar */}
        <aside className={`lg:w-64 ${showFilters ? 'block' : 'hidden lg:block'}`}>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Filters</h2>
              <button
                onClick={clearFilters}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Clear All
              </button>
            </div>

            {/* Search */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input
                type="text"
                name="search"
                value={localFilters.search}
                onChange={handleFilterChange}
                placeholder="Search products..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Category Filter */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                name="category"
                value={localFilters.category}
                onChange={handleFilterChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Categories</option>
                {categories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name} ({category.products_count})
                  </option>
                ))}
              </select>
            </div>

            {/* Price Range */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Price Range</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  name="min_price"
                  value={localFilters.min_price}
                  onChange={handleFilterChange}
                  placeholder="Min"
                  className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
                <input
                  type="number"
                  name="max_price"
                  value={localFilters.max_price}
                  onChange={handleFilterChange}
                  placeholder="Max"
                  className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* In Stock Filter */}
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="in_stock"
                  checked={localFilters.in_stock}
                  onChange={handleFilterChange}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">In Stock Only</span>
              </label>
            </div>

            {/* Sort Order */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
              <select
                name="ordering"
                value={localFilters.ordering}
                onChange={handleFilterChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="-created_at">Newest First</option>
                <option value="created_at">Oldest First</option>
                <option value="price">Price: Low to High</option>
                <option value="-price">Price: High to Low</option>
                <option value="name">Name: A to Z</option>
                <option value="-name">Name: Z to A</option>
              </select>
            </div>
          </div>
        </aside>

        {/* Products Grid */}
        <div className="flex-1">
          {/* Mobile Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="lg:hidden mb-4 bg-primary-600 text-white px-4 py-2 rounded-md"
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>

          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <>
              {products.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-lg">No products found matching your criteria.</p>
                  <button
                    onClick={clearFilters}
                    className="mt-4 text-primary-600 hover:text-primary-700"
                  >
                    Clear filters
                  </button>
                </div>
              ) : (
                <>
                  <p className="text-gray-600 mb-4">{products.length} products found</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {products.map(product => (
                      <ProductCard key={product.id} product={product} />
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProductsPage