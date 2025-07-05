// Performance Monitoring and Optimization

export interface PerformanceMetrics {
  // Core Web Vitals
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  
  // Additional metrics
  ttfb?: number; // Time to First Byte
  tti?: number; // Time to Interactive
  tbt?: number; // Total Blocking Time
  
  // Custom metrics
  loadTime?: number;
  domContentLoaded?: number;
  firstInteraction?: number;
  
  // Resource metrics
  resourceTimings?: PerformanceResourceTiming[];
  
  // Navigation metrics
  navigationTiming?: PerformanceNavigationTiming;
}

export interface PerformanceReport {
  url: string;
  timestamp: number;
  userAgent: string;
  connectionType?: string;
  metrics: PerformanceMetrics;
  errors?: Error[];
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {};
  private observers: PerformanceObserver[] = [];
  private errorLog: Error[] = [];
  private isInitialized = false;

  constructor() {
    this.initializeMonitoring();
  }

  private initializeMonitoring(): void {
    if (this.isInitialized) return;

    // Setup performance observers
    this.setupPerformanceObservers();
    
    // Setup error tracking
    this.setupErrorTracking();
    
    // Setup resource timing
    this.setupResourceTiming();
    
    // Setup navigation timing
    this.setupNavigationTiming();
    
    this.isInitialized = true;
  }

  private setupPerformanceObservers(): void {
    // First Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const fcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
          if (fcpEntry) {
            this.metrics.fcp = fcpEntry.startTime;
          }
        });
        fcpObserver.observe({ entryTypes: ['paint'] });
        this.observers.push(fcpObserver);
      } catch (e) {
        console.warn('FCP observer not supported:', e);
      }

      // Largest Contentful Paint
      try {
        const lcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const lastEntry = entries[entries.length - 1];
          if (lastEntry) {
            this.metrics.lcp = lastEntry.startTime;
          }
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported:', e);
      }

      // First Input Delay
      try {
        const fidObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const fidEntry = entries[0] as any;
          if (fidEntry) {
            this.metrics.fid = fidEntry.processingStart - fidEntry.startTime;
            this.metrics.firstInteraction = fidEntry.startTime;
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);
      } catch (e) {
        console.warn('FID observer not supported:', e);
      }

      // Cumulative Layout Shift
      try {
        const clsObserver = new PerformanceObserver((entryList) => {
          let clsValue = 0;
          for (const entry of entryList.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
          this.metrics.cls = clsValue;
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (e) {
        console.warn('CLS observer not supported:', e);
      }

      // Long Tasks (for Total Blocking Time)
      try {
        const tbtObserver = new PerformanceObserver((entryList) => {
          let tbtValue = 0;
          for (const entry of entryList.getEntries()) {
            if (entry.duration > 50) {
              tbtValue += entry.duration - 50;
            }
          }
          this.metrics.tbt = tbtValue;
        });
        tbtObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(tbtObserver);
      } catch (e) {
        console.warn('TBT observer not supported:', e);
      }
    }
  }

  private setupErrorTracking(): void {
    // Global error handler
    window.addEventListener('error', (event) => {
      this.errorLog.push(new Error(event.message));
    });

    // Promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.errorLog.push(new Error(`Unhandled promise rejection: ${event.reason}`));
    });
  }

  private setupResourceTiming(): void {
    window.addEventListener('load', () => {
      setTimeout(() => {
        this.metrics.resourceTimings = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      }, 0);
    });
  }

  private setupNavigationTiming(): void {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        this.metrics.navigationTiming = navigation;
        
        if (navigation) {
          this.metrics.ttfb = navigation.responseStart - navigation.requestStart;
          this.metrics.loadTime = navigation.loadEventEnd - (navigation as any).navigationStart;
          this.metrics.domContentLoaded = navigation.domContentLoadedEventEnd - (navigation as any).navigationStart;
        }
      }, 0);
    });
  }

  // Get current metrics
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  // Generate performance report
  generateReport(): PerformanceReport {
    return {
      url: window.location.href,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      connectionType: (navigator as any).connection?.effectiveType,
      metrics: this.getMetrics(),
      errors: [...this.errorLog]
    };
  }

  // Send performance report to server
  async sendReport(endpoint: string = '/api/performance'): Promise<void> {
    const report = this.generateReport();
    
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(endpoint, JSON.stringify(report));
      } else {
        await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(report)
        });
      }
    } catch (error) {
      console.error('Failed to send performance report:', error);
    }
  }

  // Calculate performance score
  calculateScore(): number {
    const metrics = this.getMetrics();
    let score = 100;

    // FCP scoring (0-2s = 100, 2-4s = 50, >4s = 0)
    if (metrics.fcp) {
      if (metrics.fcp > 4000) score -= 30;
      else if (metrics.fcp > 2000) score -= 15;
    }

    // LCP scoring (0-2.5s = 100, 2.5-4s = 50, >4s = 0)
    if (metrics.lcp) {
      if (metrics.lcp > 4000) score -= 30;
      else if (metrics.lcp > 2500) score -= 15;
    }

    // FID scoring (0-100ms = 100, 100-300ms = 50, >300ms = 0)
    if (metrics.fid) {
      if (metrics.fid > 300) score -= 25;
      else if (metrics.fid > 100) score -= 12;
    }

    // CLS scoring (0-0.1 = 100, 0.1-0.25 = 50, >0.25 = 0)
    if (metrics.cls) {
      if (metrics.cls > 0.25) score -= 15;
      else if (metrics.cls > 0.1) score -= 8;
    }

    return Math.max(0, score);
  }

  // Get performance grade
  getGrade(): string {
    const score = this.calculateScore();
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  // Cleanup observers
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Resource loading optimization
export class ResourceOptimizer {
  private static criticalResources: string[] = [];
  private static preloadedResources: Set<string> = new Set();

  // Preload critical resources
  static preloadResource(url: string, type: 'style' | 'script' | 'font' | 'image'): void {
    if (this.preloadedResources.has(url)) return;

    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = type;
    
    if (type === 'font') {
      link.crossOrigin = 'anonymous';
    }
    
    document.head.appendChild(link);
    this.preloadedResources.add(url);
  }

  // Lazy load images
  static lazyLoadImages(): void {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            img.src = img.dataset.src!;
            img.classList.remove('lazy');
            imageObserver.unobserve(img);
          }
        });
      });

      images.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      images.forEach(img => {
        const image = img as HTMLImageElement;
        image.src = image.dataset.src!;
        image.classList.remove('lazy');
      });
    }
  }

  // Optimize third-party scripts
  static optimizeThirdPartyScripts(): void {
    // Defer non-critical scripts
    const scripts = document.querySelectorAll('script[src]:not([async]):not([defer])');
    scripts.forEach(script => {
      const src = script.getAttribute('src');
      if (src && !this.criticalResources.includes(src)) {
        script.setAttribute('defer', '');
      }
    });
  }

  // Implement service worker for caching
  static async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }
}

// Memory usage monitoring
export interface MemoryUsage {
  timestamp: number;
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

export class MemoryMonitor {
  private memoryUsage: MemoryUsage[] = [];
  private interval: number | null = null;

  startMonitoring(intervalMs: number = 10000): void {
    if (this.interval) return;

    this.interval = window.setInterval(() => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        this.memoryUsage.push({
          timestamp: Date.now(),
          usedJSHeapSize: memory.usedJSHeapSize,
          totalJSHeapSize: memory.totalJSHeapSize,
          jsHeapSizeLimit: memory.jsHeapSizeLimit
        });
      }
    }, intervalMs);
  }

  stopMonitoring(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }

  getMemoryUsage(): MemoryUsage[] {
    return [...this.memoryUsage];
  }

  getAverageMemoryUsage(): number {
    if (this.memoryUsage.length === 0) return 0;
    const total = this.memoryUsage.reduce((sum, usage) => sum + usage.usedJSHeapSize, 0);
    return total / this.memoryUsage.length;
  }
}

// Create singleton instances
export const performanceMonitor = new PerformanceMonitor();
export const memoryMonitor = new MemoryMonitor();

// Initialize performance monitoring
export const initPerformanceMonitoring = (): void => {
  performanceMonitor.generateReport();
  memoryMonitor.startMonitoring();
  
  // Send report on page unload
  window.addEventListener('beforeunload', () => {
    performanceMonitor.sendReport();
  });
  
  // Send report after 30 seconds
  setTimeout(() => {
    performanceMonitor.sendReport();
  }, 30000);
};

// React hook for performance monitoring
export const usePerformanceMonitoring = () => {
  const getMetrics = () => performanceMonitor.getMetrics();
  const getScore = () => performanceMonitor.calculateScore();
  const getGrade = () => performanceMonitor.getGrade();
  
  return {
    getMetrics,
    getScore,
    getGrade,
    generateReport: () => performanceMonitor.generateReport()
  };
};