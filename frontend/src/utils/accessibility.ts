// Accessibility Audit and WCAG 2.1 AA Compliance System

export interface AccessibilityIssue {
  id: string;
  type: 'error' | 'warning' | 'notice';
  wcagLevel: 'A' | 'AA' | 'AAA';
  principle: 'perceivable' | 'operable' | 'understandable' | 'robust';
  guideline: string;
  criterion: string;
  element?: Element;
  selector?: string;
  message: string;
  impact: 'minor' | 'moderate' | 'serious' | 'critical';
  help: string;
  helpUrl: string;
}

export interface AccessibilityReport {
  url: string;
  timestamp: number;
  score: number;
  totalElements: number;
  issues: AccessibilityIssue[];
  statistics: {
    errors: number;
    warnings: number;
    notices: number;
    byPrinciple: Record<string, number>;
    byImpact: Record<string, number>;
  };
}

export interface ColorContrastResult {
  foreground: string;
  background: string;
  ratio: number;
  aaCompliant: boolean;
  aaaCompliant: boolean;
}

class AccessibilityAuditor {
  private issues: AccessibilityIssue[] = [];
  private isAuditing = false;

  // Run comprehensive accessibility audit
  async audit(): Promise<AccessibilityReport> {
    if (this.isAuditing) {
      throw new Error('Audit already in progress');
    }

    this.isAuditing = true;
    this.issues = [];

    try {
      // Perform various accessibility checks
      await this.checkImages();
      await this.checkHeadings();
      await this.checkForms();
      await this.checkLinks();
      await this.checkButtons();
      await this.checkColorContrast();
      await this.checkKeyboardNavigation();
      await this.checkLandmarks();
      await this.checkFocus();
      await this.checkARIA();
      await this.checkLanguage();
      await this.checkStructure();

      return this.generateReport();
    } finally {
      this.isAuditing = false;
    }
  }

  // Check images for alt text and accessibility
  private async checkImages(): Promise<void> {
    const images = document.querySelectorAll('img');
    
    images.forEach((img, index) => {
      // Check for alt attribute
      if (!img.hasAttribute('alt')) {
        this.addIssue({
          type: 'error',
          wcagLevel: 'A',
          principle: 'perceivable',
          guideline: '1.1',
          criterion: '1.1.1',
          element: img,
          selector: this.getSelector(img),
          message: 'Image missing alt attribute',
          impact: 'serious',
          help: 'All images must have an alt attribute to describe the image content for screen readers',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html'
        });
      }

      // Check for empty alt on decorative images
      if (img.alt === '' && !img.hasAttribute('role')) {
        // This might be decorative, but check if it should have alt text
        const parentLink = img.closest('a');
        if (parentLink && !parentLink.textContent?.trim()) {
          this.addIssue({
            type: 'error',
            wcagLevel: 'A',
            principle: 'perceivable',
            guideline: '1.1',
            criterion: '1.1.1',
            element: img,
            selector: this.getSelector(img),
            message: 'Image in link without alt text',
            impact: 'serious',
            help: 'Images within links must have alt text describing the link destination',
            helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html'
          });
        }
      }

      // Check for very long alt text
      if (img.alt && img.alt.length > 125) {
        this.addIssue({
          type: 'warning',
          wcagLevel: 'A',
          principle: 'perceivable',
          guideline: '1.1',
          criterion: '1.1.1',
          element: img,
          selector: this.getSelector(img),
          message: 'Alt text is very long (>125 characters)',
          impact: 'minor',
          help: 'Alt text should be concise and describe the essential information',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html'
        });
      }
    });
  }

  // Check heading structure
  private async checkHeadings(): Promise<void> {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let previousLevel = 0;
    let hasH1 = false;

    headings.forEach((heading) => {
      const level = parseInt(heading.tagName.charAt(1));
      
      if (level === 1) {
        if (hasH1) {
          this.addIssue({
            type: 'error',
            wcagLevel: 'AA',
            principle: 'perceivable',
            guideline: '1.3',
            criterion: '1.3.1',
            element: heading,
            selector: this.getSelector(heading),
            message: 'Multiple H1 headings found',
            impact: 'moderate',
            help: 'Use only one H1 heading per page for proper document structure',
            helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
          });
        }
        hasH1 = true;
      }

      // Check for heading level skipping
      if (previousLevel > 0 && level > previousLevel + 1) {
        this.addIssue({
          type: 'error',
          wcagLevel: 'AA',
          principle: 'perceivable',
          guideline: '1.3',
          criterion: '1.3.1',
          element: heading,
          selector: this.getSelector(heading),
          message: `Heading level skipped from h${previousLevel} to h${level}`,
          impact: 'moderate',
          help: 'Heading levels should not skip levels in the hierarchy',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
        });
      }

      // Check for empty headings
      if (!heading.textContent?.trim()) {
        this.addIssue({
          type: 'error',
          wcagLevel: 'A',
          principle: 'perceivable',
          guideline: '1.3',
          criterion: '1.3.1',
          element: heading,
          selector: this.getSelector(heading),
          message: 'Empty heading found',
          impact: 'serious',
          help: 'Headings must contain text content',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
        });
      }

      previousLevel = level;
    });

    // Check if page has any headings
    if (headings.length === 0) {
      this.addIssue({
        type: 'error',
        wcagLevel: 'AA',
        principle: 'perceivable',
        guideline: '1.3',
        criterion: '1.3.1',
        element: document.body,
        selector: 'body',
        message: 'Page has no headings',
        impact: 'serious',
        help: 'Pages should have headings to provide structure and navigation aids',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
      });
    }
  }

  // Check form accessibility
  private async checkForms(): Promise<void> {
    const inputs = document.querySelectorAll('input, textarea, select');
    
    inputs.forEach((input) => {
      // Check for labels
      const hasLabel = this.hasAssociatedLabel(input);
      if (!hasLabel && input.getAttribute('type') !== 'hidden') {
        this.addIssue({
          type: 'error',
          wcagLevel: 'A',
          principle: 'perceivable',
          guideline: '1.3',
          criterion: '1.3.1',
          element: input,
          selector: this.getSelector(input),
          message: 'Form input missing label',
          impact: 'serious',
          help: 'All form inputs must have associated labels',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
        });
      }

      // Check for required field indicators
      if (input.hasAttribute('required') && !input.hasAttribute('aria-required')) {
        this.addIssue({
          type: 'warning',
          wcagLevel: 'AA',
          principle: 'understandable',
          guideline: '3.3',
          criterion: '3.3.2',
          element: input,
          selector: this.getSelector(input),
          message: 'Required field not clearly indicated',
          impact: 'moderate',
          help: 'Required fields should be clearly marked with aria-required or visual indicators',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html'
        });
      }
    });

    // Check fieldsets and legends
    const fieldsets = document.querySelectorAll('fieldset');
    fieldsets.forEach((fieldset) => {
      const legend = fieldset.querySelector('legend');
      if (!legend) {
        this.addIssue({
          type: 'error',
          wcagLevel: 'A',
          principle: 'perceivable',
          guideline: '1.3',
          criterion: '1.3.1',
          element: fieldset,
          selector: this.getSelector(fieldset),
          message: 'Fieldset missing legend',
          impact: 'moderate',
          help: 'Fieldsets must have a legend to describe the group of form controls',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
        });
      }
    });
  }

  // Check link accessibility
  private async checkLinks(): Promise<void> {
    const links = document.querySelectorAll('a[href]');
    
    links.forEach((link) => {
      const text = this.getAccessibleText(link);
      
      // Check for empty links
      if (!text.trim()) {
        this.addIssue({
          type: 'error',
          wcagLevel: 'A',
          principle: 'operable',
          guideline: '2.4',
          criterion: '2.4.4',
          element: link,
          selector: this.getSelector(link),
          message: 'Link has no accessible text',
          impact: 'serious',
          help: 'Links must have accessible text that describes the link purpose',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html'
        });
      }

      // Check for non-descriptive link text
      const nonDescriptiveTexts = ['click here', 'read more', 'more', 'here', 'link'];
      if (nonDescriptiveTexts.some(t => text.toLowerCase().includes(t))) {
        this.addIssue({
          type: 'warning',
          wcagLevel: 'AA',
          principle: 'operable',
          guideline: '2.4',
          criterion: '2.4.4',
          element: link,
          selector: this.getSelector(link),
          message: 'Link text is not descriptive',
          impact: 'moderate',
          help: 'Link text should describe the destination or purpose of the link',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html'
        });
      }

      // Check for target="_blank" without warning
      if (link.getAttribute('target') === '_blank' && !link.hasAttribute('aria-label')) {
        this.addIssue({
          type: 'warning',
          wcagLevel: 'AAA',
          principle: 'understandable',
          guideline: '3.2',
          criterion: '3.2.5',
          element: link,
          selector: this.getSelector(link),
          message: 'Link opens in new window without warning',
          impact: 'minor',
          help: 'Links that open in new windows should inform users',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/change-on-request.html'
        });
      }
    });
  }

  // Check button accessibility
  private async checkButtons(): Promise<void> {
    const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"], input[type="reset"]');
    
    buttons.forEach((button) => {
      const text = this.getAccessibleText(button);
      
      // Check for empty buttons
      if (!text.trim()) {
        this.addIssue({
          type: 'error',
          wcagLevel: 'A',
          principle: 'perceivable',
          guideline: '1.1',
          criterion: '1.1.1',
          element: button,
          selector: this.getSelector(button),
          message: 'Button has no accessible text',
          impact: 'serious',
          help: 'Buttons must have text or accessible labels',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html'
        });
      }
    });
  }

  // Check color contrast
  private async checkColorContrast(): Promise<void> {
    const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, a, button, label, td, th, li');
    
    for (const element of textElements) {
      if (element.textContent?.trim()) {
        const contrast = this.getColorContrast(element);
        
        if (contrast.ratio < 4.5) {
          this.addIssue({
            type: 'error',
            wcagLevel: 'AA',
            principle: 'perceivable',
            guideline: '1.4',
            criterion: '1.4.3',
            element: element,
            selector: this.getSelector(element),
            message: `Low color contrast ratio: ${contrast.ratio.toFixed(2)}:1`,
            impact: 'serious',
            help: 'Text must have a contrast ratio of at least 4.5:1 for WCAG AA compliance',
            helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html'
          });
        }
      }
    }
  }

  // Check keyboard navigation
  private async checkKeyboardNavigation(): Promise<void> {
    const focusableElements = document.querySelectorAll(
      'a[href], button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])'
    );
    
    focusableElements.forEach((element) => {
      // Check for missing focus indicators
      const styles = window.getComputedStyle(element);
      const hasFocusStyle = styles.outline !== 'none' || styles.boxShadow !== 'none';
      
      if (!hasFocusStyle) {
        this.addIssue({
          type: 'warning',
          wcagLevel: 'AA',
          principle: 'operable',
          guideline: '2.4',
          criterion: '2.4.7',
          element: element,
          selector: this.getSelector(element),
          message: 'Element may not have visible focus indicator',
          impact: 'moderate',
          help: 'All interactive elements should have visible focus indicators',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html'
        });
      }

      // Check for positive tabindex
      const tabindex = element.getAttribute('tabindex');
      if (tabindex && parseInt(tabindex) > 0) {
        this.addIssue({
          type: 'warning',
          wcagLevel: 'A',
          principle: 'operable',
          guideline: '2.4',
          criterion: '2.4.3',
          element: element,
          selector: this.getSelector(element),
          message: 'Positive tabindex found',
          impact: 'moderate',
          help: 'Avoid positive tabindex values as they can disrupt natural tab order',
          helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html'
        });
      }
    });
  }

  // Check ARIA usage
  private async checkARIA(): Promise<void> {
    const elementsWithARIA = document.querySelectorAll('[aria-labelledby], [aria-describedby], [role]');
    
    elementsWithARIA.forEach((element) => {
      // Check aria-labelledby references
      const labelledBy = element.getAttribute('aria-labelledby');
      if (labelledBy) {
        const ids = labelledBy.split(' ');
        ids.forEach(id => {
          if (!document.getElementById(id)) {
            this.addIssue({
              type: 'error',
              wcagLevel: 'A',
              principle: 'robust',
              guideline: '4.1',
              criterion: '4.1.2',
              element: element,
              selector: this.getSelector(element),
              message: `aria-labelledby references non-existent element: ${id}`,
              impact: 'serious',
              help: 'aria-labelledby must reference existing element IDs',
              helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html'
            });
          }
        });
      }

      // Check aria-describedby references
      const describedBy = element.getAttribute('aria-describedby');
      if (describedBy) {
        const ids = describedBy.split(' ');
        ids.forEach(id => {
          if (!document.getElementById(id)) {
            this.addIssue({
              type: 'error',
              wcagLevel: 'A',
              principle: 'robust',
              guideline: '4.1',
              criterion: '4.1.2',
              element: element,
              selector: this.getSelector(element),
              message: `aria-describedby references non-existent element: ${id}`,
              impact: 'serious',
              help: 'aria-describedby must reference existing element IDs',
              helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html'
            });
          }
        });
      }
    });
  }

  // Check page language
  private async checkLanguage(): Promise<void> {
    const html = document.documentElement;
    if (!html.hasAttribute('lang')) {
      this.addIssue({
        type: 'error',
        wcagLevel: 'A',
        principle: 'understandable',
        guideline: '3.1',
        criterion: '3.1.1',
        element: html,
        selector: 'html',
        message: 'Page language not specified',
        impact: 'serious',
        help: 'The lang attribute must be specified on the html element',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html'
      });
    }
  }

  // Check landmarks
  private async checkLandmarks(): Promise<void> {
    const main = document.querySelector('main, [role="main"]');
    if (!main) {
      this.addIssue({
        type: 'warning',
        wcagLevel: 'AA',
        principle: 'perceivable',
        guideline: '1.3',
        criterion: '1.3.1',
        element: document.body,
        selector: 'body',
        message: 'Page missing main landmark',
        impact: 'moderate',
        help: 'Pages should have a main landmark to identify the primary content',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
      });
    }

    const nav = document.querySelector('nav, [role="navigation"]');
    if (!nav) {
      this.addIssue({
        type: 'notice',
        wcagLevel: 'AA',
        principle: 'perceivable',
        guideline: '1.3',
        criterion: '1.3.1',
        element: document.body,
        selector: 'body',
        message: 'Page missing navigation landmark',
        impact: 'minor',
        help: 'Consider adding navigation landmarks for better structure',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
      });
    }
  }

  // Check document structure
  private async checkStructure(): Promise<void> {
    // Check for skip links
    const skipLink = document.querySelector('a[href^="#"]:first-child');
    if (!skipLink || !skipLink.textContent?.toLowerCase().includes('skip')) {
      this.addIssue({
        type: 'warning',
        wcagLevel: 'A',
        principle: 'operable',
        guideline: '2.4',
        criterion: '2.4.1',
        element: document.body,
        selector: 'body',
        message: 'Page missing skip link',
        impact: 'moderate',
        help: 'Provide a skip link as the first focusable element',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html'
      });
    }
  }

  // Check focus management
  private async checkFocus(): Promise<void> {
    // This would typically involve testing focus trap, focus restoration, etc.
    // Implementation would depend on specific framework and components
  }

  // Helper methods
  private hasAssociatedLabel(element: Element): boolean {
    // Check for explicit label
    const id = element.id;
    if (id && document.querySelector(`label[for="${id}"]`)) {
      return true;
    }

    // Check for implicit label (label wrapping the input)
    if (element.closest('label')) {
      return true;
    }

    // Check for aria-label or aria-labelledby
    if (element.hasAttribute('aria-label') || element.hasAttribute('aria-labelledby')) {
      return true;
    }

    return false;
  }

  private getAccessibleText(element: Element): string {
    // Priority order: aria-label > aria-labelledby > text content > alt > title
    
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel;

    const ariaLabelledBy = element.getAttribute('aria-labelledby');
    if (ariaLabelledBy) {
      const referencedElement = document.getElementById(ariaLabelledBy);
      if (referencedElement) return referencedElement.textContent || '';
    }

    const textContent = element.textContent?.trim();
    if (textContent) return textContent;

    const alt = element.getAttribute('alt');
    if (alt) return alt;

    const title = element.getAttribute('title');
    if (title) return title;

    return '';
  }

  private getColorContrast(element: Element): ColorContrastResult {
    const styles = window.getComputedStyle(element);
    const foreground = this.parseColor(styles.color);
    const background = this.parseColor(styles.backgroundColor);

    const ratio = this.calculateContrastRatio(foreground, background);

    return {
      foreground: styles.color,
      background: styles.backgroundColor,
      ratio,
      aaCompliant: ratio >= 4.5,
      aaaCompliant: ratio >= 7
    };
  }

  private parseColor(color: string): [number, number, number] {
    // Simple RGB parsing - in production, use a proper color parsing library
    const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (match) {
      return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
    }
    return [0, 0, 0]; // Default to black
  }

  private calculateContrastRatio(color1: [number, number, number], color2: [number, number, number]): number {
    const l1 = this.getLuminance(color1);
    const l2 = this.getLuminance(color2);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
  }

  private getLuminance([r, g, b]: [number, number, number]): number {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  }

  private getSelector(element: Element): string {
    if (element.id) return `#${element.id}`;
    if (element.className) return `${element.tagName.toLowerCase()}.${element.className.split(' ')[0]}`;
    return element.tagName.toLowerCase();
  }

  private addIssue(issue: Omit<AccessibilityIssue, 'id'>): void {
    this.issues.push({
      ...issue,
      id: Date.now().toString(36) + Math.random().toString(36).substr(2)
    });
  }

  private generateReport(): AccessibilityReport {
    const statistics = {
      errors: this.issues.filter(i => i.type === 'error').length,
      warnings: this.issues.filter(i => i.type === 'warning').length,
      notices: this.issues.filter(i => i.type === 'notice').length,
      byPrinciple: {} as Record<string, number>,
      byImpact: {} as Record<string, number>
    };

    this.issues.forEach(issue => {
      statistics.byPrinciple[issue.principle] = (statistics.byPrinciple[issue.principle] || 0) + 1;
      statistics.byImpact[issue.impact] = (statistics.byImpact[issue.impact] || 0) + 1;
    });

    const score = Math.max(0, 100 - (statistics.errors * 10 + statistics.warnings * 5 + statistics.notices * 1));

    return {
      url: window.location.href,
      timestamp: Date.now(),
      score,
      totalElements: document.querySelectorAll('*').length,
      issues: this.issues,
      statistics
    };
  }
}

// Create singleton instance
export const accessibilityAuditor = new AccessibilityAuditor();

// Convenience functions
export const runAccessibilityAudit = (): Promise<AccessibilityReport> => {
  return accessibilityAuditor.audit();
};

// React hook for accessibility
export const useAccessibility = () => {
  const announceToScreenReader = (message: string) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      try {
        if (document.body.contains(announcement)) {
          announcement.remove();
        }
      } catch (error) {
        console.debug('Announcement cleanup error:', error);
      }
    }, 1000);
  };

  const manageFocus = (element: HTMLElement | null) => {
    if (element) {
      element.focus();
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const trapFocus = (container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'a[href], button, input, textarea, select, details, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  };

  return {
    announceToScreenReader,
    manageFocus,
    trapFocus,
    runAudit: runAccessibilityAudit
  };
};