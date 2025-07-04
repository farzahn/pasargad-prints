import { useState, useEffect } from 'react'
import { useLazyLoad } from '../hooks/useLazyLoad'
import { getOptimizedImageUrl, getResponsiveImageSrcSet } from '../utils/cdn'

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string
  alt: string
  placeholder?: string
  className?: string
  onError?: () => void
  optimizationOptions?: {
    width?: number
    height?: number
    quality?: number
    format?: 'webp' | 'avif' | 'jpeg' | 'png'
  }
  responsive?: boolean
  responsiveSizes?: number[]
}

const LazyImage = ({ 
  src, 
  alt, 
  placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"%3E%3Crect width="400" height="400" fill="%23f3f4f6"/%3E%3C/svg%3E',
  className = '',
  onError,
  optimizationOptions,
  responsive = false,
  responsiveSizes,
  ...props 
}: LazyImageProps) => {
  const [imageSrc, setImageSrc] = useState(placeholder)
  const [isIntersecting, imageRef] = useLazyLoad<HTMLDivElement>()
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)

  // Generate optimized image URLs
  const optimizedSrc = getOptimizedImageUrl(src, optimizationOptions)
  const srcSet = responsive ? getResponsiveImageSrcSet(src, responsiveSizes, optimizationOptions) : undefined

  useEffect(() => {
    if (isIntersecting && src && !hasError) {
      const img = new Image()
      img.src = optimizedSrc
      
      img.onload = () => {
        setImageSrc(optimizedSrc)
        setIsLoaded(true)
      }
      
      img.onerror = () => {
        setHasError(true)
        setIsLoaded(true)
        onError?.()
      }
    }
  }, [isIntersecting, src, hasError, onError, optimizedSrc])

  if (hasError) {
    return (
      <div 
        ref={imageRef}
        className={`flex items-center justify-center bg-gray-100 ${className}`}
      >
        <svg 
          className="w-16 h-16 text-gray-400" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
          />
        </svg>
      </div>
    )
  }

  return (
    <div ref={imageRef} className="relative">
      <img
        src={imageSrc}
        srcSet={srcSet}
        alt={alt}
        className={`${className} ${!isLoaded ? 'blur-sm' : ''} transition-all duration-300`}
        loading="lazy"
        {...props}
      />
      {!isLoaded && (
        <div className="absolute inset-0 bg-gray-100 animate-pulse" />
      )}
    </div>
  )
}

export default LazyImage