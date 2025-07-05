import { useState, useEffect, useRef, useCallback } from 'react'
import { useLazyLoad } from '../hooks/useLazyLoad'
import { getSmartOptimizedImageUrl, getResponsiveImageSrcSet, getBrowserCapabilities } from '../utils/cdn'

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string
  alt: string
  placeholder?: string
  className?: string
  onError?: () => void
  onLoad?: () => void
  optimizationOptions?: {
    width?: number
    height?: number
    quality?: number
    format?: 'webp' | 'avif' | 'jpeg' | 'png' | 'auto'
    blur?: number
    progressive?: boolean
  }
  responsive?: boolean
  responsiveSizes?: number[]
  priority?: boolean
  aspectRatio?: string
  blurDataURL?: string
  enableLQIP?: boolean // Low Quality Image Placeholder
  sizes?: string
  crossOrigin?: 'anonymous' | 'use-credentials'
  referrerPolicy?: ReferrerPolicy
  fetchPriority?: 'high' | 'low' | 'auto'
}

const LazyImage = ({ 
  src, 
  alt, 
  placeholder,
  className = '',
  onError,
  onLoad,
  optimizationOptions = {},
  responsive = false,
  responsiveSizes = [320, 640, 768, 1024, 1280, 1536],
  priority = false,
  aspectRatio,
  blurDataURL,
  enableLQIP = true,
  sizes = '100vw',
  crossOrigin,
  referrerPolicy,
  fetchPriority = 'auto',
  ...props 
}: LazyImageProps) => {
  const [imageSrc, setImageSrc] = useState<string>('')
  const [isIntersecting, imageRef] = useLazyLoad<HTMLDivElement>({
    threshold: 0.1,
    rootMargin: priority ? '0px' : '200px'
  })
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [loadStarted, setLoadStarted] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  const preloadRef = useRef<HTMLLinkElement | null>(null)

  // Browser capabilities
  const capabilities = getBrowserCapabilities()

  // Generate optimized image URLs with smart format detection
  const optimizedOptions = {
    format: 'auto' as const,
    quality: 85,
    progressive: true,
    ...optimizationOptions
  }

  const optimizedSrc = getSmartOptimizedImageUrl(src, optimizedOptions)
  const srcSet = responsive ? getResponsiveImageSrcSet(src, responsiveSizes, optimizedOptions) : undefined

  // Generate LQIP (Low Quality Image Placeholder) URL
  const lqipSrc = enableLQIP ? getSmartOptimizedImageUrl(src, {
    ...optimizedOptions,
    quality: 20,
    width: 40,
    blur: 5
  }) : undefined

  // Default placeholder SVG
  const defaultPlaceholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"%3E%3Crect width="400" height="400" fill="%23f3f4f6"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23a1a1aa"%3ELoading...%3C/text%3E%3C/svg%3E'

  const currentPlaceholder = blurDataURL || lqipSrc || placeholder || defaultPlaceholder

  // Handle image preloading for priority images
  useEffect(() => {
    if (priority && optimizedSrc) {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'image'
      link.href = optimizedSrc
      if (srcSet) link.imageSrcset = srcSet
      if (sizes) link.imageSizes = sizes
      if (crossOrigin) link.crossOrigin = crossOrigin
      
      document.head.appendChild(link)
      preloadRef.current = link

      return () => {
        if (preloadRef.current) {
          try {
            if (document.head.contains(preloadRef.current)) {
              preloadRef.current.remove()
            }
          } catch (error) {
            console.debug('Preload link cleanup error:', error)
          }
          preloadRef.current = null
        }
      }
    }
  }, [priority, optimizedSrc, srcSet, sizes, crossOrigin])

  // Handle image loading
  const handleImageLoad = useCallback(() => {
    if (!loadStarted && (priority || isIntersecting) && src && !hasError) {
      setLoadStarted(true)
      
      const img = new Image()
      
      // Set up cross-origin if needed
      if (crossOrigin) {
        img.crossOrigin = crossOrigin
      }
      
      // Set up referrer policy
      if (referrerPolicy) {
        img.referrerPolicy = referrerPolicy
      }

      img.onload = () => {
        setImageSrc(optimizedSrc)
        setIsLoaded(true)
        onLoad?.()
      }
      
      img.onerror = () => {
        setHasError(true)
        setIsLoaded(true)
        onError?.()
      }

      // Load the image
      if (srcSet && capabilities.intersectionObserver) {
        img.srcset = srcSet
        img.sizes = sizes
      }
      img.src = optimizedSrc
    }
  }, [loadStarted, priority, isIntersecting, src, hasError, optimizedSrc, srcSet, sizes, crossOrigin, referrerPolicy, onLoad, onError, capabilities.intersectionObserver])

  useEffect(() => {
    handleImageLoad()
  }, [handleImageLoad])

  // Set initial placeholder
  useEffect(() => {
    if (!imageSrc) {
      setImageSrc(currentPlaceholder)
    }
  }, [currentPlaceholder, imageSrc])

  // Error state component
  if (hasError) {
    return (
      <div 
        ref={imageRef}
        className={`flex items-center justify-center bg-gray-100 text-gray-400 ${className}`}
        style={aspectRatio ? { aspectRatio } : undefined}
        aria-label={`Failed to load image: ${alt}`}
      >
        <div className="text-center">
          <svg 
            className="w-16 h-16 mx-auto mb-2" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
            />
          </svg>
          <p className="text-sm">Image failed to load</p>
        </div>
      </div>
    )
  }

  // Container styles
  const containerStyle: React.CSSProperties = {
    ...(aspectRatio && { aspectRatio }),
    position: 'relative',
    overflow: 'hidden'
  }

  // Image styles
  const imageStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    transition: 'opacity 0.3s ease, filter 0.3s ease',
    ...(isLoaded ? { opacity: 1, filter: 'none' } : { opacity: 0.8, filter: 'blur(5px)' })
  }

  return (
    <div 
      ref={imageRef} 
      className={`relative ${className}`}
      style={containerStyle}
    >
      <img
        ref={imgRef}
        src={imageSrc}
        srcSet={isLoaded && srcSet ? srcSet : undefined}
        sizes={isLoaded && responsive ? sizes : undefined}
        alt={alt}
        style={imageStyle}
        loading={priority ? 'eager' : 'lazy'}
        fetchPriority={fetchPriority}
        crossOrigin={crossOrigin}
        referrerPolicy={referrerPolicy}
        onLoad={() => {
          setIsLoaded(true)
          onLoad?.()
        }}
        onError={() => {
          setHasError(true)
          onError?.()
        }}
        {...props}
      />
      
      {/* Loading indicator */}
      {!isLoaded && !hasError && (
        <div 
          className="absolute inset-0 bg-gray-100 flex items-center justify-center"
          aria-hidden="true"
        >
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      
      {/* Progress indicator for slow loading images */}
      {loadStarted && !isLoaded && !hasError && (
        <div className="absolute bottom-2 left-2 right-2">
          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full animate-pulse" />
          </div>
        </div>
      )}
    </div>
  )
}

export default LazyImage