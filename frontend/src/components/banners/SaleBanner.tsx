import { Link } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import type { AppDispatch } from '../../store/index'
import { dismissBanner, type Banner } from '../../store/slices/bannersSlice'

interface SaleBannerProps {
  banner: Banner
}

const SaleBanner = ({ banner }: SaleBannerProps) => {
  const dispatch = useDispatch<AppDispatch>()

  const handleDismiss = () => {
    dispatch(dismissBanner(banner.id))
  }

  const content = (
    <div 
      className="relative rounded-lg overflow-hidden shadow-lg bg-gradient-to-r from-red-500 to-pink-500 p-8 text-white"
      style={{
        backgroundImage: banner.image_url ? `url(${banner.image_url})` : undefined,
        backgroundColor: banner.background_color || undefined,
      }}
    >
      {/* Pattern overlay */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.1) 35px, rgba(255,255,255,.1) 70px)`
        }} />
      </div>
      
      <div className="relative z-10 text-center">
        <div className="inline-block mb-4">
          <span className="bg-white text-red-600 px-4 py-1 rounded-full text-sm font-bold uppercase tracking-wide">
            Limited Time
          </span>
        </div>
        
        <h3 
          className="text-3xl md:text-4xl font-bold mb-2"
          style={{ color: banner.text_color || '#ffffff' }}
        >
          {banner.title}
        </h3>
        
        {banner.subtitle && (
          <p 
            className="text-xl md:text-2xl mb-6"
            style={{ color: banner.text_color || '#ffffff' }}
          >
            {banner.subtitle}
          </p>
        )}
        
        {banner.description && (
          <p 
            className="text-lg mb-8 max-w-2xl mx-auto"
            style={{ color: banner.text_color || '#ffffff' }}
          >
            {banner.description}
          </p>
        )}
        
        {banner.link_url && banner.link_text && (
          <Link
            to={banner.link_url}
            className="inline-block bg-white text-red-600 px-8 py-3 rounded-md font-bold hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg"
          >
            {banner.link_text}
          </Link>
        )}
      </div>
      
      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        className="absolute top-4 right-4 text-white hover:text-gray-200 bg-black bg-opacity-20 rounded-full p-2"
        title="Dismiss banner"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      
      {/* Sale countdown timer could go here */}
      {banner.end_date && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
          <CountdownTimer endDate={banner.end_date} />
        </div>
      )}
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

// Simple countdown timer component
const CountdownTimer = ({ endDate }: { endDate: string }) => {
  // This would need to be implemented with proper state management
  // For now, just showing a placeholder
  return (
    <div className="flex items-center gap-2 text-sm">
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>Ends soon</span>
    </div>
  )
}

export default SaleBanner