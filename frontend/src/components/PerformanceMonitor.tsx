import { useEffect } from 'react'

const PerformanceMonitor = () => {
  useEffect(() => {
    // Monitor Core Web Vitals
    if ('PerformanceObserver' in window) {
      // Monitor Largest Contentful Paint (LCP)
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        console.log('LCP:', lastEntry.startTime)
        // You can send this data to your analytics service
      })
      
      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
      } catch (e) {
        console.error('LCP observer error:', e)
      }

      // Monitor First Input Delay (FID)
      const fidObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const eventEntry = entry as PerformanceEventTiming
          const delay = eventEntry.processingStart - eventEntry.startTime
          console.log('FID:', delay)
          // You can send this data to your analytics service
        }
      })
      
      try {
        fidObserver.observe({ entryTypes: ['first-input'] })
      } catch (e) {
        console.error('FID observer error:', e)
      }

      // Monitor Cumulative Layout Shift (CLS)
      let clsValue = 0
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const layoutShiftEntry = entry as PerformanceEntry & {
            hadRecentInput?: boolean;
            value: number;
          };
          if (!layoutShiftEntry.hadRecentInput) {
            clsValue += layoutShiftEntry.value
            console.log('CLS:', clsValue)
            // You can send this data to your analytics service
          }
        }
      })
      
      try {
        clsObserver.observe({ entryTypes: ['layout-shift'] })
      } catch (e) {
        console.error('CLS observer error:', e)
      }

      // Cleanup
      return () => {
        lcpObserver.disconnect()
        fidObserver.disconnect()
        clsObserver.disconnect()
      }
    }

    // Monitor page load time
    window.addEventListener('load', () => {
      const navEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      if (navEntry) {
        console.log('Page Load Time:', navEntry.loadEventEnd - navEntry.fetchStart)
        console.log('DOM Content Loaded:', navEntry.domContentLoadedEventEnd - navEntry.fetchStart)
        console.log('First Paint:', navEntry.domContentLoadedEventStart - navEntry.fetchStart)
      }
    })
  }, [])

  return null
}

export default PerformanceMonitor