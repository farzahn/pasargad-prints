import { useState } from 'react'
import LazyImage from './LazyImage'

interface ImageGalleryProps {
  images: Array<{
    image: string
    alt?: string
  }>
  mainImage?: string
  productName: string
}

const OptimizedImageGallery = ({ images, mainImage, productName }: ImageGalleryProps) => {
  const [selectedImage, setSelectedImage] = useState(mainImage || images[0]?.image || '')
  const [isZoomed, setIsZoomed] = useState(false)

  const allImages = mainImage 
    ? [{ image: mainImage, alt: productName }, ...images]
    : images

  const handleImageClick = (image: string) => {
    setSelectedImage(image)
    setIsZoomed(false)
  }

  const toggleZoom = () => {
    setIsZoomed(!isZoomed)
  }

  return (
    <div className="space-y-4">
      {/* Main Image Display */}
      <div 
        className="relative bg-gray-100 rounded-lg overflow-hidden cursor-zoom-in"
        onClick={toggleZoom}
      >
        <LazyImage
          src={selectedImage}
          alt={productName}
          className={`w-full h-96 lg:h-[500px] object-contain transition-transform duration-300 ${
            isZoomed ? 'scale-150' : ''
          }`}
        />
        
        {/* Zoom Indicator */}
        <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white p-2 rounded-full">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d={isZoomed 
                ? "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" 
                : "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7"
              } 
            />
          </svg>
        </div>
      </div>

      {/* Thumbnail Gallery */}
      {allImages.length > 1 && (
        <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
          {allImages.map((img, index) => (
            <button
              key={index}
              onClick={() => handleImageClick(img.image)}
              className={`relative aspect-square bg-gray-100 rounded-md overflow-hidden border-2 transition-all ${
                selectedImage === img.image 
                  ? 'border-primary-600 shadow-md' 
                  : 'border-transparent hover:border-gray-300'
              }`}
              aria-label={`View image ${index + 1}`}
            >
              <LazyImage
                src={img.image}
                alt={img.alt || `${productName} - Image ${index + 1}`}
                className="w-full h-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default OptimizedImageGallery