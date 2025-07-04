import { useState, useEffect } from 'react'
import type { Category } from '../types'

interface FilterState {
  categories: number[]
  priceRange: [number, number]
  rating: number
  inStock: boolean
  featured: boolean
  sortBy: string
  search: string
}

interface AdvancedFiltersProps {
  categories: Category[]
  onFiltersChange: (filters: FilterState) => void
  initialFilters?: Partial<FilterState>
  productCount: number
}

const AdvancedFilters = ({ categories, onFiltersChange, initialFilters, productCount }: AdvancedFiltersProps) => {
  const [filters, setFilters] = useState<FilterState>({
    categories: [],
    priceRange: [0, 1000],
    rating: 0,
    inStock: false,
    featured: false,
    sortBy: '-created_at',
    search: '',
    ...initialFilters,
  })

  const [priceInput, setPriceInput] = useState({
    min: filters.priceRange[0].toString(),
    max: filters.priceRange[1].toString(),
  })

  const [isExpanded, setIsExpanded] = useState({
    categories: true,
    price: true,
    rating: true,
    other: true,
  })

  useEffect(() => {
    onFiltersChange(filters)
  }, [filters, onFiltersChange])

  const handleCategoryToggle = (categoryId: number) => {
    setFilters(prev => ({
      ...prev,
      categories: prev.categories.includes(categoryId)
        ? prev.categories.filter(id => id !== categoryId)
        : [...prev.categories, categoryId],
    }))
  }

  const handlePriceChange = (type: 'min' | 'max', value: string) => {
    setPriceInput(prev => ({ ...prev, [type]: value }))
  }

  const handlePriceBlur = () => {
    const min = Math.max(0, parseInt(priceInput.min) || 0)
    const max = Math.max(min, parseInt(priceInput.max) || 1000)
    setFilters(prev => ({ ...prev, priceRange: [min, max] }))
    setPriceInput({ min: min.toString(), max: max.toString() })
  }

  const handleRatingChange = (rating: number) => {
    setFilters(prev => ({ ...prev, rating: prev.rating === rating ? 0 : rating }))
  }

  const handleCheckboxChange = (field: 'inStock' | 'featured') => {
    setFilters(prev => ({ ...prev, [field]: !prev[field] }))
  }

  const handleSortChange = (sortBy: string) => {
    setFilters(prev => ({ ...prev, sortBy }))
  }

  const handleSearchChange = (search: string) => {
    setFilters(prev => ({ ...prev, search }))
  }

  const clearFilters = () => {
    const defaultFilters: FilterState = {
      categories: [],
      priceRange: [0, 1000],
      rating: 0,
      inStock: false,
      featured: false,
      sortBy: '-created_at',
      search: '',
    }
    setFilters(defaultFilters)
    setPriceInput({ min: '0', max: '1000' })
  }

  const activeFilterCount = 
    filters.categories.length +
    (filters.priceRange[0] > 0 || filters.priceRange[1] < 1000 ? 1 : 0) +
    (filters.rating > 0 ? 1 : 0) +
    (filters.inStock ? 1 : 0) +
    (filters.featured ? 1 : 0) +
    (filters.search ? 1 : 0)

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          {activeFilterCount > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              {activeFilterCount} active • {productCount} products
            </p>
          )}
        </div>
        {activeFilterCount > 0 && (
          <button
            onClick={clearFilters}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search products..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <svg
            className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {/* Categories */}
      <div className="mb-6">
        <button
          onClick={() => setIsExpanded(prev => ({ ...prev, categories: !prev.categories }))}
          className="flex items-center justify-between w-full py-2 text-left"
        >
          <h3 className="font-medium text-gray-900">Categories</h3>
          <svg
            className={`w-5 h-5 text-gray-500 transform transition-transform ${
              isExpanded.categories ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isExpanded.categories && (
          <div className="mt-3 space-y-2">
            {categories.map(category => (
              <label key={category.id} className="flex items-center group cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.categories.includes(category.id)}
                  onChange={() => handleCategoryToggle(category.id)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-sm text-gray-700 group-hover:text-gray-900 flex-1">
                  {category.name}
                </span>
                <span className="text-xs text-gray-500">({category.products_count})</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Price Range */}
      <div className="mb-6">
        <button
          onClick={() => setIsExpanded(prev => ({ ...prev, price: !prev.price }))}
          className="flex items-center justify-between w-full py-2 text-left"
        >
          <h3 className="font-medium text-gray-900">Price Range</h3>
          <svg
            className={`w-5 h-5 text-gray-500 transform transition-transform ${
              isExpanded.price ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isExpanded.price && (
          <div className="mt-3">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="text-xs text-gray-600">Min</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    value={priceInput.min}
                    onChange={(e) => handlePriceChange('min', e.target.value)}
                    onBlur={handlePriceBlur}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
              <span className="text-gray-400 mt-6">—</span>
              <div className="flex-1">
                <label className="text-xs text-gray-600">Max</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    value={priceInput.max}
                    onChange={(e) => handlePriceChange('max', e.target.value)}
                    onBlur={handlePriceBlur}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Rating */}
      <div className="mb-6">
        <button
          onClick={() => setIsExpanded(prev => ({ ...prev, rating: !prev.rating }))}
          className="flex items-center justify-between w-full py-2 text-left"
        >
          <h3 className="font-medium text-gray-900">Rating</h3>
          <svg
            className={`w-5 h-5 text-gray-500 transform transition-transform ${
              isExpanded.rating ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isExpanded.rating && (
          <div className="mt-3 space-y-2">
            {[4, 3, 2, 1].map(rating => (
              <button
                key={rating}
                onClick={() => handleRatingChange(rating)}
                className={`flex items-center w-full py-2 px-3 rounded-md transition-colors ${
                  filters.rating === rating
                    ? 'bg-primary-50 text-primary-700'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex text-yellow-400">
                  {[...Array(5)].map((_, i) => (
                    <svg
                      key={i}
                      className={`w-4 h-4 ${i < rating ? 'fill-current' : 'stroke-current fill-none'}`}
                      viewBox="0 0 24 24"
                    >
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  ))}
                </div>
                <span className="ml-2 text-sm text-gray-700">& up</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Other Filters */}
      <div className="mb-6">
        <button
          onClick={() => setIsExpanded(prev => ({ ...prev, other: !prev.other }))}
          className="flex items-center justify-between w-full py-2 text-left"
        >
          <h3 className="font-medium text-gray-900">Other Filters</h3>
          <svg
            className={`w-5 h-5 text-gray-500 transform transition-transform ${
              isExpanded.other ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isExpanded.other && (
          <div className="mt-3 space-y-3">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={filters.inStock}
                onChange={() => handleCheckboxChange('inStock')}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-3 text-sm text-gray-700">In Stock Only</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={filters.featured}
                onChange={() => handleCheckboxChange('featured')}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-3 text-sm text-gray-700">Featured Products</span>
            </label>
          </div>
        )}
      </div>

      {/* Sort By */}
      <div className="border-t pt-6">
        <label className="block text-sm font-medium text-gray-900 mb-3">Sort By</label>
        <select
          value={filters.sortBy}
          onChange={(e) => handleSortChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="-created_at">Newest First</option>
          <option value="created_at">Oldest First</option>
          <option value="price">Price: Low to High</option>
          <option value="-price">Price: High to Low</option>
          <option value="name">Name: A to Z</option>
          <option value="-name">Name: Z to A</option>
          <option value="-average_rating">Highest Rated</option>
        </select>
      </div>
    </div>
  )
}

export default AdvancedFilters