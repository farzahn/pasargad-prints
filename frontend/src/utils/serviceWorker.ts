// Service Worker Configuration and Management
import { Workbox } from 'workbox-window'

export interface ServiceWorkerConfig {
  enabled: boolean
  updateInterval: number
  skipWaiting: boolean
  offlineSupport: boolean
  backgroundSync: boolean
  pushNotifications: boolean
}

export interface UpdateInfo {
  isUpdateAvailable: boolean
  isUpdatePending: boolean
  hasNewContent: boolean
  waitingServiceWorker: ServiceWorker | null
}

class ServiceWorkerManager {
  private wb: Workbox | null = null
  private config: ServiceWorkerConfig
  private updateInfo: UpdateInfo = {
    isUpdateAvailable: false,
    isUpdatePending: false,
    hasNewContent: false,
    waitingServiceWorker: null
  }
  private eventListeners: Map<string, Function[]> = new Map()

  constructor(config: Partial<ServiceWorkerConfig> = {}) {
    this.config = {
      enabled: import.meta.env.PROD,
      updateInterval: 60000, // Check for updates every minute
      skipWaiting: false,
      offlineSupport: true,
      backgroundSync: true,
      pushNotifications: false,
      ...config
    }
  }

  // Initialize service worker
  async init(): Promise<void> {
    if (!this.config.enabled || !('serviceWorker' in navigator)) {
      console.log('Service Worker is not enabled or not supported')
      return
    }

    try {
      // Initialize Workbox
      this.wb = new Workbox('/sw.js')

      // Set up event listeners
      this.setupEventListeners()

      // Register service worker
      await this.wb.register()

      // Set up update checking
      this.setupUpdateChecking()

      console.log('Service Worker initialized successfully')
    } catch (error) {
      console.error('Failed to initialize Service Worker:', error)
    }
  }

  // Set up event listeners
  private setupEventListeners(): void {
    if (!this.wb) return

    // Service worker is installing
    this.wb.addEventListener('installing', (event) => {
      console.log('Service Worker installing...')
      this.emit('installing', event)
    })

    // Service worker is installed
    this.wb.addEventListener('installed', (event) => {
      console.log('Service Worker installed')
      this.emit('installed', event)
    })

    // Service worker is waiting
    this.wb.addEventListener('waiting', (event) => {
      console.log('Service Worker is waiting')
      this.updateInfo.isUpdateAvailable = true
      this.updateInfo.waitingServiceWorker = event.sw
      this.emit('waiting', event)
    })

    // Service worker is controlling
    this.wb.addEventListener('controlling', (event) => {
      console.log('Service Worker is controlling')
      this.emit('controlling', event)
    })

    // Service worker is activated
    this.wb.addEventListener('activated', (event) => {
      console.log('Service Worker activated')
      this.emit('activated', event)
    })

    // Handle external updates
    this.wb.addEventListener('externalinstalled', (event) => {
      console.log('External Service Worker installed')
      this.emit('externalinstalled', event)
    })

    this.wb.addEventListener('externalactivated', (event) => {
      console.log('External Service Worker activated')
      this.emit('externalactivated', event)
    })

    // Handle redundant state
    this.wb.addEventListener('redundant', (event) => {
      console.log('Service Worker became redundant')
      this.emit('redundant', event)
    })

    // Handle messages from service worker
    this.wb.addEventListener('message', (event) => {
      console.log('Message from Service Worker:', event.data)
      this.handleServiceWorkerMessage(event.data)
    })
  }

  // Handle messages from service worker
  private handleServiceWorkerMessage(data: any): void {
    switch (data.type) {
      case 'CACHE_UPDATED':
        this.updateInfo.hasNewContent = true
        this.emit('cacheUpdated', data)
        break
      case 'OFFLINE_FALLBACK':
        this.emit('offlineFallback', data)
        break
      case 'BACKGROUND_SYNC':
        this.emit('backgroundSync', data)
        break
      case 'PUSH_NOTIFICATION':
        this.emit('pushNotification', data)
        break
    }
  }

  // Set up automatic update checking
  private setupUpdateChecking(): void {
    if (!this.wb) return

    // Check for updates immediately
    this.checkForUpdates()

    // Set up periodic update checks
    setInterval(() => {
      this.checkForUpdates()
    }, this.config.updateInterval)

    // Check for updates when the page becomes visible
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.checkForUpdates()
      }
    })
  }

  // Check for service worker updates
  async checkForUpdates(): Promise<void> {
    if (!this.wb) return

    try {
      const registration = await this.wb.getSW()
      if (registration) {
        await registration.update()
      }
    } catch (error) {
      console.error('Error checking for updates:', error)
    }
  }

  // Force service worker to skip waiting and take control
  async skipWaiting(): Promise<void> {
    if (!this.wb || !this.updateInfo.waitingServiceWorker) return

    try {
      // Send skip waiting message
      this.wb.messageSkipWaiting()
      
      // Wait for the new service worker to take control
      await new Promise<void>((resolve) => {
        this.wb!.addEventListener('controlling', () => {
          resolve()
        })
      })

      // Reload the page to use the new service worker
      window.location.reload()
    } catch (error) {
      console.error('Error skipping waiting:', error)
    }
  }

  // Register for push notifications
  async registerPushNotifications(): Promise<void> {
    if (!this.config.pushNotifications || !('PushManager' in window)) {
      console.log('Push notifications not supported or not enabled')
      return
    }

    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlB64ToUint8Array(
          import.meta.env.VITE_VAPID_PUBLIC_KEY || ''
        )
      })

      console.log('Push notification subscription:', subscription)
      
      // Send subscription to server
      await this.sendSubscriptionToServer(subscription)
      
      this.emit('pushSubscribed', subscription)
    } catch (error) {
      console.error('Error registering push notifications:', error)
    }
  }

  // Send subscription to server
  private async sendSubscriptionToServer(subscription: PushSubscription): Promise<void> {
    try {
      const response = await fetch('/api/push-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(subscription)
      })

      if (!response.ok) {
        throw new Error('Failed to send subscription to server')
      }
    } catch (error) {
      console.error('Error sending subscription to server:', error)
    }
  }

  // Convert VAPID key
  private urlB64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
  }

  // Get cache storage usage
  async getCacheStorageUsage(): Promise<{ used: number; available: number }> {
    if (!('storage' in navigator)) {
      return { used: 0, available: 0 }
    }

    try {
      const estimate = await navigator.storage.estimate()
      return {
        used: estimate.usage || 0,
        available: estimate.quota || 0
      }
    } catch (error) {
      console.error('Error getting cache storage usage:', error)
      return { used: 0, available: 0 }
    }
  }

  // Clear cache storage
  async clearCacheStorage(): Promise<void> {
    try {
      const cacheNames = await caches.keys()
      await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      )
      console.log('Cache storage cleared')
      this.emit('cacheCleared')
    } catch (error) {
      console.error('Error clearing cache storage:', error)
    }
  }

  // Check if app is running in standalone mode
  isStandalone(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches ||
           ('standalone' in navigator && (navigator as any).standalone)
  }

  // Get network status
  getNetworkStatus(): { online: boolean; connection?: any } {
    return {
      online: navigator.onLine,
      connection: (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
    }
  }

  // Event listener management
  on(event: string, callback: Function): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push(callback)
  }

  off(event: string, callback: Function): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  private emit(event: string, data?: any): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(callback => callback(data))
    }
  }

  // Get current update info
  getUpdateInfo(): UpdateInfo {
    return { ...this.updateInfo }
  }

  // Unregister service worker
  async unregister(): Promise<void> {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.ready
      await registration.unregister()
      console.log('Service Worker unregistered')
    }
  }
}

// Create singleton instance
export const serviceWorkerManager = new ServiceWorkerManager()

// Convenience functions
export const initServiceWorker = (config?: Partial<ServiceWorkerConfig>) => {
  return serviceWorkerManager.init()
}

export const checkForUpdates = () => {
  return serviceWorkerManager.checkForUpdates()
}

export const skipWaiting = () => {
  return serviceWorkerManager.skipWaiting()
}

export const registerPushNotifications = () => {
  return serviceWorkerManager.registerPushNotifications()
}

export const getCacheStorageUsage = () => {
  return serviceWorkerManager.getCacheStorageUsage()
}

export const clearCacheStorage = () => {
  return serviceWorkerManager.clearCacheStorage()
}

export const isStandalone = () => {
  return serviceWorkerManager.isStandalone()
}

export const getNetworkStatus = () => {
  return serviceWorkerManager.getNetworkStatus()
}

// React hook for service worker
export const useServiceWorker = () => {
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo>(serviceWorkerManager.getUpdateInfo())
  const [networkStatus, setNetworkStatus] = useState(getNetworkStatus())
  const [cacheUsage, setCacheUsage] = useState({ used: 0, available: 0 })

  useEffect(() => {
    const handleUpdate = () => {
      setUpdateInfo(serviceWorkerManager.getUpdateInfo())
    }

    const handleNetworkChange = () => {
      setNetworkStatus(getNetworkStatus())
    }

    // Set up event listeners
    serviceWorkerManager.on('waiting', handleUpdate)
    serviceWorkerManager.on('activated', handleUpdate)
    serviceWorkerManager.on('cacheUpdated', handleUpdate)

    window.addEventListener('online', handleNetworkChange)
    window.addEventListener('offline', handleNetworkChange)

    // Get initial cache usage
    getCacheStorageUsage().then(setCacheUsage)

    // Cleanup
    return () => {
      serviceWorkerManager.off('waiting', handleUpdate)
      serviceWorkerManager.off('activated', handleUpdate)
      serviceWorkerManager.off('cacheUpdated', handleUpdate)
      window.removeEventListener('online', handleNetworkChange)
      window.removeEventListener('offline', handleNetworkChange)
    }
  }, [])

  return {
    updateInfo,
    networkStatus,
    cacheUsage,
    checkForUpdates,
    skipWaiting,
    registerPushNotifications,
    clearCacheStorage,
    isStandalone: isStandalone()
  }
}