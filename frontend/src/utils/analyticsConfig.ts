// Production Analytics Configuration
import { analytics, initAnalytics } from './analytics';

// Analytics configuration based on environment
export interface AnalyticsEnvironmentConfig {
  googleAnalyticsId: string;
  googleTagManagerId: string;
  hotjarId: string;
  sentryDsn: string;
  enableAnalytics: boolean;
  enablePerformanceMonitoring: boolean;
  enableErrorTracking: boolean;
  enableHeatmaps: boolean;
  enableSessionRecording: boolean;
  enableUserFeedback: boolean;
  environment: 'development' | 'staging' | 'production';
  debugMode: boolean;
}

// Get analytics configuration from environment variables
export const getAnalyticsConfig = (): AnalyticsEnvironmentConfig => {
  const isProduction = import.meta.env.VITE_NODE_ENV === 'production';
  const enableAnalytics = import.meta.env.VITE_ENABLE_ANALYTICS === 'true';
  
  return {
    googleAnalyticsId: import.meta.env.VITE_GOOGLE_ANALYTICS_ID || '',
    googleTagManagerId: import.meta.env.VITE_GOOGLE_TAG_MANAGER_ID || '',
    hotjarId: import.meta.env.VITE_HOTJAR_ID || '',
    sentryDsn: import.meta.env.VITE_SENTRY_DSN || '',
    enableAnalytics: enableAnalytics && isProduction,
    enablePerformanceMonitoring: import.meta.env.VITE_ENABLE_PERFORMANCE_MONITORING === 'true' && isProduction,
    enableErrorTracking: import.meta.env.VITE_ENABLE_ERROR_TRACKING === 'true',
    enableHeatmaps: import.meta.env.VITE_ENABLE_HEATMAPS === 'true' && isProduction,
    enableSessionRecording: import.meta.env.VITE_ENABLE_SESSION_RECORDING === 'true' && isProduction,
    enableUserFeedback: import.meta.env.VITE_ENABLE_USER_FEEDBACK === 'true',
    environment: import.meta.env.VITE_NODE_ENV as 'development' | 'staging' | 'production' || 'development',
    debugMode: import.meta.env.VITE_ANALYTICS_DEBUG === 'true' && !isProduction
  };
};

// Initialize Hotjar for heatmaps and user behavior analysis
export const initializeHotjar = () => {
  const config = getAnalyticsConfig();
  
  if (!config.enableHeatmaps || !config.hotjarId) {
    return;
  }

  try {
    (function(h: any, o: any, t: any, j: any, a?: any, r?: any) {
      h.hj = h.hj || function(...args: any[]) { 
        (h.hj.q = h.hj.q || []).push(args);
      };
      h._hjSettings = { hjid: parseInt(config.hotjarId), hjsv: 6 };
      a = o.getElementsByTagName('head')[0];
      r = o.createElement('script');
      r.async = 1;
      r.src = t + h._hjSettings.hjid + j + h._hjSettings.hjsv;
      a.appendChild(r);
    })(window, document, 'https://static.hotjar.com/c/hotjar-', '.js?sv=');

    if (config.debugMode) {
      console.log('Hotjar initialized with ID:', config.hotjarId);
    }
  } catch (error) {
    console.error('Failed to initialize Hotjar:', error);
  }
};

// Initialize Sentry for error tracking
export const initializeSentry = async () => {
  const config = getAnalyticsConfig();
  
  if (!config.enableErrorTracking || !config.sentryDsn) {
    return;
  }

  try {
    // Dynamic import to avoid loading Sentry in development
    const { init, configureScope, setUser, setTag } = await import('@sentry/browser');
    
    init({
      dsn: config.sentryDsn,
      environment: config.environment,
      enabled: config.enableErrorTracking,
      debug: config.debugMode,
      tracesSampleRate: config.environment === 'production' ? 0.1 : 1.0,
      beforeSend(event) {
        // Filter out non-production errors in staging
        if (config.environment === 'staging' && event.level === 'error') {
          return null;
        }
        return event;
      },
      integrations: [
        // Add performance monitoring
        new (await import('@sentry/browser')).BrowserTracing({
          tracingOrigins: [window.location.hostname]
        })
      ]
    });

    // Set user context
    configureScope((scope) => {
      scope.setTag('app.version', import.meta.env.VITE_APP_VERSION || '1.0.0');
      scope.setTag('app.environment', config.environment);
      
      // Set user ID if available
      const userId = localStorage.getItem('user_id');
      if (userId) {
        setUser({ id: userId });
      }
    });

    if (config.debugMode) {
      console.log('Sentry initialized for environment:', config.environment);
    }
  } catch (error) {
    console.error('Failed to initialize Sentry:', error);
  }
};

// Facebook Pixel integration
export const initializeFacebookPixel = () => {
  const config = getAnalyticsConfig();
  const facebookAppId = import.meta.env.VITE_FACEBOOK_APP_ID;
  
  if (!config.enableAnalytics || !facebookAppId) {
    return;
  }

  try {
    (function(f: any, b: any, e: any, v: any, n?: any, t?: any, s?: any) {
      if (f.fbq) return;
      n = f.fbq = function(...args: any[]) {
        n.callMethod ? n.callMethod.apply(n, args) : n.queue.push(args);
      };
      if (!f._fbq) f._fbq = n;
      n.push = n;
      n.loaded = true;
      n.version = '2.0';
      n.queue = [];
      t = b.createElement(e);
      t.async = true;
      t.src = v;
      s = b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t, s);
    })(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');

    (window as any).fbq('init', facebookAppId);
    (window as any).fbq('track', 'PageView');

    if (config.debugMode) {
      console.log('Facebook Pixel initialized with App ID:', facebookAppId);
    }
  } catch (error) {
    console.error('Failed to initialize Facebook Pixel:', error);
  }
};

// LinkedIn Insight Tag
export const initializeLinkedInInsight = () => {
  const config = getAnalyticsConfig();
  const linkedinId = import.meta.env.VITE_LINKEDIN_COMPANY_ID;
  
  if (!config.enableAnalytics || !linkedinId) {
    return;
  }

  try {
    (window as any)._linkedin_partner_id = linkedinId;
    (window as any)._linkedin_data_partner_ids = (window as any)._linkedin_data_partner_ids || [];
    (window as any)._linkedin_data_partner_ids.push(linkedinId);

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.async = true;
    script.src = 'https://snap.licdn.com/li.lms-analytics/insight.min.js';
    document.head.appendChild(script);

    if (config.debugMode) {
      console.log('LinkedIn Insight Tag initialized with ID:', linkedinId);
    }
  } catch (error) {
    console.error('Failed to initialize LinkedIn Insight Tag:', error);
  }
};

// Cookie consent management
export const initializeCookieConsent = () => {
  const config = getAnalyticsConfig();
  
  if (!config.enableAnalytics) {
    return;
  }

  // Check if user has already given consent
  const hasConsent = localStorage.getItem('cookie_consent') === 'true';
  
  if (!hasConsent) {
    // Show cookie consent banner
    showCookieConsentBanner();
  } else {
    // Initialize all analytics tools
    initializeAllAnalytics();
  }
};

// Show cookie consent banner
const showCookieConsentBanner = () => {
  const banner = document.createElement('div');
  banner.id = 'cookie-consent-banner';
  banner.innerHTML = `
    <div style="
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: #2d3748;
      color: white;
      padding: 1rem;
      z-index: 10000;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: system-ui, -apple-system, sans-serif;
      box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    ">
      <div style="flex: 1; margin-right: 1rem;">
        <p style="margin: 0; font-size: 14px;">
          We use cookies to improve your experience and analyze site usage. 
          <a href="/privacy" style="color: #60a5fa; text-decoration: underline;">Learn more</a>
        </p>
      </div>
      <div style="display: flex; gap: 0.5rem;">
        <button id="cookie-accept" style="
          background: #3b82f6;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        ">Accept</button>
        <button id="cookie-decline" style="
          background: transparent;
          color: #d1d5db;
          border: 1px solid #6b7280;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        ">Decline</button>
      </div>
    </div>
  `;

  document.body.appendChild(banner);

  // Handle consent
  document.getElementById('cookie-accept')?.addEventListener('click', () => {
    localStorage.setItem('cookie_consent', 'true');
    banner.remove();
    initializeAllAnalytics();
  });

  document.getElementById('cookie-decline')?.addEventListener('click', () => {
    localStorage.setItem('cookie_consent', 'false');
    banner.remove();
  });
};

// Initialize all analytics tools
export const initializeAllAnalytics = () => {
  const config = getAnalyticsConfig();
  
  if (!config.enableAnalytics) {
    if (config.debugMode) {
      console.log('Analytics disabled by configuration');
    }
    return;
  }

  // Initialize Google Analytics and GTM
  initAnalytics();
  
  // Initialize other analytics tools
  initializeHotjar();
  initializeSentry();
  initializeFacebookPixel();
  initializeLinkedInInsight();

  if (config.debugMode) {
    console.log('All analytics tools initialized for environment:', config.environment);
  }
};

// Enhanced e-commerce tracking for production
export const trackProductPurchase = (
  transactionId: string,
  items: Array<{
    id: string;
    name: string;
    category: string;
    price: number;
    quantity: number;
  }>,
  value: number,
  currency: string = 'USD'
) => {
  const config = getAnalyticsConfig();
  
  if (!config.enableAnalytics) return;

  // Track in Google Analytics
  analytics.trackEcommerce({
    event: 'purchase',
    currency,
    value,
    items: items.map(item => ({
      item_id: item.id,
      item_name: item.name,
      item_category: item.category,
      price: item.price,
      quantity: item.quantity
    })),
    transaction_id: transactionId
  });

  // Track in Facebook Pixel
  if ((window as any).fbq) {
    (window as any).fbq('track', 'Purchase', {
      value,
      currency,
      content_ids: items.map(item => item.id),
      content_type: 'product'
    });
  }

  // Track in LinkedIn (for B2B)
  if ((window as any).lintrk) {
    (window as any).lintrk('track', { conversion_id: 'purchase' });
  }
};

// Performance monitoring
export const trackPerformanceMetrics = () => {
  const config = getAnalyticsConfig();
  
  if (!config.enablePerformanceMonitoring) return;

  // Track Core Web Vitals
  if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        analytics.trackEvent({
          action: 'core_web_vitals',
          category: 'Performance',
          label: entry.name,
          value: Math.round(entry.startTime + entry.duration),
          customParameters: {
            metric_type: entry.entryType,
            metric_value: entry.startTime + entry.duration
          }
        });
      });
    });

    observer.observe({ entryTypes: ['measure', 'navigation'] });
  }
};

// Initialize analytics system
export const initializeAnalyticsSystem = () => {
  const config = getAnalyticsConfig();
  
  if (config.debugMode) {
    console.log('Analytics configuration:', config);
  }

  // Initialize cookie consent first
  initializeCookieConsent();
  
  // Set up performance monitoring
  trackPerformanceMetrics();
  
  // Track page load time
  window.addEventListener('load', () => {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    analytics.trackEvent({
      action: 'page_load_time',
      category: 'Performance',
      value: loadTime
    });
  });
};