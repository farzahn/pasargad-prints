// Security Headers and Content Security Policy Configuration

export interface SecurityConfig {
  contentSecurityPolicy: {
    directives: Record<string, string[]>;
    reportOnly: boolean;
    reportUri?: string;
  };
  headers: Record<string, string>;
  environment: 'development' | 'staging' | 'production';
}

// Generate Content Security Policy
export const generateCSP = (config: SecurityConfig): string => {
  const { directives } = config.contentSecurityPolicy;
  
  const cspString = Object.entries(directives)
    .map(([directive, sources]) => `${directive} ${sources.join(' ')}`)
    .join('; ');
    
  return cspString;
};

// Default security configuration
export const getSecurityConfig = (): SecurityConfig => {
  const environment = (import.meta.env.VITE_APP_ENV || 'development') as 'development' | 'staging' | 'production';
  const isDevelopment = environment === 'development';
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const cdnUrl = import.meta.env.VITE_CDN_URL || '';
  const staticUrl = import.meta.env.VITE_STATIC_URL || '';

  return {
    environment,
    contentSecurityPolicy: {
      reportOnly: isDevelopment,
      reportUri: isDevelopment ? undefined : '/api/csp-report',
      directives: {
        'default-src': ["'self'"],
        'script-src': [
          "'self'",
          "'unsafe-inline'", // Required for some React functionality
          "'unsafe-eval'", // Required for development builds
          'https://www.google-analytics.com',
          'https://www.googletagmanager.com',
          'https://js.stripe.com',
          ...(isDevelopment ? ["'unsafe-eval'"] : [])
        ],
        'style-src': [
          "'self'",
          "'unsafe-inline'", // Required for CSS-in-JS and dynamic styles
          'https://fonts.googleapis.com'
        ],
        'img-src': [
          "'self'",
          'data:',
          'blob:',
          'https:',
          ...(cdnUrl ? [cdnUrl] : []),
          ...(staticUrl ? [staticUrl] : []),
          'https://www.google-analytics.com',
          'https://www.googletagmanager.com'
        ],
        'font-src': [
          "'self'",
          'https://fonts.gstatic.com',
          ...(cdnUrl ? [cdnUrl] : []),
          ...(staticUrl ? [staticUrl] : [])
        ],
        'connect-src': [
          "'self'",
          apiUrl,
          'https://www.google-analytics.com',
          'https://analytics.google.com',
          'https://api.stripe.com',
          ...(cdnUrl ? [cdnUrl] : []),
          ...(staticUrl ? [staticUrl] : []),
          ...(isDevelopment ? ['ws:', 'wss:'] : []) // WebSocket for HMR
        ],
        'frame-src': [
          "'self'",
          'https://js.stripe.com',
          'https://hooks.stripe.com'
        ],
        'object-src': ["'none'"],
        'media-src': [
          "'self'",
          ...(cdnUrl ? [cdnUrl] : []),
          ...(staticUrl ? [staticUrl] : [])
        ],
        'worker-src': [
          "'self'",
          'blob:'
        ],
        'child-src': [
          "'self'",
          'blob:'
        ],
        'form-action': [
          "'self'",
          apiUrl
        ],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'manifest-src': ["'self'"]
      }
    },
    headers: {
      // Content Security Policy
      'Content-Security-Policy': '', // Will be filled by generateCSP
      
      // Strict Transport Security
      'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
      
      // X-Frame-Options (defense in depth with CSP frame-ancestors)
      'X-Frame-Options': 'DENY',
      
      // X-Content-Type-Options
      'X-Content-Type-Options': 'nosniff',
      
      // X-XSS-Protection
      'X-XSS-Protection': '1; mode=block',
      
      // Referrer Policy
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      
      // Permissions Policy (formerly Feature Policy)
      'Permissions-Policy': [
        'camera=()',
        'microphone=()',
        'geolocation=()',
        'interest-cohort=()',
        'payment=(self)',
        'usb=()',
        'fullscreen=(self)'
      ].join(', '),
      
      // X-DNS-Prefetch-Control
      'X-DNS-Prefetch-Control': 'on',
      
      // X-Download-Options
      'X-Download-Options': 'noopen',
      
      // X-Permitted-Cross-Domain-Policies
      'X-Permitted-Cross-Domain-Policies': 'none',
      
      // Cross-Origin Embedder Policy
      'Cross-Origin-Embedder-Policy': isDevelopment ? 'unsafe-none' : 'require-corp',
      
      // Cross-Origin Opener Policy
      'Cross-Origin-Opener-Policy': 'same-origin',
      
      // Cross-Origin Resource Policy
      'Cross-Origin-Resource-Policy': 'same-origin'
    }
  };
};

// Apply security headers to the document
export const applySecurityHeaders = (): void => {
  const config = getSecurityConfig();
  const csp = generateCSP(config);
  
  // Update CSP in config
  config.headers['Content-Security-Policy'] = csp;
  
  // Apply CSP via meta tag (as fallback)
  const existingCSP = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
  if (existingCSP) {
    existingCSP.setAttribute('content', csp);
  } else {
    const meta = document.createElement('meta');
    meta.setAttribute('http-equiv', 'Content-Security-Policy');
    meta.setAttribute('content', csp);
    document.head.appendChild(meta);
  }
  
  console.log('Applied Content Security Policy:', csp);
};

// Security audit functions
export interface SecurityAuditResult {
  score: number;
  issues: SecurityIssue[];
  recommendations: string[];
}

export interface SecurityIssue {
  severity: 'high' | 'medium' | 'low';
  category: 'csp' | 'headers' | 'mixed-content' | 'external-resources' | 'permissions';
  message: string;
  recommendation: string;
}

export const auditSecurity = (): SecurityAuditResult => {
  const issues: SecurityIssue[] = [];
  const recommendations: string[] = [];
  
  // Check for HTTPS
  if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
    issues.push({
      severity: 'high',
      category: 'mixed-content',
      message: 'Site not served over HTTPS',
      recommendation: 'Enable HTTPS to ensure secure data transmission'
    });
  }
  
  // Check for mixed content
  const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
  const mixedContent = resources.filter(resource => 
    window.location.protocol === 'https:' && resource.name.startsWith('http:')
  );
  
  if (mixedContent.length > 0) {
    issues.push({
      severity: 'high',
      category: 'mixed-content',
      message: `Found ${mixedContent.length} mixed content resources`,
      recommendation: 'Update all HTTP resources to use HTTPS'
    });
  }
  
  // Check for inline scripts (basic check)
  const inlineScripts = document.querySelectorAll('script:not([src])');
  if (inlineScripts.length > 0) {
    issues.push({
      severity: 'medium',
      category: 'csp',
      message: `Found ${inlineScripts.length} inline scripts`,
      recommendation: 'Move inline scripts to external files or use nonces/hashes in CSP'
    });
  }
  
  // Check for external resources
  const externalResources = resources.filter(resource => {
    const url = new URL(resource.name);
    return url.hostname !== window.location.hostname;
  });
  
  const untrustedDomains = externalResources
    .map(r => new URL(r.name).hostname)
    .filter(hostname => !isTrustedDomain(hostname));
  
  if (untrustedDomains.length > 0) {
    issues.push({
      severity: 'medium',
      category: 'external-resources',
      message: `Resources loaded from potentially untrusted domains: ${[...new Set(untrustedDomains)].join(', ')}`,
      recommendation: 'Review external dependencies and ensure they are from trusted sources'
    });
  }
  
  // Check for security headers
  const criticalHeaders = [
    'Content-Security-Policy',
    'X-Frame-Options',
    'X-Content-Type-Options',
    'Strict-Transport-Security'
  ];
  
  // Note: In a real application, you'd check response headers
  // This is a simplified check for demonstration
  
  // Generate recommendations
  if (issues.length === 0) {
    recommendations.push('Security configuration looks good!');
  } else {
    recommendations.push('Review and address the identified security issues');
    recommendations.push('Implement a comprehensive Content Security Policy');
    recommendations.push('Enable all security headers on the server');
    recommendations.push('Regularly audit third-party dependencies');
    recommendations.push('Implement Subresource Integrity (SRI) for external resources');
  }
  
  const score = Math.max(0, 100 - (issues.length * 10));
  
  return {
    score,
    issues,
    recommendations
  };
};

// Check if domain is trusted
const isTrustedDomain = (domain: string): boolean => {
  const trustedDomains = [
    'google-analytics.com',
    'googletagmanager.com',
    'fonts.googleapis.com',
    'fonts.gstatic.com',
    'stripe.com',
    'js.stripe.com',
    'api.stripe.com',
    'hooks.stripe.com',
    'cdnjs.cloudflare.com',
    'unpkg.com'
  ];
  
  return trustedDomains.some(trusted => 
    domain === trusted || domain.endsWith(`.${trusted}`)
  );
};

// Subresource Integrity (SRI) helper
export const generateSRIHash = async (url: string): Promise<string> => {
  try {
    const response = await fetch(url);
    const content = await response.text();
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest('SHA-384', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashBase64 = btoa(String.fromCharCode(...hashArray));
    return `sha384-${hashBase64}`;
  } catch (error) {
    console.error('Failed to generate SRI hash:', error);
    return '';
  }
};

// Add SRI to external scripts
export const addSRIToExternalScripts = async (): Promise<void> => {
  const externalScripts = document.querySelectorAll('script[src]:not([integrity])');
  
  for (const script of externalScripts) {
    const src = script.getAttribute('src');
    if (src && src.startsWith('https://')) {
      try {
        const hash = await generateSRIHash(src);
        if (hash) {
          script.setAttribute('integrity', hash);
          script.setAttribute('crossorigin', 'anonymous');
        }
      } catch (error) {
        console.warn(`Failed to add SRI to script: ${src}`, error);
      }
    }
  }
};

// Input validation helpers
export const sanitizeInput = (input: string): string => {
  // Basic HTML escaping
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
};

export const validateURL = (url: string): boolean => {
  try {
    const parsedUrl = new URL(url);
    return ['http:', 'https:'].includes(parsedUrl.protocol);
  } catch {
    return false;
  }
};

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Rate limiting helper (client-side)
export class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  
  constructor(
    private maxRequests: number = 100,
    private windowMs: number = 60000 // 1 minute
  ) {}
  
  isAllowed(identifier: string): boolean {
    const now = Date.now();
    const requests = this.requests.get(identifier) || [];
    
    // Remove old requests outside the window
    const validRequests = requests.filter(time => now - time < this.windowMs);
    
    if (validRequests.length >= this.maxRequests) {
      return false;
    }
    
    validRequests.push(now);
    this.requests.set(identifier, validRequests);
    return true;
  }
  
  reset(identifier: string): void {
    this.requests.delete(identifier);
  }
}

// Create rate limiter instance
export const globalRateLimiter = new RateLimiter();

// React hook for security
export const useSecurity = () => {
  const sanitize = sanitizeInput;
  const validateUrl = validateURL;
  const validateEmailAddress = validateEmail;
  const checkRateLimit = (identifier: string) => globalRateLimiter.isAllowed(identifier);
  
  const reportSecurityIssue = (issue: {
    type: string;
    message: string;
    url?: string;
    userAgent?: string;
  }) => {
    // Report security issues to server
    fetch('/api/security/report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...issue,
        timestamp: Date.now(),
        url: issue.url || window.location.href,
        userAgent: issue.userAgent || navigator.userAgent
      })
    }).catch(error => {
      console.error('Failed to report security issue:', error);
    });
  };
  
  return {
    sanitize,
    validateUrl,
    validateEmailAddress,
    checkRateLimit,
    reportSecurityIssue,
    auditSecurity
  };
};