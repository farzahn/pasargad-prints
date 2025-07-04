// Analytics and Tracking System

// Google Analytics 4 Configuration
export interface GAConfig {
  measurementId: string;
  enabled: boolean;
  trackPageViews: boolean;
  trackScrolls: boolean;
  trackOutboundLinks: boolean;
  trackFileDownloads: boolean;
}

// Custom Event Types
export interface CustomEvent {
  action: string;
  category: string;
  label?: string;
  value?: number;
  customParameters?: Record<string, any>;
}

// E-commerce Event Types
export interface EcommerceEvent {
  event: 'purchase' | 'add_to_cart' | 'remove_from_cart' | 'view_item' | 'begin_checkout' | 'add_payment_info' | 'add_shipping_info';
  currency: string;
  value: number;
  items: Array<{
    item_id: string;
    item_name: string;
    item_category: string;
    item_brand?: string;
    price: number;
    quantity: number;
  }>;
  transaction_id?: string;
  coupon?: string;
  shipping?: number;
  tax?: number;
}

// Performance Metrics
export interface PerformanceMetrics {
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  ttfb: number; // Time to First Byte
}

// User Behavior Tracking
export interface UserBehavior {
  userId?: string;
  sessionId: string;
  pageViews: number;
  timeOnSite: number;
  scrollDepth: number;
  clickEvents: Array<{
    element: string;
    timestamp: number;
    coordinates: { x: number; y: number };
  }>;
}

class AnalyticsService {
  private config: GAConfig;
  private userBehavior: UserBehavior;
  private sessionStartTime: number;
  private isInitialized = false;

  constructor() {
    this.config = {
      measurementId: import.meta.env.VITE_GOOGLE_ANALYTICS_ID || '',
      enabled: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
      trackPageViews: true,
      trackScrolls: true,
      trackOutboundLinks: true,
      trackFileDownloads: true
    };

    this.userBehavior = {
      sessionId: this.generateSessionId(),
      pageViews: 0,
      timeOnSite: 0,
      scrollDepth: 0,
      clickEvents: []
    };

    this.sessionStartTime = Date.now();
  }

  // Initialize Analytics
  async init(): Promise<void> {
    if (!this.config.enabled || !this.config.measurementId || this.isInitialized) {
      return;
    }

    try {
      // Load Google Analytics 4
      await this.loadGoogleAnalytics();
      
      // Initialize Google Tag Manager if configured
      if (import.meta.env.VITE_GOOGLE_TAG_MANAGER_ID) {
        await this.loadGoogleTagManager();
      }

      // Set up event listeners
      this.setupEventListeners();
      
      this.isInitialized = true;
      console.log('Analytics initialized successfully');
    } catch (error) {
      console.error('Failed to initialize analytics:', error);
    }
  }

  // Load Google Analytics 4
  private async loadGoogleAnalytics(): Promise<void> {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${this.config.measurementId}`;
      document.head.appendChild(script);

      script.onload = () => {
        // Initialize gtag
        (window as any).dataLayer = (window as any).dataLayer || [];
        (window as any).gtag = function() {
          (window as any).dataLayer.push(arguments);
        };

        (window as any).gtag('js', new Date());
        (window as any).gtag('config', this.config.measurementId, {
          page_title: document.title,
          page_location: window.location.href,
          anonymize_ip: true,
          allow_google_signals: false,
          allow_ad_personalization_signals: false
        });

        resolve();
      };
    });
  }

  // Load Google Tag Manager
  private async loadGoogleTagManager(): Promise<void> {
    return new Promise((resolve) => {
      const gtmId = import.meta.env.VITE_GOOGLE_TAG_MANAGER_ID;
      
      // GTM Script
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtm.js?id=${gtmId}`;
      document.head.appendChild(script);

      // GTM NoScript
      const noscript = document.createElement('noscript');
      noscript.innerHTML = `<iframe src="https://www.googletagmanager.com/ns.html?id=${gtmId}" height="0" width="0" style="display:none;visibility:hidden"></iframe>`;
      document.body.appendChild(noscript);

      // Initialize dataLayer
      (window as any).dataLayer = (window as any).dataLayer || [];
      (window as any).dataLayer.push({
        'gtm.start': new Date().getTime(),
        event: 'gtm.js'
      });

      resolve();
    });
  }

  // Set up event listeners
  private setupEventListeners(): void {
    // Track page views
    if (this.config.trackPageViews) {
      this.trackPageView();
    }

    // Track scroll depth
    if (this.config.trackScrolls) {
      this.setupScrollTracking();
    }

    // Track outbound links
    if (this.config.trackOutboundLinks) {
      this.setupOutboundLinkTracking();
    }

    // Track file downloads
    if (this.config.trackFileDownloads) {
      this.setupFileDownloadTracking();
    }

    // Track performance metrics
    this.setupPerformanceTracking();

    // Track user behavior
    this.setupUserBehaviorTracking();
  }

  // Track page view
  trackPageView(pagePath?: string, pageTitle?: string): void {
    if (!this.isInitialized) return;

    const path = pagePath || window.location.pathname;
    const title = pageTitle || document.title;

    if (typeof (window as any).gtag === 'function') {
      (window as any).gtag('config', this.config.measurementId, {
        page_path: path,
        page_title: title
      });
    }

    this.userBehavior.pageViews++;
  }

  // Track custom event
  trackEvent(event: CustomEvent): void {
    if (!this.isInitialized) return;

    if (typeof (window as any).gtag === 'function') {
      (window as any).gtag('event', event.action, {
        event_category: event.category,
        event_label: event.label,
        value: event.value,
        ...event.customParameters
      });
    }
  }

  // Track e-commerce event
  trackEcommerce(event: EcommerceEvent): void {
    if (!this.isInitialized) return;

    if (typeof (window as any).gtag === 'function') {
      (window as any).gtag('event', event.event, {
        currency: event.currency,
        value: event.value,
        items: event.items,
        transaction_id: event.transaction_id,
        coupon: event.coupon,
        shipping: event.shipping,
        tax: event.tax
      });
    }
  }

  // Track performance metrics
  private setupPerformanceTracking(): void {
    if ('performance' in window) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const metrics = this.getPerformanceMetrics();
          this.trackEvent({
            action: 'performance_metrics',
            category: 'Performance',
            customParameters: metrics
          });
        }, 0);
      });
    }
  }

  // Get Web Vitals metrics
  private getPerformanceMetrics(): PerformanceMetrics {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const paint = performance.getEntriesByType('paint');
    
    return {
      fcp: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
      lcp: 0, // Would need web-vitals library for accurate LCP
      fid: 0, // Would need web-vitals library for accurate FID
      cls: 0, // Would need web-vitals library for accurate CLS
      ttfb: navigation.responseStart - navigation.requestStart
    };
  }

  // Setup scroll tracking
  private setupScrollTracking(): void {
    let maxScroll = 0;
    let scrollTimer: NodeJS.Timeout;

    const trackScroll = () => {
      const scrollPercent = Math.round(
        (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100
      );
      
      if (scrollPercent > maxScroll) {
        maxScroll = scrollPercent;
        this.userBehavior.scrollDepth = maxScroll;
        
        // Track milestone scrolls
        if (maxScroll >= 25 && maxScroll < 50) {
          this.trackEvent({
            action: 'scroll_depth',
            category: 'Engagement',
            label: '25%',
            value: 25
          });
        } else if (maxScroll >= 50 && maxScroll < 75) {
          this.trackEvent({
            action: 'scroll_depth',
            category: 'Engagement',
            label: '50%',
            value: 50
          });
        } else if (maxScroll >= 75 && maxScroll < 100) {
          this.trackEvent({
            action: 'scroll_depth',
            category: 'Engagement',
            label: '75%',
            value: 75
          });
        } else if (maxScroll >= 100) {
          this.trackEvent({
            action: 'scroll_depth',
            category: 'Engagement',
            label: '100%',
            value: 100
          });
        }
      }
    };

    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(trackScroll, 100);
    });
  }

  // Setup outbound link tracking
  private setupOutboundLinkTracking(): void {
    document.addEventListener('click', (event) => {
      const link = (event.target as Element).closest('a');
      if (link && link.href) {
        const url = new URL(link.href);
        if (url.hostname !== window.location.hostname) {
          this.trackEvent({
            action: 'outbound_link',
            category: 'External Links',
            label: link.href
          });
        }
      }
    });
  }

  // Setup file download tracking
  private setupFileDownloadTracking(): void {
    const downloadExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.csv'];
    
    document.addEventListener('click', (event) => {
      const link = (event.target as Element).closest('a');
      if (link && link.href) {
        const hasDownloadExtension = downloadExtensions.some(ext => 
          link.href.toLowerCase().includes(ext)
        );
        
        if (hasDownloadExtension) {
          this.trackEvent({
            action: 'file_download',
            category: 'Downloads',
            label: link.href
          });
        }
      }
    });
  }

  // Setup user behavior tracking
  private setupUserBehaviorTracking(): void {
    // Track clicks
    document.addEventListener('click', (event) => {
      this.userBehavior.clickEvents.push({
        element: (event.target as Element).tagName,
        timestamp: Date.now(),
        coordinates: { x: event.clientX, y: event.clientY }
      });
    });

    // Track time on site
    setInterval(() => {
      this.userBehavior.timeOnSite = Date.now() - this.sessionStartTime;
    }, 30000); // Update every 30 seconds

    // Send behavior data before page unload
    window.addEventListener('beforeunload', () => {
      this.sendUserBehaviorData();
    });
  }

  // Send user behavior data
  private sendUserBehaviorData(): void {
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/analytics/behavior', JSON.stringify(this.userBehavior));
    }
  }

  // Generate session ID
  private generateSessionId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Get user ID from localStorage or generate new one
  getUserId(): string {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
      userId = this.generateSessionId();
      localStorage.setItem('user_id', userId);
    }
    return userId;
  }

  // Set user properties
  setUserProperties(properties: Record<string, any>): void {
    if (!this.isInitialized) return;

    if (typeof (window as any).gtag === 'function') {
      (window as any).gtag('config', this.config.measurementId, {
        user_properties: properties
      });
    }
  }

  // Track conversion
  trackConversion(conversionId: string, conversionLabel: string, value?: number): void {
    if (!this.isInitialized) return;

    if (typeof (window as any).gtag === 'function') {
      (window as any).gtag('event', 'conversion', {
        send_to: `${conversionId}/${conversionLabel}`,
        value: value,
        currency: 'USD'
      });
    }
  }
}

// Create singleton instance
export const analytics = new AnalyticsService();

// Convenience functions
export const trackPageView = (pagePath?: string, pageTitle?: string) => {
  analytics.trackPageView(pagePath, pageTitle);
};

export const trackEvent = (event: CustomEvent) => {
  analytics.trackEvent(event);
};

export const trackEcommerce = (event: EcommerceEvent) => {
  analytics.trackEcommerce(event);
};

export const initAnalytics = () => {
  analytics.init();
};

// React hook for analytics
export const useAnalytics = () => {
  const trackProductView = (productId: string, productName: string, category: string, price: number) => {
    trackEcommerce({
      event: 'view_item',
      currency: 'USD',
      value: price,
      items: [{
        item_id: productId,
        item_name: productName,
        item_category: category,
        price: price,
        quantity: 1
      }]
    });
  };

  const trackAddToCart = (productId: string, productName: string, category: string, price: number, quantity: number) => {
    trackEcommerce({
      event: 'add_to_cart',
      currency: 'USD',
      value: price * quantity,
      items: [{
        item_id: productId,
        item_name: productName,
        item_category: category,
        price: price,
        quantity: quantity
      }]
    });
  };

  const trackPurchase = (transactionId: string, totalValue: number, items: any[], tax?: number, shipping?: number) => {
    trackEcommerce({
      event: 'purchase',
      currency: 'USD',
      value: totalValue,
      items: items,
      transaction_id: transactionId,
      tax: tax,
      shipping: shipping
    });
  };

  return {
    trackPageView,
    trackEvent,
    trackProductView,
    trackAddToCart,
    trackPurchase
  };
};