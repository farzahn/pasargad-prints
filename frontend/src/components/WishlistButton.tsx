import { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { AppDispatch, RootState } from '../store/index'
import { addToWishlist, removeFromWishlist, selectIsItemInWishlist } from '../store/slices/wishlistSlice'
import type { Product } from '../types'

interface WishlistButtonProps {
  product: Product
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
}

const WishlistButton = ({ product, size = 'md', showText = false, className = '' }: WishlistButtonProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const isInWishlist = useSelector((state: RootState) => selectIsItemInWishlist(state, product.id))
  const wishlistItems = useSelector((state: RootState) => state.wishlist.wishlist?.items || [])
  const [isAnimating, setIsAnimating] = useState(false)
  const [localIsInWishlist, setLocalIsInWishlist] = useState(isInWishlist)

  useEffect(() => {
    setLocalIsInWishlist(isInWishlist)
  }, [isInWishlist])

  const handleToggleWishlist = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    setIsAnimating(true)
    setLocalIsInWishlist(!localIsInWishlist)

    try {
      if (isInWishlist) {
        const wishlistItem = wishlistItems.find(item => item.product.id === product.id)
        if (wishlistItem) {
          await dispatch(removeFromWishlist({ item_id: wishlistItem.id })).unwrap()
        }
      } else {
        await dispatch(addToWishlist({ product_id: product.id })).unwrap()
      }
    } catch {
      // Revert local state on error
      setLocalIsInWishlist(isInWishlist)
    } finally {
      setTimeout(() => setIsAnimating(false), 600)
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

  return (
    <button
      onClick={handleToggleWishlist}
      className={`
        ${showText ? 'flex items-center gap-2 px-4 py-2' : `${sizeClasses[size]} flex items-center justify-center`}
        ${localIsInWishlist ? 'text-red-500' : 'text-gray-400 hover:text-gray-600'}
        bg-white rounded-lg shadow-sm hover:shadow-md
        transition-all duration-200 
        focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50
        ${className}
      `}
      title={localIsInWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
    >
      <svg
        className={`${iconSizeClasses[size]} ${isAnimating ? 'animate-heartbeat' : ''} transition-all duration-200`}
        fill={localIsInWishlist ? 'currentColor' : 'none'}
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
        />
      </svg>
      {showText && (
        <span className="font-medium">
          {localIsInWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}
        </span>
      )}
    </button>
  )
}

export default WishlistButton