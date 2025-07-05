// Advanced Image Preloader with Priority Queue
import { getSmartOptimizedImageUrl, getBrowserCapabilities } from './cdn'

interface PreloadOptions {
  priority?: 'high' | 'medium' | 'low'
  formats?: ('webp' | 'avif' | 'jpeg')[]
  sizes?: { width: number; height: number }[]
  quality?: number
  crossOrigin?: 'anonymous' | 'use-credentials'
  referrerPolicy?: ReferrerPolicy
  timeout?: number
  retries?: number
}

interface PreloadTask {
  id: string
  url: string
  options: PreloadOptions
  priority: number
  promise: Promise<void>
  resolve: () => void
  reject: (error: Error) => void
  attempts: number
  maxAttempts: number
}

class ImagePreloader {
  private queue: PreloadTask[] = []
  private activePreloads = new Map<string, PreloadTask>()
  private completed = new Set<string>()
  private failed = new Set<string>()
  private maxConcurrent = 4
  private isProcessing = false

  // Priority values
  private readonly priorities = {
    high: 1,
    medium: 2,
    low: 3
  }

  constructor() {
    // Adjust max concurrent based on connection
    this.adjustConcurrency()
  }

  // Adjust concurrency based on network conditions
  private adjustConcurrency() {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
    
    if (connection) {
      switch (connection.effectiveType) {
        case 'slow-2g':
        case '2g':
          this.maxConcurrent = 1
          break
        case '3g':
          this.maxConcurrent = 2
          break
        case '4g':
        default:
          this.maxConcurrent = 4
          break
      }
    }

    // Reduce concurrency on low-end devices
    if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) {
      this.maxConcurrent = Math.min(this.maxConcurrent, 2)
    }
  }

  // Preload a single image
  async preload(url: string, options: PreloadOptions = {}): Promise<void> {
    const taskId = this.generateTaskId(url, options)
    
    // Return existing promise if already preloading or completed
    if (this.activePreloads.has(taskId)) {
      return this.activePreloads.get(taskId)!.promise
    }
    
    if (this.completed.has(taskId)) {
      return Promise.resolve()
    }
    
    if (this.failed.has(taskId)) {
      return Promise.reject(new Error(`Image preload failed: ${url}`))
    }

    // Create new preload task
    const task = this.createPreloadTask(taskId, url, options)
    this.queue.push(task)
    this.activePreloads.set(taskId, task)

    // Sort queue by priority
    this.queue.sort((a, b) => a.priority - b.priority)

    // Start processing if not already running
    if (!this.isProcessing) {
      this.processQueue()
    }

    return task.promise
  }

  // Preload multiple images
  async preloadBatch(items: Array<{ url: string; options?: PreloadOptions }>): Promise<void[]> {
    const promises = items.map(item => this.preload(item.url, item.options))
    return Promise.allSettled(promises).then(results => 
      results.map(result => {
        if (result.status === 'rejected') {
          console.warn('Image preload failed:', result.reason)
        }
      })
    )
  }

  // Preload critical above-the-fold images
  async preloadCritical(images: string[], options: PreloadOptions = {}): Promise<void> {
    const criticalOptions = { ...options, priority: 'high' as const }
    await this.preloadBatch(images.map(url => ({ url, options: criticalOptions })))
  }

  // Create a preload task
  private createPreloadTask(id: string, url: string, options: PreloadOptions): PreloadTask {
    let resolve: () => void
    let reject: (error: Error) => void

    const promise = new Promise<void>((res, rej) => {
      resolve = res
      reject = rej
    })

    return {
      id,
      url,
      options,
      priority: this.priorities[options.priority || 'medium'],
      promise,
      resolve: resolve!,
      reject: reject!,
      attempts: 0,
      maxAttempts: options.retries || 3
    }
  }

  // Generate unique task ID
  private generateTaskId(url: string, options: PreloadOptions): string {
    const optionsStr = JSON.stringify(options)
    return btoa(url + optionsStr).replace(/[+/=]/g, '')
  }

  // Process the preload queue
  private async processQueue() {
    this.isProcessing = true

    while (this.queue.length > 0) {
      const activeTasks = Array.from(this.activePreloads.values())
        .filter(task => task.attempts > 0)
      
      if (activeTasks.length >= this.maxConcurrent) {
        // Wait for at least one to complete
        await Promise.race(activeTasks.map(task => task.promise.catch(() => {})))
        continue
      }

      const task = this.queue.shift()
      if (!task) break

      this.executePreloadTask(task)
    }

    this.isProcessing = false
  }

  // Execute a single preload task
  private async executePreloadTask(task: PreloadTask) {
    try {
      task.attempts++
      await this.performPreload(task)
      this.completed.add(task.id)
      this.activePreloads.delete(task.id)
      task.resolve()
    } catch (error) {
      if (task.attempts < task.maxAttempts) {
        // Retry with exponential backoff
        const delay = Math.pow(2, task.attempts - 1) * 1000
        setTimeout(() => {
          this.queue.unshift(task) // Add back to front with high priority
          if (!this.isProcessing) {
            this.processQueue()
          }
        }, delay)
      } else {
        this.failed.add(task.id)
        this.activePreloads.delete(task.id)
        task.reject(error as Error)
      }
    }
  }

  // Perform the actual preload
  private async performPreload(task: PreloadTask): Promise<void> {
    const { url, options } = task
    const capabilities = getBrowserCapabilities()

    return new Promise((resolve, reject) => {
      // Choose the best format
      let targetUrl = url
      if (options.formats) {
        for (const format of options.formats) {
          if ((format === 'avif' && capabilities.avif) || 
              (format === 'webp' && capabilities.webp)) {
            targetUrl = getSmartOptimizedImageUrl(url, { 
              format, 
              quality: options.quality || 85 
            })
            break
          }
        }
      } else {
        targetUrl = getSmartOptimizedImageUrl(url, { 
          format: 'auto', 
          quality: options.quality || 85 
        })
      }

      // Use link prefetch for better performance
      if ('HTMLLinkElement' in window) {
        const link = document.createElement('link')
        link.rel = 'prefetch'
        link.as = 'image'
        link.href = targetUrl
        
        if (options.crossOrigin) {
          link.crossOrigin = options.crossOrigin
        }
        
        if (options.referrerPolicy) {
          link.referrerPolicy = options.referrerPolicy
        }

        // Handle multiple sizes
        if (options.sizes && options.sizes.length > 0) {
          const srcSet = options.sizes.map(size => 
            `${getSmartOptimizedImageUrl(url, { 
              format: 'auto', 
              quality: options.quality || 85,
              width: size.width,
              height: size.height
            })} ${size.width}w`
          ).join(', ')
          
          link.imageSrcset = srcSet
          link.imageSizes = '(max-width: 768px) 100vw, 50vw'
        }

        let isResolved = false
        const timeout = options.timeout || 10000

        const cleanup = () => {
          try {
            if (document.head.contains(link)) {
              link.remove()
            }
          } catch (error) {
            console.debug('Preload link cleanup error:', error)
          }
        }

        const resolveOnce = () => {
          if (!isResolved) {
            isResolved = true
            cleanup()
            resolve()
          }
        }

        const rejectOnce = (error: Error) => {
          if (!isResolved) {
            isResolved = true
            cleanup()
            reject(error)
          }
        }

        // Set up timeout
        const timeoutId = setTimeout(() => {
          rejectOnce(new Error('Preload timeout'))
        }, timeout)

        // Use Image as fallback for better load detection
        const img = new Image()
        
        if (options.crossOrigin) {
          img.crossOrigin = options.crossOrigin
        }
        
        if (options.referrerPolicy) {
          img.referrerPolicy = options.referrerPolicy
        }

        img.onload = () => {
          clearTimeout(timeoutId)
          resolveOnce()
        }

        img.onerror = () => {
          clearTimeout(timeoutId)
          rejectOnce(new Error(`Failed to load image: ${targetUrl}`))
        }

        // Add link to DOM and start loading
        document.head.appendChild(link)
        img.src = targetUrl

      } else {
        // Fallback to Image preloading
        const img = new Image()
        
        if (options.crossOrigin) {
          img.crossOrigin = options.crossOrigin
        }
        
        if (options.referrerPolicy) {
          img.referrerPolicy = options.referrerPolicy
        }

        const timeout = options.timeout || 10000
        const timeoutId = setTimeout(() => {
          reject(new Error('Preload timeout'))
        }, timeout)

        img.onload = () => {
          clearTimeout(timeoutId)
          resolve()
        }

        img.onerror = () => {
          clearTimeout(timeoutId)
          reject(new Error(`Failed to load image: ${targetUrl}`))
        }

        img.src = targetUrl
      }
    })
  }

  // Cancel preload
  cancelPreload(url: string, options: PreloadOptions = {}): void {
    const taskId = this.generateTaskId(url, options)
    const task = this.activePreloads.get(taskId)
    
    if (task) {
      this.activePreloads.delete(taskId)
      task.reject(new Error('Preload cancelled'))
    }

    // Remove from queue
    this.queue = this.queue.filter(t => t.id !== taskId)
  }

  // Cancel all preloads
  cancelAll(): void {
    this.queue.forEach(task => task.reject(new Error('Preload cancelled')))
    this.activePreloads.forEach(task => task.reject(new Error('Preload cancelled')))
    
    this.queue = []
    this.activePreloads.clear()
  }

  // Get preload statistics
  getStats() {
    return {
      completed: this.completed.size,
      failed: this.failed.size,
      active: this.activePreloads.size,
      queued: this.queue.length,
      maxConcurrent: this.maxConcurrent
    }
  }

  // Check if image is preloaded
  isPreloaded(url: string, options: PreloadOptions = {}): boolean {
    const taskId = this.generateTaskId(url, options)
    return this.completed.has(taskId)
  }

  // Clear cache
  clearCache(): void {
    this.completed.clear()
    this.failed.clear()
  }
}

// Global preloader instance
export const imagePreloader = new ImagePreloader()

// Convenience functions
export const preloadImage = (url: string, options?: PreloadOptions) => {
  return imagePreloader.preload(url, options)
}

export const preloadImages = (urls: string[], options?: PreloadOptions) => {
  return imagePreloader.preloadBatch(urls.map(url => ({ url, options })))
}

export const preloadCriticalImages = (urls: string[], options?: PreloadOptions) => {
  return imagePreloader.preloadCritical(urls, options)
}

export const cancelImagePreload = (url: string, options?: PreloadOptions) => {
  return imagePreloader.cancelPreload(url, options)
}

export const getPreloadStats = () => {
  return imagePreloader.getStats()
}

// React hook for image preloading
export const useImagePreloader = () => {
  return {
    preload: preloadImage,
    preloadBatch: preloadImages,
    preloadCritical: preloadCriticalImages,
    cancel: cancelImagePreload,
    getStats: getPreloadStats,
    isPreloaded: imagePreloader.isPreloaded.bind(imagePreloader)
  }
}

// Auto-preload based on user interaction patterns
export class IntelligentPreloader {
  private hoverTimer: NodeJS.Timeout | null = null
  private preloadedOnHover = new Set<string>()

  // Preload on hover with delay
  preloadOnHover(element: HTMLElement, urls: string[], delay = 300) {
    const handleMouseEnter = () => {
      this.hoverTimer = setTimeout(() => {
        urls.forEach(url => {
          if (!this.preloadedOnHover.has(url)) {
            preloadImage(url, { priority: 'medium' })
            this.preloadedOnHover.add(url)
          }
        })
      }, delay)
    }

    const handleMouseLeave = () => {
      if (this.hoverTimer) {
        clearTimeout(this.hoverTimer)
        this.hoverTimer = null
      }
    }

    element.addEventListener('mouseenter', handleMouseEnter)
    element.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      element.removeEventListener('mouseenter', handleMouseEnter)
      element.removeEventListener('mouseleave', handleMouseLeave)
      if (this.hoverTimer) {
        clearTimeout(this.hoverTimer)
      }
    }
  }

  // Preload next page images based on scroll position
  preloadOnScroll(urls: string[], threshold = 0.8) {
    let hasPreloaded = false

    const handleScroll = () => {
      if (hasPreloaded) return

      const scrollPercent = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)
      
      if (scrollPercent >= threshold) {
        hasPreloaded = true
        preloadImages(urls, { priority: 'low' })
        window.removeEventListener('scroll', handleScroll)
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }
}

export const intelligentPreloader = new IntelligentPreloader()