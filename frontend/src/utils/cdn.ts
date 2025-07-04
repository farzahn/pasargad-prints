// CDN Configuration and Asset Optimization Utilities

interface CDNConfig {
  baseUrl: string;
  staticUrl: string;
  enableOptimization: boolean;
  enableWebP: boolean;
  enableAVIF: boolean;
  enableLazyLoading: boolean;
  enableCompression: boolean;
  enableCacheBusting: boolean;
  supportedFormats: string[];
  defaultQuality: number;
}

interface ImageOptimizationOptions {
  width?: number;
  height?: number;
  quality?: number;
  format?: 'webp' | 'avif' | 'jpeg' | 'png' | 'auto';
  fit?: 'cover' | 'contain' | 'fill' | 'inside' | 'outside';
  blur?: number;
  sharpen?: boolean;
  grayscale?: boolean;
  progressive?: boolean;
}

// Get CDN configuration based on environment
export const getCDNConfig = (): CDNConfig => {
  const cdnUrl = import.meta.env.VITE_CDN_URL || '';
  const staticUrl = import.meta.env.VITE_STATIC_URL || '';
  const enableOptimization = import.meta.env.VITE_OPTIMIZE_IMAGES === 'true';
  const enableWebP = import.meta.env.VITE_ENABLE_WEBP !== 'false'; // Default to true
  const enableAVIF = import.meta.env.VITE_ENABLE_AVIF === 'true';
  const enableLazyLoading = import.meta.env.VITE_LAZY_LOAD_IMAGES === 'true';
  const enableCompression = import.meta.env.VITE_ENABLE_COMPRESSION === 'true';
  const enableCacheBusting = import.meta.env.VITE_CACHE_BUSTING === 'true';

  return {
    baseUrl: cdnUrl,
    staticUrl: staticUrl,
    enableOptimization,
    enableWebP,
    enableAVIF,
    enableLazyLoading,
    enableCompression,
    enableCacheBusting,
    supportedFormats: ['avif', 'webp', 'jpeg', 'png'],
    defaultQuality: 80
  };
};

// Generate optimized image URL
export const getOptimizedImageUrl = (
  originalUrl: string,
  options: {
    width?: number;
    height?: number;
    quality?: number;
    format?: 'webp' | 'avif' | 'jpeg' | 'png';
    fit?: 'cover' | 'contain' | 'fill';
  } = {}
): string => {
  const config = getCDNConfig();
  
  if (!config.enableOptimization || !config.baseUrl) {
    return originalUrl;
  }

  const {
    width,
    height,
    quality = 80,
    format = 'webp',
    fit = 'cover'
  } = options;

  // If the URL is already absolute, return as-is
  if (originalUrl.startsWith('http')) {
    return originalUrl;
  }

  // Build optimization parameters
  const params = new URLSearchParams();
  
  if (width) params.append('w', width.toString());
  if (height) params.append('h', height.toString());
  if (quality) params.append('q', quality.toString());
  if (format && config.enableWebP) params.append('f', format);
  if (fit) params.append('fit', fit);

  const optimizedUrl = `${config.baseUrl}/optimize/${originalUrl.replace(/^\//, '')}`;
  return params.toString() ? `${optimizedUrl}?${params.toString()}` : optimizedUrl;
};

// Generate responsive image srcset
export const getResponsiveImageSrcSet = (
  originalUrl: string,
  sizes: number[] = [320, 640, 768, 1024, 1280, 1536],
  options: {
    quality?: number;
    format?: 'webp' | 'avif' | 'jpeg' | 'png';
  } = {}
): string => {
  const config = getCDNConfig();
  
  if (!config.enableOptimization) {
    return originalUrl;
  }

  return sizes
    .map(size => 
      `${getOptimizedImageUrl(originalUrl, { width: size, ...options })} ${size}w`
    )
    .join(', ');
};

// Asset URL helper
export const getAssetUrl = (path: string): string => {
  const config = getCDNConfig();
  
  if (!config.staticUrl) {
    return path;
  }

  // If the path is already absolute, return as-is
  if (path.startsWith('http')) {
    return path;
  }

  return `${config.staticUrl}${path.startsWith('/') ? '' : '/'}${path}`;
};

// Preload critical assets
export const preloadCriticalAssets = (assets: string[]) => {
  if (!import.meta.env.VITE_PRELOAD_CRITICAL_ASSETS) {
    return;
  }

  assets.forEach(asset => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = getAssetUrl(asset);
    
    // Determine the type based on file extension
    const extension = asset.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'css':
        link.as = 'style';
        break;
      case 'js':
        link.as = 'script';
        break;
      case 'woff':
      case 'woff2':
        link.as = 'font';
        link.type = `font/${extension}`;
        link.crossOrigin = 'anonymous';
        break;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'webp':
      case 'avif':
        link.as = 'image';
        break;
      default:
        return; // Skip unknown types
    }
    
    document.head.appendChild(link);
  });
};

// Cache management
export const getCacheHeaders = (assetType: string): Record<string, string> => {
  const headers: Record<string, string> = {};
  
  switch (assetType) {
    case 'image':
      headers['Cache-Control'] = 'public, max-age=31536000, immutable'; // 1 year
      break;
    case 'font':
      headers['Cache-Control'] = 'public, max-age=31536000, immutable'; // 1 year
      break;
    case 'css':
    case 'js':
      headers['Cache-Control'] = 'public, max-age=31536000, immutable'; // 1 year
      break;
    case 'html':
      headers['Cache-Control'] = 'public, max-age=300'; // 5 minutes
      break;
    default:
      headers['Cache-Control'] = 'public, max-age=86400'; // 1 day
  }
  
  return headers;
};

// Service Worker registration for offline support
export const registerServiceWorker = async (): Promise<void> => {
  if (!import.meta.env.VITE_ENABLE_SERVICE_WORKER || !('serviceWorker' in navigator)) {
    return;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js');
    console.log('Service Worker registered:', registration);
  } catch (error) {
    console.error('Service Worker registration failed:', error);
  }
};

// Browser capability detection
export const getBrowserCapabilities = () => {
  const canvas = document.createElement('canvas');
  const supportsWebP = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  
  const supportsAVIF = (() => {
    try {
      const canvas = document.createElement('canvas');
      return canvas.toDataURL('image/avif').indexOf('data:image/avif') === 0;
    } catch {
      return false;
    }
  })();

  return {
    webp: supportsWebP,
    avif: supportsAVIF,
    webgl: !!document.createElement('canvas').getContext('webgl'),
    intersectionObserver: 'IntersectionObserver' in window,
    serviceWorker: 'serviceWorker' in navigator,
    pushManager: 'PushManager' in window
  };
};

// Auto-detect best image format
export const getBestImageFormat = (): 'avif' | 'webp' | 'jpeg' => {
  const capabilities = getBrowserCapabilities();
  const config = getCDNConfig();
  
  if (config.enableAVIF && capabilities.avif) {
    return 'avif';
  }
  if (config.enableWebP && capabilities.webp) {
    return 'webp';
  }
  return 'jpeg';
};

// Enhanced image optimization with auto-format detection
export const getSmartOptimizedImageUrl = (
  originalUrl: string,
  options: ImageOptimizationOptions = {}
): string => {
  const config = getCDNConfig();
  
  if (!config.enableOptimization || !config.baseUrl) {
    return originalUrl;
  }

  const bestFormat = options.format === 'auto' ? getBestImageFormat() : options.format;
  
  return getOptimizedImageUrl(originalUrl, {
    ...options,
    format: bestFormat,
    quality: options.quality || config.defaultQuality
  });
};

// Critical resource hints
export const addResourceHints = () => {
  const config = getCDNConfig();
  
  if (config.baseUrl) {
    // DNS prefetch for CDN
    const dnsPrefetch = document.createElement('link');
    dnsPrefetch.rel = 'dns-prefetch';
    dnsPrefetch.href = config.baseUrl;
    document.head.appendChild(dnsPrefetch);
    
    // Preconnect to CDN
    const preconnect = document.createElement('link');
    preconnect.rel = 'preconnect';
    preconnect.href = config.baseUrl;
    preconnect.crossOrigin = 'anonymous';
    document.head.appendChild(preconnect);
  }
  
  // Preconnect to Google Fonts
  const fontsPrefetch = document.createElement('link');
  fontsPrefetch.rel = 'preconnect';
  fontsPrefetch.href = 'https://fonts.googleapis.com';
  document.head.appendChild(fontsPrefetch);
  
  const fontsGstatic = document.createElement('link');
  fontsGstatic.rel = 'preconnect';
  fontsGstatic.href = 'https://fonts.gstatic.com';
  fontsGstatic.crossOrigin = 'anonymous';
  document.head.appendChild(fontsGstatic);
};

// Image lazy loading with intersection observer
export class LazyImageLoader {
  private observer: IntersectionObserver | null = null;
  private images: Set<HTMLImageElement> = new Set();

  constructor(options: IntersectionObserverInit = {}) {
    const capabilities = getBrowserCapabilities();
    
    if (capabilities.intersectionObserver) {
      this.observer = new IntersectionObserver(this.handleIntersection.bind(this), {
        rootMargin: '50px 0px',
        threshold: 0.01,
        ...options
      });
    }
  }

  private handleIntersection(entries: IntersectionObserverEntry[]) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        this.loadImage(img);
        this.observer?.unobserve(img);
        this.images.delete(img);
      }
    });
  }

  private loadImage(img: HTMLImageElement) {
    const src = img.dataset.src;
    const srcset = img.dataset.srcset;
    
    if (src) {
      img.src = src;
      img.removeAttribute('data-src');
    }
    
    if (srcset) {
      img.srcset = srcset;
      img.removeAttribute('data-srcset');
    }
    
    img.classList.remove('lazy');
    img.classList.add('loaded');
  }

  observe(img: HTMLImageElement) {
    if (this.observer && !this.images.has(img)) {
      this.images.add(img);
      this.observer.observe(img);
    } else {
      // Fallback for browsers without IntersectionObserver
      this.loadImage(img);
    }
  }

  disconnect() {
    this.observer?.disconnect();
    this.images.clear();
  }
}

// Global lazy loader instance
export const lazyLoader = new LazyImageLoader();

// Performance monitoring for CDN assets
export const monitorCDNPerformance = () => {
  if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.name.includes(getCDNConfig().baseUrl)) {
          console.debug('CDN Asset Performance:', {
            name: entry.name,
            duration: entry.duration,
            transferSize: (entry as any).transferSize,
            decodedBodySize: (entry as any).decodedBodySize
          });
        }
      });
    });
    
    observer.observe({ entryTypes: ['resource'] });
  }
};

// Initialize CDN utilities
export const initializeCDN = () => {
  addResourceHints();
  
  if (import.meta.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true') {
    monitorCDNPerformance();
  }
  
  // Initialize service worker
  registerServiceWorker();
};