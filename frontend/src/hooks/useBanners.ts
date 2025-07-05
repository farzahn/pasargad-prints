import { useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import type { AppDispatch, RootState } from '../store/index'
import {
  fetchBanners,
  selectBannersByPosition,
  selectBannersByType,
  dismissBanner,
  type Banner,
} from '../store/slices/bannersSlice'

export const useBanners = () => {
  const dispatch = useDispatch<AppDispatch>()
  const loading = useSelector((state: RootState) => state.banners.loading)
  const error = useSelector((state: RootState) => state.banners.error)
  const bannersByPosition = useSelector(selectBannersByPosition)
  const bannersByType = useSelector(selectBannersByType)

  useEffect(() => {
    dispatch(fetchBanners())
  }, [dispatch])

  const getBannersByPosition = (position: Banner['position']) => {
    return bannersByPosition[position] || []
  }

  const getBannersByType = (type: Banner['banner_type']) => {
    return bannersByType[type] || []
  }

  const handleDismissBanner = (bannerId: number) => {
    dispatch(dismissBanner(bannerId))
  }

  return {
    loading,
    error,
    getBannersByPosition,
    getBannersByType,
    dismissBanner: handleDismissBanner,
  }
}

export default useBanners