import { useEffect, useState, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useSearchParams } from 'react-router-dom'
import type { AppDispatch, RootState } from '../store/index'
import { fetchProducts, fetchCategories, setFilters } from '../store/slices/productsSlice'
import ProductCard from '../components/ProductCard'
import AdvancedFilters from '../components/AdvancedFilters'
import LoadingSpinner from '../components/LoadingSpinner'
import { ProductGridSkeleton } from '../components/SkeletonLoader'
import MobileFilterPanel from '../components/MobileFilterPanel'

interface ActiveFilter {
  id: string
  label: string
  type: string
  value: any
}

const EnhancedProductsPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const [searchParams, setSearchParams] = useSearchParams()
  const { products, categories, isLoading, pagination } = useSelector((state: RootState) => state.products)
  const [showMobileFilters, setShowMobileFilters] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [activeFilters, setActiveFilters] = useState<ActiveFilter[]>([])

  useEffect(() => {
    dispatch(fetchCategories())
  }, [dispatch])

  const handleFiltersChange = useCallback((filters: any) => {
    const params: any = {}
    const newActiveFilters: ActiveFilter[] = []

    // Categories
    if (filters.categories.length > 0) {
      params.category = filters.categories.join(',')
      filters.categories.forEach((catId: number) => {
        const category = categories.find(c => c.id === catId)
        if (category) {
          newActiveFilters.push({
            id: `category-${catId}`,
            label: category.name,
            type: 'category',
            value: catId,
          })
        }
      })
    }

    // Price range
    if (filters.priceRange[0] > 0 || filters.priceRange[1] < 1000) {
      params.min_price = filters.priceRange[0]
      params.max_price = filters.priceRange[1]
      newActiveFilters.push({
        id: 'price',
        label: `$${filters.priceRange[0]} - $${filters.priceRange[1]}`,
        type: 'price',
        value: filters.priceRange,
      })
    }

    // Rating
    if (filters.rating > 0) {
      params.min_rating = filters.rating
      newActiveFilters.push({
        id: 'rating',
        label: `${filters.rating}+ stars`,
        type: 'rating',
        value: filters.rating,
      })
    }

    // Other filters
    if (filters.inStock) {
      params.in_stock = 'true'
      newActiveFilters.push({
        id: 'in_stock',
        label: 'In Stock',
        type: 'stock',
        value: true,
      })
    }

    if (filters.featured) {
      params.is_featured = 'true'
      newActiveFilters.push({
        id: 'featured',
        label: 'Featured',
        type: 'featured',
        value: true,
      })
    }

    if (filters.search) {
      params.search = filters.search
      newActiveFilters.push({
        id: 'search',
        label: `Search: "${filters.search}"`,
        type: 'search',
        value: filters.search,
      })
    }

    if (filters.sortBy) {
      params.ordering = filters.sortBy
    }

    setActiveFilters(newActiveFilters)
    dispatch(setFilters(params))
    dispatch(fetchProducts(params))

    // Update URL
    const newSearchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value) newSearchParams.set(key, value.toString())
    })
    setSearchParams(newSearchParams)
  }, [categories, dispatch, setSearchParams])

  const removeActiveFilter = (filterId: string) => {
    const filter = activeFilters.find(f => f.id === filterId)
    if (!filter) return

    // This would need to be implemented based on your filter logic
    // For now, just refresh without that filter
    const remainingFilters = activeFilters.filter(f => f.id !== filterId)
    // Convert back to filter format and apply
  }

  const initialFilters = {
    categories: searchParams.get('category')?.split(',').map(Number).filter(Boolean) || [],
    priceRange: [
      parseInt(searchParams.get('min_price') || '0'),
      parseInt(searchParams.get('max_price') || '1000'),
    ] as [number, number],
    rating: parseInt(searchParams.get('min_rating') || '0'),
    inStock: searchParams.get('in_stock') === 'true',
    featured: searchParams.get('is_featured') === 'true',
    sortBy: searchParams.get('ordering') || '-created_at',
    search: searchParams.get('search') || '',
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Our Products</h1>
        <p className="text-gray-600">Discover our collection of high-quality 3D printed products</p>
      </div>

      {/* Active Filters Bar */}
      {activeFilters.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-700">Active Filters</h3>
            <button
              onClick={() => handleFiltersChange({
                categories: [],
                priceRange: [0, 1000],
                rating: 0,
                inStock: false,
                featured: false,
                sortBy: '-created_at',
                search: '',
              })}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              Clear All
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {activeFilters.map(filter => (
              <span
                key={filter.id}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-white border border-gray-300"
              >
                {filter.label}
                <button
                  onClick={() => removeActiveFilter(filter.id)}
                  className="ml-2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Desktop Filters Sidebar */}
        <aside className="hidden lg:block lg:w-80">
          <AdvancedFilters
            categories={categories}
            onFiltersChange={handleFiltersChange}
            initialFilters={initialFilters}
            productCount={products.length}
          />
        </aside>

        {/* Products Section */}
        <div className="flex-1">
          {/* Toolbar */}
          <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4">
              <p className="text-gray-600">
                {products.length} {products.length === 1 ? 'product' : 'products'} found
              </p>
              
              {/* View Mode Toggle - Desktop Only */}
              <div className="hidden sm:flex items-center gap-2 border border-gray-300 rounded-md p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-1.5 rounded ${
                    viewMode === 'grid' 
                      ? 'bg-primary-100 text-primary-600' 
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                  title="Grid view"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-1.5 rounded ${
                    viewMode === 'list' 
                      ? 'bg-primary-100 text-primary-600' 
                      : 'text-gray-400 hover:text-gray-600'
                  }`}
                  title="List view"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Mobile Filter Button */}
            <button
              onClick={() => setShowMobileFilters(true)}
              className="lg:hidden flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filters
              {activeFilters.length > 0 && (
                <span className="bg-primary-600 text-white text-xs rounded-full px-2 py-0.5">
                  {activeFilters.length}
                </span>
              )}
            </button>
          </div>

          {/* Products Display */}
          {isLoading ? (
            <ProductGridSkeleton />
          ) : (
            <>
              {products.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-lg shadow-sm">
                  <svg
                    className="w-16 h-16 text-gray-400 mx-auto mb-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No products found</h3>
                  <p className="text-gray-500 mb-6">Try adjusting your filters to find what you're looking for.</p>
                  <button
                    onClick={() => handleFiltersChange({
                      categories: [],
                      priceRange: [0, 1000],
                      rating: 0,
                      inStock: false,
                      featured: false,
                      sortBy: '-created_at',
                      search: '',
                    })}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Clear all filters
                  </button>
                </div>
              ) : (
                <div className={viewMode === 'grid' 
                  ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6" 
                  : "space-y-4"
                }>
                  {products.map((product, index) => (
                    <div
                      key={product.id}
                      className="animate-fade-in"
                      style={{ animationDelay: `${index * 0.05}s` }}
                    >
                      <ProductCard product={product} />
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Pagination could go here */}
        </div>
      </div>

      {/* Mobile Filter Panel */}
      <MobileFilterPanel
        isOpen={showMobileFilters}
        onClose={() => setShowMobileFilters(false)}
      >
        <div className="h-full overflow-y-auto">
          <AdvancedFilters
            categories={categories}
            onFiltersChange={(filters) => {
              handleFiltersChange(filters)
              setShowMobileFilters(false)
            }}
            initialFilters={initialFilters}
            productCount={products.length}
          />
        </div>
      </MobileFilterPanel>
    </div>
  )
}

export default EnhancedProductsPage