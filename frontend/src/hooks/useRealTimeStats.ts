import { useEffect, useRef } from 'react'
import { useDispatch } from 'react-redux'
import type { AppDispatch } from '../store'
import { fetchRealtimeStats } from '../store/slices/adminSlice'

export const useRealTimeStats = (intervalMs: number = 30000) => {
  const dispatch = useDispatch<AppDispatch>()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    // Initial fetch
    dispatch(fetchRealtimeStats())

    // Set up polling
    intervalRef.current = setInterval(() => {
      dispatch(fetchRealtimeStats())
    }, intervalMs)

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [dispatch, intervalMs])

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])
}

export default useRealTimeStats