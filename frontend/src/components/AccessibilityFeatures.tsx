// Accessibility Features Component

import { useState, useEffect, useRef } from 'react';
import { useAccessibility } from '../utils/accessibility';

// Skip Link Component
export const SkipLink = ({ targetId = 'main-content', text = 'Skip to main content' }) => {
  return (
    <a
      href={`#${targetId}`}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 
                 bg-blue-600 text-white px-4 py-2 rounded-md z-50 
                 focus:outline-none focus:ring-2 focus:ring-blue-300"
      onClick={(e) => {
        e.preventDefault();
        const target = document.getElementById(targetId);
        if (target) {
          target.focus();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }}
    >
      {text}
    </a>
  );
};

// Screen Reader Only Text
export const ScreenReaderOnly = ({ children }: { children: React.ReactNode }) => {
  return (
    <span className="sr-only">
      {children}
    </span>
  );
};

// Live Region for Announcements
export const LiveRegion = ({ 
  children, 
  politeness = 'polite' as 'polite' | 'assertive',
  atomic = true 
}: {
  children: React.ReactNode;
  politeness?: 'polite' | 'assertive';
  atomic?: boolean;
}) => {
  return (
    <div
      aria-live={politeness}
      aria-atomic={atomic}
      className="sr-only"
    >
      {children}
    </div>
  );
};

// Focus Trap Component
export const FocusTrap = ({ 
  children, 
  isActive = true,
  restoreFocus = true
}: {
  children: React.ReactNode;
  isActive?: boolean;
  restoreFocus?: boolean;
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const { trapFocus } = useAccessibility();

  useEffect(() => {
    if (isActive && containerRef.current) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      const cleanup = trapFocus(containerRef.current);
      
      return () => {
        cleanup();
        if (restoreFocus && previousFocusRef.current) {
          previousFocusRef.current.focus();
        }
      };
    }
  }, [isActive, restoreFocus, trapFocus]);

  return (
    <div ref={containerRef}>
      {children}
    </div>
  );
};

// Accessible Button Component
export const AccessibleButton = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  ariaLabel,
  ariaDescribedBy,
  className = '',
  ...props
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  className?: string;
  [key: string]: any;
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-300',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500 disabled:bg-gray-100',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-red-300'
  };

  const sizeClasses = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg'
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// Accessible Modal Component
export const AccessibleModal = ({
  isOpen,
  onClose,
  title,
  children,
  className = ''
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  className?: string;
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const titleId = `modal-title-${Date.now()}`;

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      modalRef.current?.focus();
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby={titleId}
      aria-modal="true"
      role="dialog"
    >
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          aria-hidden="true"
          onClick={onClose}
        />

        <FocusTrap isActive={isOpen}>
          <div
            ref={modalRef}
            tabIndex={-1}
            className={`inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left 
                       overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle 
                       sm:max-w-lg sm:w-full sm:p-6 ${className}`}
          >
            <div className="flex items-start justify-between">
              <h2 id={titleId} className="text-lg font-medium text-gray-900">
                {title}
              </h2>
              <button
                type="button"
                onClick={onClose}
                className="ml-3 inline-flex items-center justify-center h-8 w-8 rounded-md 
                          text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 
                          focus:ring-offset-2 focus:ring-blue-500"
                aria-label="Close modal"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="mt-4">
              {children}
            </div>
          </div>
        </FocusTrap>
      </div>
    </div>
  );
};

// Accessible Form Field Component
export const AccessibleFormField = ({
  label,
  children,
  error,
  help,
  required = false,
  className = ''
}: {
  label: string;
  children: React.ReactElement;
  error?: string;
  help?: string;
  required?: boolean;
  className?: string;
}) => {
  const fieldId = children.props.id || `field-${Date.now()}`;
  const errorId = error ? `${fieldId}-error` : undefined;
  const helpId = help ? `${fieldId}-help` : undefined;
  const describedBy = [errorId, helpId].filter(Boolean).join(' ');

  return (
    <div className={`space-y-1 ${className}`}>
      <label 
        htmlFor={fieldId}
        className="block text-sm font-medium text-gray-700"
      >
        {label}
        {required && (
          <span className="text-red-500 ml-1" aria-label="required">
            *
          </span>
        )}
      </label>
      
      {React.cloneElement(children, {
        id: fieldId,
        'aria-describedby': describedBy || undefined,
        'aria-invalid': error ? 'true' : undefined,
        'aria-required': required ? 'true' : undefined
      })}
      
      {help && (
        <p id={helpId} className="text-sm text-gray-500">
          {help}
        </p>
      )}
      
      {error && (
        <p id={errorId} className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

// Accessible Tabs Component
export const AccessibleTabs = ({
  tabs,
  activeTab,
  onTabChange,
  className = ''
}: {
  tabs: Array<{ id: string; label: string; content: React.ReactNode }>;
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}) => {
  const tabListRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent, tabId: string, index: number) => {
    let nextIndex = index;

    switch (e.key) {
      case 'ArrowLeft':
        e.preventDefault();
        nextIndex = index > 0 ? index - 1 : tabs.length - 1;
        break;
      case 'ArrowRight':
        e.preventDefault();
        nextIndex = index < tabs.length - 1 ? index + 1 : 0;
        break;
      case 'Home':
        e.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        nextIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    const nextTab = tabs[nextIndex];
    onTabChange(nextTab.id);
    
    // Focus the next tab
    setTimeout(() => {
      const nextButton = tabListRef.current?.querySelector(`[aria-controls="panel-${nextTab.id}"]`) as HTMLButtonElement;
      nextButton?.focus();
    }, 0);
  };

  return (
    <div className={className}>
      <div
        ref={tabListRef}
        role="tablist"
        className="flex border-b border-gray-200"
      >
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            id={`tab-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onClick={() => onTabChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, tab.id, index)}
            className={`px-4 py-2 font-medium text-sm focus:outline-none focus:ring-2 
                       focus:ring-offset-2 focus:ring-blue-500 ${
              activeTab === tab.id
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab) => (
        <div
          key={tab.id}
          id={`panel-${tab.id}`}
          role="tabpanel"
          aria-labelledby={`tab-${tab.id}`}
          hidden={activeTab !== tab.id}
          className="mt-4"
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
};

// Progress Indicator Component
export const AccessibleProgressBar = ({
  value,
  max = 100,
  label,
  showValue = true,
  className = ''
}: {
  value: number;
  max?: number;
  label: string;
  showValue?: boolean;
  className?: string;
}) => {
  const percentage = Math.round((value / max) * 100);

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex justify-between text-sm font-medium text-gray-700">
        <span>{label}</span>
        {showValue && <span>{percentage}%</span>}
      </div>
      <div
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label}
        className="w-full bg-gray-200 rounded-full h-2"
      >
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

// Tooltip Component
export const AccessibleTooltip = ({
  children,
  content,
  position = 'top'
}: {
  children: React.ReactElement;
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipId = `tooltip-${Date.now()}`;

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
  };

  return (
    <div className="relative inline-block">
      {React.cloneElement(children, {
        'aria-describedby': tooltipId,
        onMouseEnter: () => setIsVisible(true),
        onMouseLeave: () => setIsVisible(false),
        onFocus: () => setIsVisible(true),
        onBlur: () => setIsVisible(false)
      })}
      
      {isVisible && (
        <div
          id={tooltipId}
          role="tooltip"
          className={`absolute z-10 px-2 py-1 text-sm text-white bg-gray-900 rounded 
                     whitespace-nowrap ${positionClasses[position]}`}
        >
          {content}
        </div>
      )}
    </div>
  );
};