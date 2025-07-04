import { Link } from 'react-router-dom'
import LazyImage from '../LazyImage'
import type { Banner } from '../../store/slices/bannersSlice'

interface HeroBannerProps {
  banner: Banner
}

const HeroBanner = ({ banner }: HeroBannerProps) => {
  const content = (
    <div className="relative min-h-[400px] md:min-h-[500px] flex items-center overflow-hidden">
      {/* Background Image with Lazy Loading */}
      <div className="absolute inset-0">
        <LazyImage
          src={banner.image_url}
          alt={banner.title}
          className="w-full h-full object-cover"
        />
      </div>
      
      {/* Overlay for better text readability */}
      <div className="absolute inset-0 bg-black bg-opacity-40" />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
        <div className="max-w-3xl">
          <h1 
            className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 animate-fade-in"
            style={{ color: banner.text_color || '#ffffff' }}
          >
            {banner.title}
          </h1>
          
          {banner.subtitle && (
            <h2 
              className="text-xl md:text-2xl lg:text-3xl mb-6 animate-slide-up"
              style={{ 
                color: banner.text_color || '#ffffff',
                animationDelay: '0.2s' 
              }}
            >
              {banner.subtitle}
            </h2>
          )}
          
          {banner.description && (
            <p 
              className="text-lg mb-8 animate-slide-up"
              style={{ 
                color: banner.text_color || '#ffffff',
                animationDelay: '0.4s' 
              }}
            >
              {banner.description}
            </p>
          )}
          
          {banner.link_url && banner.link_text && (
            <Link
              to={banner.link_url}
              className="inline-block bg-white text-gray-900 px-8 py-3 rounded-md font-semibold hover:bg-gray-100 transition-colors transform hover:scale-105 animate-slide-up"
              style={{ animationDelay: '0.6s' }}
            >
              {banner.link_text}
            </Link>
          )}
        </div>
      </div>
    </div>
  )

  return banner.link_url && !banner.link_text ? (
    <Link to={banner.link_url} className="block">
      {content}
    </Link>
  ) : (
    content
  )
}

export default HeroBanner