// Error Tracking and Monitoring System

export interface ErrorReport {
  id: string;
  timestamp: number;
  type: 'javascript' | 'network' | 'console' | 'unhandled_promise' | 'user_action';
  message: string;
  stack?: string;
  url?: string;
  line?: number;
  column?: number;
  userAgent: string;
  userId?: string;
  sessionId: string;
  breadcrumbs: Breadcrumb[];
  context: Record<string, any>;
}

export interface Breadcrumb {
  timestamp: number;
  category: 'navigation' | 'user_action' | 'network' | 'console' | 'error';
  message: string;
  level: 'info' | 'warning' | 'error';
  data?: Record<string, any>;
}

export interface ErrorContext {
  userId?: string;
  sessionId: string;
  environment: string;
  release: string;
  tags: Record<string, string>;
  extra: Record<string, any>;
}

class ErrorTracker {
  private breadcrumbs: Breadcrumb[] = [];
  private context: ErrorContext;
  private maxBreadcrumbs = 50;
  private isInitialized = false;
  private sentryDsn?: string;

  constructor() {
    this.context = {
      sessionId: this.generateSessionId(),
      environment: import.meta.env.VITE_APP_ENV || 'development',
      release: import.meta.env.VITE_APP_VERSION || '1.0.0',
      tags: {},
      extra: {}
    };

    this.sentryDsn = import.meta.env.VITE_SENTRY_DSN;
  }

  // Initialize error tracking
  init(): void {
    if (this.isInitialized) return;

    this.setupErrorHandlers();
    this.setupBreadcrumbTracking();
    
    if (this.sentryDsn) {
      this.initSentry();
    }

    this.isInitialized = true;
    console.log('Error tracking initialized');
  }

  // Setup error handlers
  private setupErrorHandlers(): void {
    // Global error handler
    window.addEventListener('error', (event) => {
      this.captureError({
        type: 'javascript',
        message: event.message,
        stack: event.error?.stack,
        url: event.filename,
        line: event.lineno,
        column: event.colno
      });
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError({
        type: 'unhandled_promise',
        message: `Unhandled promise rejection: ${event.reason}`,
        stack: event.reason?.stack
      });
    });

    // Console error tracking
    const originalConsoleError = console.error;
    console.error = (...args) => {
      this.addBreadcrumb({
        category: 'console',
        message: args.join(' '),
        level: 'error'
      });
      originalConsoleError.apply(console, args);
    };

    // Network error tracking
    this.setupNetworkErrorTracking();
  }

  // Setup network error tracking
  private setupNetworkErrorTracking(): void {
    // Fetch error tracking
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        
        if (!response.ok) {
          this.captureError({
            type: 'network',
            message: `Network error: ${response.status} ${response.statusText}`,
            url: args[0] as string
          });
        }
        
        return response;
      } catch (error) {
        this.captureError({
          type: 'network',
          message: `Fetch error: ${error}`,
          url: args[0] as string,
          stack: (error as Error).stack
        });
        throw error;
      }
    };

    // XMLHttpRequest error tracking
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, ...args) {
      (this as any)._errorTrackerMethod = method;
      (this as any)._errorTrackerUrl = url;
      return originalXHROpen.call(this, method, url, ...args);
    };

    XMLHttpRequest.prototype.send = function(...args) {
      this.addEventListener('error', () => {
        errorTracker.captureError({
          type: 'network',
          message: `XHR error: ${(this as any)._errorTrackerMethod} ${(this as any)._errorTrackerUrl}`,
          url: (this as any)._errorTrackerUrl
        });
      });

      this.addEventListener('load', () => {
        if (this.status >= 400) {
          errorTracker.captureError({
            type: 'network',
            message: `XHR error: ${this.status} ${this.statusText}`,
            url: (this as any)._errorTrackerUrl
          });
        }
      });

      return originalXHRSend.call(this, ...args);
    };
  }

  // Setup breadcrumb tracking
  private setupBreadcrumbTracking(): void {
    // Navigation breadcrumbs
    window.addEventListener('popstate', () => {
      this.addBreadcrumb({
        category: 'navigation',
        message: `Navigation to ${window.location.pathname}`,
        level: 'info',
        data: { url: window.location.href }
      });
    });

    // Click tracking
    document.addEventListener('click', (event) => {
      const target = event.target as Element;
      this.addBreadcrumb({
        category: 'user_action',
        message: `Clicked ${target.tagName}`,
        level: 'info',
        data: {
          tag: target.tagName,
          id: target.id,
          className: target.className,
          textContent: target.textContent?.slice(0, 50)
        }
      });
    });

    // Form submissions
    document.addEventListener('submit', (event) => {
      const form = event.target as HTMLFormElement;
      this.addBreadcrumb({
        category: 'user_action',
        message: 'Form submitted',
        level: 'info',
        data: {
          formId: form.id,
          action: form.action
        }
      });
    });
  }

  // Initialize Sentry (if DSN is provided)
  private async initSentry(): Promise<void> {
    try {
      // In a real implementation, you would import and configure Sentry here
      // import * as Sentry from "@sentry/browser";
      // 
      // Sentry.init({
      //   dsn: this.sentryDsn,
      //   environment: this.context.environment,
      //   release: this.context.release,
      //   beforeSend: (event) => {
      //     // Custom filtering logic
      //     return event;
      //   }
      // });

      console.log('Sentry would be initialized here with DSN:', this.sentryDsn);
    } catch (error) {
      console.error('Failed to initialize Sentry:', error);
    }
  }

  // Capture error
  captureError(errorData: Partial<ErrorReport>): void {
    const errorReport: ErrorReport = {
      id: this.generateErrorId(),
      timestamp: Date.now(),
      type: errorData.type || 'javascript',
      message: errorData.message || 'Unknown error',
      stack: errorData.stack,
      url: errorData.url,
      line: errorData.line,
      column: errorData.column,
      userAgent: navigator.userAgent,
      userId: this.context.userId,
      sessionId: this.context.sessionId,
      breadcrumbs: [...this.breadcrumbs],
      context: {
        environment: this.context.environment,
        release: this.context.release,
        tags: this.context.tags,
        extra: this.context.extra
      }
    };

    // Add error as breadcrumb
    this.addBreadcrumb({
      category: 'error',
      message: errorReport.message,
      level: 'error',
      data: {
        type: errorReport.type,
        url: errorReport.url
      }
    });

    // Send to server
    this.sendErrorReport(errorReport);

    // Log locally for debugging
    console.error('Error captured:', errorReport);
  }

  // Add breadcrumb
  addBreadcrumb(breadcrumb: Omit<Breadcrumb, 'timestamp'>): void {
    const fullBreadcrumb: Breadcrumb = {
      timestamp: Date.now(),
      ...breadcrumb
    };

    this.breadcrumbs.push(fullBreadcrumb);

    // Keep only the last N breadcrumbs
    if (this.breadcrumbs.length > this.maxBreadcrumbs) {
      this.breadcrumbs.shift();
    }
  }

  // Set user context
  setUser(userId: string, email?: string, username?: string): void {
    this.context.userId = userId;
    this.context.extra.email = email;
    this.context.extra.username = username;
  }

  // Set tags
  setTag(key: string, value: string): void {
    this.context.tags[key] = value;
  }

  // Set extra context
  setExtra(key: string, value: any): void {
    this.context.extra[key] = value;
  }

  // Send error report to server
  private async sendErrorReport(errorReport: ErrorReport): Promise<void> {
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/errors', JSON.stringify(errorReport));
      } else {
        await fetch('/api/errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorReport)
        });
      }
    } catch (error) {
      console.error('Failed to send error report:', error);
    }
  }

  // Generate unique error ID
  private generateErrorId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Generate session ID
  private generateSessionId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Get error reports for debugging
  getErrorReports(): ErrorReport[] {
    const reports = localStorage.getItem('error_reports');
    return reports ? JSON.parse(reports) : [];
  }

  // Clear stored error reports
  clearErrorReports(): void {
    localStorage.removeItem('error_reports');
  }
}

// User feedback system for errors
export class UserFeedbackCollector {
  private errorId: string | null = null;

  // Show feedback dialog for error
  showFeedbackDialog(errorId: string): void {
    this.errorId = errorId;
    
    // Create feedback modal
    const modal = document.createElement('div');
    modal.className = 'error-feedback-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <h3>Something went wrong</h3>
        <p>We've encountered an error. Your feedback helps us improve.</p>
        <textarea id="error-feedback" placeholder="What were you trying to do when this happened?"></textarea>
        <div class="modal-actions">
          <button id="send-feedback">Send Feedback</button>
          <button id="close-feedback">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Handle feedback submission
    modal.querySelector('#send-feedback')?.addEventListener('click', () => {
      const feedback = (modal.querySelector('#error-feedback') as HTMLTextAreaElement).value;
      this.submitFeedback(errorId, feedback);
      modal.remove();
    });

    // Handle close
    modal.querySelector('#close-feedback')?.addEventListener('click', () => {
      modal.remove();
    });
  }

  // Submit user feedback
  private async submitFeedback(errorId: string, feedback: string): Promise<void> {
    try {
      await fetch('/api/errors/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          errorId,
          feedback,
          timestamp: Date.now()
        })
      });
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  }
}

// Create singleton instances
export const errorTracker = new ErrorTracker();
export const feedbackCollector = new UserFeedbackCollector();

// Initialize error tracking
export const initErrorTracking = (): void => {
  errorTracker.init();
};

// Convenience functions
export const captureError = (error: Error | string, context?: Record<string, any>): void => {
  if (typeof error === 'string') {
    errorTracker.captureError({
      type: 'user_action',
      message: error,
      context
    });
  } else {
    errorTracker.captureError({
      type: 'javascript',
      message: error.message,
      stack: error.stack,
      context
    });
  }
};

export const addBreadcrumb = (breadcrumb: Omit<Breadcrumb, 'timestamp'>): void => {
  errorTracker.addBreadcrumb(breadcrumb);
};

export const setUser = (userId: string, email?: string, username?: string): void => {
  errorTracker.setUser(userId, email, username);
};

export const setTag = (key: string, value: string): void => {
  errorTracker.setTag(key, value);
};

export const setExtra = (key: string, value: any): void => {
  errorTracker.setExtra(key, value);
};

// React hook for error tracking
export const useErrorTracking = () => {
  const captureComponentError = (error: Error, errorInfo: any, componentName: string) => {
    errorTracker.captureError({
      type: 'javascript',
      message: `React component error in ${componentName}: ${error.message}`,
      stack: error.stack,
      context: {
        componentName,
        errorInfo
      }
    });
  };

  const captureAsyncError = async (asyncFn: () => Promise<any>, context?: string) => {
    try {
      return await asyncFn();
    } catch (error) {
      errorTracker.captureError({
        type: 'javascript',
        message: `Async error${context ? ` in ${context}` : ''}: ${error}`,
        stack: (error as Error).stack,
        context: { asyncContext: context }
      });
      throw error;
    }
  };

  return {
    captureError,
    captureComponentError,
    captureAsyncError,
    addBreadcrumb,
    setUser,
    setTag,
    setExtra
  };
};