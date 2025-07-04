import { Link } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import type { AppDispatch } from '../../store/index'
import { dismissBanner, type Banner } from '../../store/slices/bannersSlice'

interface PromotionBannerProps {
  banner: Banner
}

const PromotionBanner = ({ banner }: PromotionBannerProps) => {
  const dispatch = useDispatch<AppDispatch>()

  const handleDismiss = () => {
    dispatch(dismissBanner(banner.id))
  }

  const content = (
    <div 
      className="relative rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow"
      style={{ backgroundColor: banner.background_color || '#ffffff' }}
    >
      {banner.image_url && (
        <div className="aspect-video md:aspect-[21/9] overflow-hidden">
          <img
            src={banner.image_url}
            alt={banner.title}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
          />
        </div>
      )}
      
      <div className="p-6">
        <h3 
          className="text-xl font-bold mb-2"
          style={{ color: banner.text_color || '#111827' }}
        >
          {banner.title}
        </h3>
        
        {banner.subtitle && (
          <p 
            className="text-lg mb-2"
            style={{ color: banner.text_color || '#111827' }}
          >
            {banner.subtitle}
          </p>
        )}
        
        {banner.description && (
          <p 
            className="text-sm mb-4 opacity-90"
            style={{ color: banner.text_color || '#4b5563' }}
          >
            {banner.description}
          </p>
        )}
        
        <div className="flex items-center justify-between">
          {banner.link_url && banner.link_text && (
            <Link
              to={banner.link_url}
              className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium"
            >
              {banner.link_text}
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          )}
          
          <button
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600"
            title="Dismiss banner"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
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

export default PromotionBanner