import { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import type { AppDispatch, RootState } from '../../store/index'
import { fetchBanners, selectBannersByPosition } from '../../store/slices/bannersSlice'
import HeroBanner from './HeroBanner'
import PromotionBanner from './PromotionBanner'
import AnnouncementBanner from './AnnouncementBanner'
import SaleBanner from './SaleBanner'

interface BannerSystemProps {
  position: 'top' | 'middle' | 'bottom'
  className?: string
}

const BannerSystem = ({ position, className = '' }: BannerSystemProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const bannersByPosition = useSelector(selectBannersByPosition)
  const loading = useSelector((state: RootState) => state.banners.loading)

  useEffect(() => {
    dispatch(fetchBanners())
  }, [dispatch])

  const banners = bannersByPosition[position] || []

  if (loading || banners.length === 0) {
    return null
  }

  const renderBanner = (banner: typeof banners[0]) => {
    switch (banner.banner_type) {
      case 'hero':
        return <HeroBanner key={banner.id} banner={banner} />
      case 'promotion':
        return (
          <div key={banner.id} className="mb-6">
            <PromotionBanner banner={banner} />
          </div>
        )
      case 'announcement':
        return <AnnouncementBanner key={banner.id} banner={banner} />
      case 'sale':
        return (
          <div key={banner.id} className="mb-6">
            <SaleBanner banner={banner} />
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className={className}>
      {banners.map(renderBanner)}
    </div>
  )
}

export default BannerSystem