import { Link } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import type { AppDispatch } from '../../store/index'
import { dismissBanner, type Banner } from '../../store/slices/bannersSlice'

interface AnnouncementBannerProps {
  banner: Banner
}

const AnnouncementBanner = ({ banner }: AnnouncementBannerProps) => {
  const dispatch = useDispatch<AppDispatch>()

  const handleDismiss = () => {
    dispatch(dismissBanner(banner.id))
  }

  return (
    <div 
      className="relative py-3 px-4"
      style={{ backgroundColor: banner.background_color || '#1f2937' }}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm font-medium" style={{ color: banner.text_color || '#ffffff' }}>
            <span className="md:hidden">{banner.title}</span>
            <span className="hidden md:inline">
              {banner.title}
              {banner.subtitle && ` - ${banner.subtitle}`}
            </span>
            {banner.link_url && banner.link_text && (
              <>
                <span className="mx-2">•</span>
                <Link
                  to={banner.link_url}
                  className="underline hover:no-underline"
                  style={{ color: banner.text_color || '#ffffff' }}
                >
                  {banner.link_text}
                </Link>
              </>
            )}
          </p>
        </div>
        
        <button
          onClick={handleDismiss}
          className="ml-4 flex-shrink-0 p-1 rounded-md hover:bg-black hover:bg-opacity-20 transition-colors"
          title="Dismiss"
        >
          <svg 
            className="w-4 h-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
            style={{ color: banner.text_color || '#ffffff' }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default AnnouncementBanner