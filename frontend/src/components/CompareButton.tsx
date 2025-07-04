import { useSelector, useDispatch } from 'react-redux'
import type { AppDispatch, RootState } from '../store/index'
import {
  addToComparison,
  removeFromComparison,
  selectIsInComparison,
  selectCanAddToComparison,
} from '../store/slices/comparisonSlice'
import type { Product } from '../types'

interface CompareButtonProps {
  product: Product
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
}

const CompareButton = ({ product, size = 'md', showText = false, className = '' }: CompareButtonProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const isInComparison = useSelector((state: RootState) => selectIsInComparison(state, product.id))
  const canAddToComparison = useSelector(selectCanAddToComparison)
  const comparisonCount = useSelector((state: RootState) => state.comparison.products.length)

  const handleToggleComparison = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (isInComparison) {
      dispatch(removeFromComparison(product.id))
    } else if (canAddToComparison) {
      dispatch(addToComparison(product))
    }
  }

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12'
  }

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  }

  const isDisabled = !isInComparison && !canAddToComparison

  return (
    <button
      onClick={handleToggleComparison}
      disabled={isDisabled}
      className={`
        ${showText ? 'flex items-center gap-2 px-4 py-2' : `${sizeClasses[size]} flex items-center justify-center`}
        ${isInComparison ? 'text-primary-600 bg-primary-50' : 'text-gray-600 bg-white'}
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-md'}
        rounded-lg shadow-sm transition-all duration-200 
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50
        ${className}
      `}
      title={
        isInComparison
          ? 'Remove from comparison'
          : isDisabled
          ? `Maximum ${comparisonCount} products can be compared`
          : 'Add to comparison'
      }
    >
      <svg
        className={`${iconSizeClasses[size]} transition-all duration-200`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      {showText && (
        <span className="font-medium">
          {isInComparison ? 'Remove from Compare' : 'Compare'}
        </span>
      )}
    </button>
  )
}

export default CompareButton