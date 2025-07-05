import { useState, useEffect, useRef, useCallback } from 'react'
import LazyImage from './LazyImage'
import { getSmartOptimizedImageUrl } from '../utils/cdn'

interface ProductImage {
  id: string
  url: string
  alt: string
  caption?: string
  isMain?: boolean
}

interface ProductImageGalleryProps {
  images: ProductImage[]
  productName: string
  className?: string
  enableZoom?: boolean
  enableFullscreen?: boolean
  enableThumbnails?: boolean
  autoplayDuration?: number
  enableSwipe?: boolean
  priority?: boolean
}

const ProductImageGallery = ({
  images,
  productName,
  className = '',
  enableZoom = true,
  enableFullscreen = true,
  enableThumbnails = true,
  autoplayDuration = 0,
  enableSwipe = true,
  priority = false
}: ProductImageGalleryProps) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isZoomed, setIsZoomed] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [zoomPosition, setZoomPosition] = useState({ x: 0, y: 0 })
  const [touchStart, setTouchStart] = useState(0)
  const [touchEnd, setTouchEnd] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(false)
  
  const mainImageRef = useRef<HTMLDivElement>(null)
  const galleryRef = useRef<HTMLDivElement>(null)
  const autoplayRef = useRef<NodeJS.Timeout>()

  const currentImage = images[currentIndex]

  // Navigation functions
  const goToNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % images.length)
  }, [images.length])

  const goToPrevious = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length)
  }, [images.length])

  // Autoplay functionality
  useEffect(() => {
    if (autoplayDuration > 0 && isAutoPlaying && images.length > 1) {
      autoplayRef.current = setInterval(goToNext, autoplayDuration)
      return () => {
        if (autoplayRef.current) {
          clearInterval(autoplayRef.current)
        }
      }
    }
  }, [autoplayDuration, isAutoPlaying, images.length, goToNext])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isFullscreen) {
        switch (event.key) {
          case 'ArrowLeft':
            event.preventDefault()
            goToPrevious()
            break
          case 'ArrowRight':
            event.preventDefault()
            goToNext()
            break
          case 'Escape':
            event.preventDefault()
            setIsFullscreen(false)
            setIsZoomed(false)
            break
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isFullscreen, goToNext, goToPrevious])

  // Touch/swipe handling
  const handleTouchStart = (e: React.TouchEvent) => {
    if (!enableSwipe) return
    setTouchStart(e.targetTouches[0].clientX)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!enableSwipe) return
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const handleTouchEnd = () => {
    if (!enableSwipe || !touchStart || !touchEnd) return
    
    const distance = touchStart - touchEnd
    const minSwipeDistance = 50

    if (distance > minSwipeDistance) {
      goToNext()
    } else if (distance < -minSwipeDistance) {
      goToPrevious()
    }
  }

  // Zoom functionality
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!enableZoom || !isZoomed) return

    const rect = mainImageRef.current?.getBoundingClientRect()
    if (!rect) return

    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    
    setZoomPosition({ x, y })
  }

  const toggleZoom = () => {
    if (!enableZoom) return
    setIsZoomed(!isZoomed)
  }

  const toggleFullscreen = () => {
    if (!enableFullscreen) return
    setIsFullscreen(!isFullscreen)
    setIsZoomed(false)
  }

  // Generate image URLs for different sizes
  const getImageUrls = (image: ProductImage) => {
    const baseOptions = { format: 'auto' as const, quality: 90 }
    
    return {
      thumbnail: getSmartOptimizedImageUrl(image.url, { ...baseOptions, width: 100, height: 100 }),
      medium: getSmartOptimizedImageUrl(image.url, { ...baseOptions, width: 600, height: 600 }),
      large: getSmartOptimizedImageUrl(image.url, { ...baseOptions, width: 1200, height: 1200 }),
      xlarge: getSmartOptimizedImageUrl(image.url, { ...baseOptions, width: 2400, height: 2400 })
    }
  }

  const currentImageUrls = currentImage ? getImageUrls(currentImage) : null

  if (!images.length) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 aspect-square ${className}`}>
        <div className="text-center text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p>No images available</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div ref={galleryRef} className={`relative ${className}`}>
        {/* Main Image */}
        <div 
          ref={mainImageRef}
          className="relative aspect-square bg-white rounded-lg overflow-hidden group cursor-pointer"
          onClick={toggleZoom}
          onMouseMove={handleMouseMove}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <LazyImage
            src={currentImage.url}
            alt={currentImage.alt || `${productName} - Image ${currentIndex + 1}`}
            className="w-full h-full object-cover"
            priority={priority && currentIndex === 0}
            responsive={true}
            optimizationOptions={{
              format: 'auto',
              quality: 90,
              progressive: true
            }}
            sizes="(max-width: 768px) 100vw, 600px"
            onLoad={() => setIsAutoPlaying(true)}
          />

          {/* Zoom overlay */}
          {isZoomed && enableZoom && (
            <div 
              className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center"
              style={{
                backgroundImage: `url(${currentImageUrls?.xlarge})`,
                backgroundPosition: `${zoomPosition.x}% ${zoomPosition.y}%`,
                backgroundSize: '200%',
                backgroundRepeat: 'no-repeat'
              }}
            >
              <div className="text-white text-center">
                <p className="text-sm">Click to exit zoom</p>
              </div>
            </div>
          )}

          {/* Navigation arrows */}
          {images.length > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  goToPrevious()
                }}
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                aria-label="Previous image"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  goToNext()
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-opacity-70"
                aria-label="Next image"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </>
          )}

          {/* Action buttons */}
          <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {enableFullscreen && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  toggleFullscreen()
                }}
                className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                aria-label="View fullscreen"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
            )}

            {autoplayDuration > 0 && images.length > 1 && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setIsAutoPlaying(!isAutoPlaying)
                }}
                className="bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-70"
                aria-label={isAutoPlaying ? "Pause slideshow" : "Start slideshow"}
              >
                {isAutoPlaying ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1" />
                  </svg>
                )}
              </button>
            )}
          </div>

          {/* Image counter */}
          {images.length > 1 && (
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
              {currentIndex + 1} / {images.length}
            </div>
          )}
        </div>

        {/* Thumbnails */}
        {enableThumbnails && images.length > 1 && (
          <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
            {images.map((image, index) => (
              <button
                key={image.id}
                onClick={() => setCurrentIndex(index)}
                className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                  index === currentIndex ? 'border-blue-500 scale-105' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <LazyImage
                  src={image.url}
                  alt={`${productName} thumbnail ${index + 1}`}
                  className="w-full h-full object-cover"
                  optimizationOptions={{
                    width: 80,
                    height: 80,
                    quality: 80,
                    format: 'auto'
                  }}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div className="fixed inset-0 bg-black bg-opacity-95 z-50 flex items-center justify-center">
          <div className="relative max-w-7xl max-h-full p-4">
            <LazyImage
              src={currentImage.url}
              alt={currentImage.alt || `${productName} - Image ${currentIndex + 1}`}
              className="max-w-full max-h-full object-contain"
              priority
              optimizationOptions={{
                format: 'auto',
                quality: 95,
                progressive: true
              }}
              sizes="100vw"
            />

            {/* Fullscreen controls */}
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-4 right-4 text-white p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70"
              aria-label="Close fullscreen"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {images.length > 1 && (
              <>
                <button
                  onClick={goToPrevious}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-white p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70"
                  aria-label="Previous image"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                
                <button
                  onClick={goToNext}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70"
                  aria-label="Next image"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white text-lg">
                  {currentIndex + 1} / {images.length}
                </div>
              </>
            )}

            {currentImage.caption && (
              <div className="absolute bottom-4 left-4 right-4 text-white text-center bg-black bg-opacity-50 p-2 rounded">
                {currentImage.caption}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export default ProductImageGallery