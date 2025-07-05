import { useEffect, useRef, useState, useCallback } from 'react'

interface UseLazyLoadOptions {
  threshold?: number | number[]
  rootMargin?: string
  triggerOnce?: boolean
  root?: Element | null
  delay?: number
  onIntersect?: (isIntersecting: boolean, entry: IntersectionObserverEntry) => void
}

interface UseLazyLoadReturn<T> {
  isIntersecting: boolean
  targetRef: React.RefObject<T>
  entry: IntersectionObserverEntry | null
  observe: () => void
  unobserve: () => void
  reset: () => void
}

export const useLazyLoad = <T extends HTMLElement = HTMLElement>(
  options: UseLazyLoadOptions = {}
): [boolean, React.RefObject<T>] | UseLazyLoadReturn<T> => {
  const {
    threshold = 0.1,
    rootMargin = '50px',
    triggerOnce = true,
    root = null,
    delay = 0,
    onIntersect
  } = options

  const [isIntersecting, setIsIntersecting] = useState(false)
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null)
  const targetRef = useRef<T>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const handleIntersection = useCallback((entries: IntersectionObserverEntry[]) => {
    const [currentEntry] = entries
    setEntry(currentEntry)

    const handleChange = () => {
      const isCurrentlyIntersecting = currentEntry.isIntersecting
      
      setIsIntersecting(isCurrentlyIntersecting)
      onIntersect?.(isCurrentlyIntersecting, currentEntry)
      
      if (isCurrentlyIntersecting && triggerOnce && targetRef.current) {
        observerRef.current?.unobserve(targetRef.current)
      }
    }

    if (delay > 0) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(handleChange, delay)
    } else {
      handleChange()
    }
  }, [triggerOnce, delay, onIntersect])

  const observe = useCallback(() => {
    const target = targetRef.current
    if (!target || observerRef.current) return

    // Check if IntersectionObserver is supported
    if (!('IntersectionObserver' in window)) {
      // Fallback for older browsers
      setIsIntersecting(true)
      return
    }

    observerRef.current = new IntersectionObserver(handleIntersection, {
      threshold,
      rootMargin,
      root
    })

    observerRef.current.observe(target)
  }, [threshold, rootMargin, root, handleIntersection])

  const unobserve = useCallback(() => {
    const target = targetRef.current
    if (target && observerRef.current) {
      observerRef.current.unobserve(target)
    }
  }, [])

  const reset = useCallback(() => {
    setIsIntersecting(false)
    setEntry(null)
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  useEffect(() => {
    if (targetRef.current) {
      observe()
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = null
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }
  }, [observe])

  // Simple return for backward compatibility
  return [isIntersecting, targetRef]
}

// Enhanced hook with more features
export const useLazyLoadAdvanced = <T extends HTMLElement = HTMLElement>(
  options: UseLazyLoadOptions = {}
): UseLazyLoadReturn<T> => {
  const {
    threshold = 0.1,
    rootMargin = '50px',
    triggerOnce = true,
    root = null,
    delay = 0,
    onIntersect
  } = options

  const [isIntersecting, setIsIntersecting] = useState(false)
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null)
  const targetRef = useRef<T>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const handleIntersection = useCallback((entries: IntersectionObserverEntry[]) => {
    const [currentEntry] = entries
    setEntry(currentEntry)

    const handleChange = () => {
      const isCurrentlyIntersecting = currentEntry.isIntersecting
      
      setIsIntersecting(isCurrentlyIntersecting)
      onIntersect?.(isCurrentlyIntersecting, currentEntry)
      
      if (isCurrentlyIntersecting && triggerOnce && targetRef.current) {
        observerRef.current?.unobserve(targetRef.current)
      }
    }

    if (delay > 0) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(handleChange, delay)
    } else {
      handleChange()
    }
  }, [triggerOnce, delay, onIntersect])

  const observe = useCallback(() => {
    const target = targetRef.current
    if (!target) return

    // Check if IntersectionObserver is supported
    if (!('IntersectionObserver' in window)) {
      // Fallback for older browsers
      setIsIntersecting(true)
      return
    }

    if (observerRef.current) {
      observerRef.current.disconnect()
    }

    observerRef.current = new IntersectionObserver(handleIntersection, {
      threshold,
      rootMargin,
      root
    })

    observerRef.current.observe(target)
  }, [threshold, rootMargin, root, handleIntersection])

  const unobserve = useCallback(() => {
    const target = targetRef.current
    if (target && observerRef.current) {
      observerRef.current.unobserve(target)
    }
  }, [])

  const reset = useCallback(() => {
    setIsIntersecting(false)
    setEntry(null)
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  useEffect(() => {
    if (targetRef.current) {
      observe()
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
        observerRef.current = null
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }
  }, [observe])

  return {
    isIntersecting,
    targetRef,
    entry,
    observe,
    unobserve,
    reset
  }
}

// Hook for monitoring viewport changes
export const useViewportIntersection = <T extends HTMLElement = HTMLElement>(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: Omit<UseLazyLoadOptions, 'onIntersect'> = {}
) => {
  const targetRef = useRef<T>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    const target = targetRef.current
    if (!target) return

    if (!('IntersectionObserver' in window)) {
      return
    }

    observerRef.current = new IntersectionObserver(callback, {
      threshold: options.threshold || 0.1,
      rootMargin: options.rootMargin || '50px',
      root: options.root || null
    })

    observerRef.current.observe(target)

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [callback, options.threshold, options.rootMargin, options.root])

  return targetRef
}