// Comprehensive SEO Utility for React SPA
import { generateCompleteSitemap, generateRobotsTxt } from './sitemapGenerator'
import { getOptimizedImageUrl } from './cdn'

// SEO Configuration
interface SEOConfig {
  siteName: string
  siteUrl: string
  defaultTitle: string
  defaultDescription: string
  defaultImage: string
  defaultKeywords: string[]
  twitterHandle: string
  facebookAppId: string
  organizationName: string
  organizationLogo: string
  language: string
  region: string
  enableJsonLd: boolean
  enableOpenGraph: boolean
  enableTwitterCards: boolean
  enableCanonicalUrls: boolean
  enableAlternateUrls: boolean
}

// Meta tags interface
interface MetaTags {
  title?: string
  description?: string
  keywords?: string[]
  image?: string
  url?: string
  type?: 'website' | 'article' | 'product' | 'profile'
  siteName?: string
  locale?: string
  author?: string
  publishedTime?: string
  modifiedTime?: string
  section?: string
  tags?: string[]
  noIndex?: boolean
  noFollow?: boolean
  canonical?: string
  alternates?: Array<{ href: string; hreflang: string }>
  robots?: string
  googleSiteVerification?: string
  bingSiteVerification?: string
  yandexVerification?: string
}

// Product-specific SEO data
interface ProductSEO {
  name: string
  description: string
  price: number
  currency: string
  availability: 'in_stock' | 'out_of_stock' | 'pre_order'
  sku?: string
  brand?: string
  category?: string
  images?: string[]
  rating?: {
    value: number
    count: number
  }
  reviews?: Array<{
    author: string
    rating: number
    content: string
    date: string
  }>
  variants?: Array<{
    name: string
    price: number
    sku?: string
    availability: string
  }>
}

// Article-specific SEO data
interface ArticleSEO {
  headline: string
  description: string
  author: string
  publishedTime: string
  modifiedTime?: string
  section?: string
  tags?: string[]
  image?: string
  wordCount?: number
  readingTime?: number
}

class SEOManager {
  private config: SEOConfig

  constructor(config: Partial<SEOConfig> = {}) {
    this.config = {
      siteName: 'Pasargad Prints',
      siteUrl: import.meta.env.VITE_SITE_URL || 'https://pasargadprints.com',
      defaultTitle: 'Pasargad Prints - Premium 3D Printing Store',
      defaultDescription: 'Discover high-quality 3D printing products, materials, and services at Pasargad Prints. Shop printers, filaments, resins, and accessories from top brands.',
      defaultImage: '/og-image.jpg',
      defaultKeywords: ['3D printing', '3D printers', 'filament', 'resin', 'PLA', 'ABS', 'PETG', '3D printing services'],
      twitterHandle: '@pasargadprints',
      facebookAppId: '',
      organizationName: 'Pasargad Prints',
      organizationLogo: '/logo.png',
      language: 'en',
      region: 'US',
      enableJsonLd: true,
      enableOpenGraph: true,
      enableTwitterCards: true,
      enableCanonicalUrls: true,
      enableAlternateUrls: true,
      ...config
    }
  }

  // Generate comprehensive meta tags
  generateMetaTags(options: MetaTags = {}): Record<string, string> {
    const meta: Record<string, string> = {}
    
    // Basic meta tags
    const title = options.title || this.config.defaultTitle
    const description = options.description || this.config.defaultDescription
    const image = options.image ? this.getAbsoluteUrl(options.image) : this.getAbsoluteUrl(this.config.defaultImage)
    const url = options.url ? this.getAbsoluteUrl(options.url) : this.config.siteUrl
    const siteName = options.siteName || this.config.siteName

    // Title
    meta['title'] = title

    // Description
    meta['description'] = description

    // Keywords
    if (options.keywords || this.config.defaultKeywords) {
      meta['keywords'] = (options.keywords || this.config.defaultKeywords).join(', ')
    }

    // Robots
    const robotsDirectives = []
    if (options.noIndex) robotsDirectives.push('noindex')
    else robotsDirectives.push('index')
    
    if (options.noFollow) robotsDirectives.push('nofollow')
    else robotsDirectives.push('follow')
    
    robotsDirectives.push('noarchive', 'noimageindex')
    
    meta['robots'] = options.robots || robotsDirectives.join(', ')

    // Canonical URL
    if (this.config.enableCanonicalUrls) {
      meta['canonical'] = options.canonical || url
    }

    // Language and region
    meta['language'] = this.config.language
    meta['geo.region'] = this.config.region

    // Author
    if (options.author) {
      meta['author'] = options.author
    }

    // OpenGraph tags
    if (this.config.enableOpenGraph) {
      meta['og:title'] = title
      meta['og:description'] = description
      meta['og:image'] = getOptimizedImageUrl(image, { width: 1200, height: 630, format: 'webp' })
      meta['og:image:width'] = '1200'
      meta['og:image:height'] = '630'
      meta['og:image:type'] = 'image/webp'
      meta['og:url'] = url
      meta['og:type'] = options.type || 'website'
      meta['og:site_name'] = siteName
      meta['og:locale'] = options.locale || `${this.config.language}_${this.config.region}`

      // Article-specific OpenGraph
      if (options.type === 'article') {
        if (options.author) meta['article:author'] = options.author
        if (options.publishedTime) meta['article:published_time'] = options.publishedTime
        if (options.modifiedTime) meta['article:modified_time'] = options.modifiedTime
        if (options.section) meta['article:section'] = options.section
        if (options.tags) {
          options.tags.forEach((tag, index) => {
            meta[`article:tag:${index}`] = tag
          })
        }
      }

      // Product-specific OpenGraph
      if (options.type === 'product') {
        // These would be handled by structured data instead
      }
    }

    // Twitter Card tags
    if (this.config.enableTwitterCards) {
      meta['twitter:card'] = 'summary_large_image'
      meta['twitter:title'] = title
      meta['twitter:description'] = description
      meta['twitter:image'] = getOptimizedImageUrl(image, { width: 1200, height: 630, format: 'webp' })
      meta['twitter:site'] = this.config.twitterHandle
      if (options.author) meta['twitter:creator'] = this.config.twitterHandle
    }

    // Facebook App ID
    if (this.config.facebookAppId) {
      meta['fb:app_id'] = this.config.facebookAppId
    }

    // Site verification
    if (options.googleSiteVerification) {
      meta['google-site-verification'] = options.googleSiteVerification
    }
    if (options.bingSiteVerification) {
      meta['msvalidate.01'] = options.bingSiteVerification
    }
    if (options.yandexVerification) {
      meta['yandex-verification'] = options.yandexVerification
    }

    return meta
  }

  // Generate JSON-LD structured data for products
  generateProductStructuredData(product: ProductSEO, url?: string): object {
    const currentUrl = url || window.location.href

    const structuredData: any = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: product.name,
      description: product.description,
      image: product.images?.map(img => getOptimizedImageUrl(img, { width: 800, height: 600 })) || [],
      url: currentUrl,
      sku: product.sku,
      brand: {
        '@type': 'Brand',
        name: product.brand || this.config.organizationName
      },
      offers: {
        '@type': 'Offer',
        price: product.price.toString(),
        priceCurrency: product.currency,
        availability: this.getSchemaAvailability(product.availability),
        url: currentUrl,
        seller: {
          '@type': 'Organization',
          name: this.config.organizationName,
          url: this.config.siteUrl
        }
      }
    }

    // Add category if available
    if (product.category) {
      structuredData.category = product.category
    }

    // Add aggregate rating if available
    if (product.rating) {
      structuredData.aggregateRating = {
        '@type': 'AggregateRating',
        ratingValue: product.rating.value,
        reviewCount: product.rating.count,
        bestRating: 5,
        worstRating: 1
      }
    }

    // Add reviews if available
    if (product.reviews && product.reviews.length > 0) {
      structuredData.review = product.reviews.map(review => ({
        '@type': 'Review',
        author: {
          '@type': 'Person',
          name: review.author
        },
        reviewRating: {
          '@type': 'Rating',
          ratingValue: review.rating,
          bestRating: 5,
          worstRating: 1
        },
        reviewBody: review.content,
        datePublished: review.date
      }))
    }

    // Add variants if available
    if (product.variants && product.variants.length > 0) {
      structuredData.hasVariant = product.variants.map(variant => ({
        '@type': 'ProductModel',
        name: variant.name,
        sku: variant.sku,
        offers: {
          '@type': 'Offer',
          price: variant.price.toString(),
          priceCurrency: product.currency,
          availability: this.getSchemaAvailability(variant.availability)
        }
      }))
    }

    return structuredData
  }

  // Generate JSON-LD structured data for articles
  generateArticleStructuredData(article: ArticleSEO, url?: string): object {
    const currentUrl = url || window.location.href
    const image = article.image ? getOptimizedImageUrl(article.image, { width: 1200, height: 630 }) : this.getAbsoluteUrl(this.config.defaultImage)

    return {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: article.headline,
      description: article.description,
      image: [image],
      url: currentUrl,
      datePublished: article.publishedTime,
      dateModified: article.modifiedTime || article.publishedTime,
      author: {
        '@type': 'Person',
        name: article.author
      },
      publisher: {
        '@type': 'Organization',
        name: this.config.organizationName,
        logo: {
          '@type': 'ImageObject',
          url: this.getAbsoluteUrl(this.config.organizationLogo)
        }
      },
      mainEntityOfPage: {
        '@type': 'WebPage',
        '@id': currentUrl
      },
      ...(article.section && { articleSection: article.section }),
      ...(article.tags && { keywords: article.tags.join(', ') }),
      ...(article.wordCount && { wordCount: article.wordCount }),
      ...(article.readingTime && { timeRequired: `PT${article.readingTime}M` })
    }
  }

  // Generate organization structured data
  generateOrganizationStructuredData(): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: this.config.organizationName,
      url: this.config.siteUrl,
      logo: this.getAbsoluteUrl(this.config.organizationLogo),
      description: this.config.defaultDescription,
      address: {
        '@type': 'PostalAddress',
        streetAddress: '123 Main Street',
        addressLocality: 'San Francisco',
        addressRegion: 'CA',
        postalCode: '94105',
        addressCountry: 'US'
      },
      contactPoint: [{
        '@type': 'ContactPoint',
        telephone: '+1-XXX-XXX-XXXX',
        contactType: 'customer service',
        availableLanguage: ['English']
      }],
      sameAs: [
        'https://www.facebook.com/pasargadprints',
        'https://www.twitter.com/pasargadprints',
        'https://www.instagram.com/pasargadprints',
        'https://www.linkedin.com/company/pasargadprints'
      ]
    }
  }

  // Generate website structured data
  generateWebsiteStructuredData(): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      name: this.config.siteName,
      url: this.config.siteUrl,
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: `${this.config.siteUrl}/products?search={search_term_string}`
        },
        'query-input': 'required name=search_term_string'
      }
    }
  }

  // Generate breadcrumb structured data
  generateBreadcrumbStructuredData(breadcrumbs: Array<{ name: string; url: string }>): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: breadcrumbs.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: item.name,
        item: this.getAbsoluteUrl(item.url)
      }))
    }
  }

  // Generate FAQ structured data
  generateFAQStructuredData(faqs: Array<{ question: string; answer: string }>): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faqs.map(faq => ({
        '@type': 'Question',
        name: faq.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: faq.answer
        }
      }))
    }
  }

  // SEO analysis and recommendations
  analyzeSEO(content: {
    title?: string
    description?: string
    content?: string
    keywords?: string[]
    images?: string[]
    headings?: Array<{ level: number; text: string }>
    links?: Array<{ href: string; text: string; external: boolean }>
  }) {
    const analysis = {
      score: 0,
      recommendations: [] as string[],
      warnings: [] as string[],
      errors: [] as string[]
    }

    let score = 0

    // Title analysis
    if (content.title) {
      if (content.title.length >= 30 && content.title.length <= 60) {
        score += 10
      } else if (content.title.length < 30) {
        analysis.recommendations.push('Title is too short. Aim for 30-60 characters.')
      } else {
        analysis.warnings.push('Title might be too long and get truncated in search results.')
      }
    } else {
      analysis.errors.push('Missing page title.')
    }

    // Description analysis
    if (content.description) {
      if (content.description.length >= 120 && content.description.length <= 160) {
        score += 10
      } else if (content.description.length < 120) {
        analysis.recommendations.push('Description is too short. Aim for 120-160 characters.')
      } else {
        analysis.warnings.push('Description might be too long and get truncated.')
      }
    } else {
      analysis.errors.push('Missing meta description.')
    }

    // Content length analysis
    if (content.content) {
      const wordCount = content.content.split(/\s+/).length
      if (wordCount >= 300) {
        score += 10
      } else {
        analysis.recommendations.push('Content is quite short. Consider adding more relevant information.')
      }
    }

    // Headings structure analysis
    if (content.headings) {
      const h1Count = content.headings.filter(h => h.level === 1).length
      if (h1Count === 1) {
        score += 10
      } else if (h1Count === 0) {
        analysis.errors.push('Missing H1 heading.')
      } else {
        analysis.warnings.push('Multiple H1 headings found. Use only one H1 per page.')
      }

      const hasH2 = content.headings.some(h => h.level === 2)
      if (hasH2) {
        score += 5
      } else {
        analysis.recommendations.push('Consider adding H2 headings to structure your content.')
      }
    }

    // Image optimization analysis
    if (content.images) {
      if (content.images.length > 0) {
        score += 5
        // Check for optimized images (this would require actual image analysis)
        analysis.recommendations.push('Ensure all images have alt text and are properly optimized.')
      }
    }

    // Keywords analysis
    if (content.keywords && content.keywords.length > 0) {
      score += 5
      if (content.content && content.keywords.length > 0) {
        const contentLower = content.content.toLowerCase()
        const keywordDensity = content.keywords.map(keyword => {
          const keywordLower = keyword.toLowerCase()
          const matches = (contentLower.match(new RegExp(keywordLower, 'g')) || []).length
          const words = content.content!.split(/\s+/).length
          return (matches / words) * 100
        })

        const avgDensity = keywordDensity.reduce((a, b) => a + b, 0) / keywordDensity.length
        if (avgDensity >= 1 && avgDensity <= 3) {
          score += 5
        } else if (avgDensity > 3) {
          analysis.warnings.push('Keyword density might be too high (over 3%).')
        } else {
          analysis.recommendations.push('Consider using your target keywords more naturally in the content.')
        }
      }
    }

    // Internal/external links analysis
    if (content.links) {
      const internalLinks = content.links.filter(link => !link.external).length
      const externalLinks = content.links.filter(link => link.external).length

      if (internalLinks > 0) {
        score += 5
      } else {
        analysis.recommendations.push('Add internal links to improve site navigation and SEO.')
      }

      if (externalLinks > 0) {
        score += 2
        analysis.recommendations.push('Ensure external links open in new tabs and have appropriate rel attributes.')
      }
    }

    analysis.score = Math.min(score, 100)
    return analysis
  }

  // Helper methods
  private getAbsoluteUrl(url: string): string {
    if (url.startsWith('http')) {
      return url
    }
    return `${this.config.siteUrl}${url.startsWith('/') ? '' : '/'}${url}`
  }

  private getSchemaAvailability(availability: string): string {
    switch (availability) {
      case 'in_stock':
        return 'https://schema.org/InStock'
      case 'out_of_stock':
        return 'https://schema.org/OutOfStock'
      case 'pre_order':
        return 'https://schema.org/PreOrder'
      default:
        return 'https://schema.org/OutOfStock'
    }
  }

  // Get configuration
  getConfig(): SEOConfig {
    return { ...this.config }
  }

  // Update configuration
  updateConfig(updates: Partial<SEOConfig>): void {
    this.config = { ...this.config, ...updates }
  }
}

// Create global SEO manager instance
export const seoManager = new SEOManager()

// Convenience functions
export const generateMetaTags = (options?: MetaTags) => {
  return seoManager.generateMetaTags(options)
}

export const generateProductStructuredData = (product: ProductSEO, url?: string) => {
  return seoManager.generateProductStructuredData(product, url)
}

export const generateArticleStructuredData = (article: ArticleSEO, url?: string) => {
  return seoManager.generateArticleStructuredData(article, url)
}

export const analyzeSEO = (content: Parameters<typeof seoManager.analyzeSEO>[0]) => {
  return seoManager.analyzeSEO(content)
}

// React hook for SEO
export const useSEO = () => {
  return {
    generateMetaTags,
    generateProductStructuredData,
    generateArticleStructuredData,
    generateOrganizationStructuredData: () => seoManager.generateOrganizationStructuredData(),
    generateWebsiteStructuredData: () => seoManager.generateWebsiteStructuredData(),
    generateBreadcrumbStructuredData: (breadcrumbs: Array<{ name: string; url: string }>) => 
      seoManager.generateBreadcrumbStructuredData(breadcrumbs),
    generateFAQStructuredData: (faqs: Array<{ question: string; answer: string }>) => 
      seoManager.generateFAQStructuredData(faqs),
    analyzeSEO,
    getConfig: () => seoManager.getConfig()
  }
}

// Utility to extract page content for SEO analysis
export const extractPageContent = (): Parameters<typeof seoManager.analyzeSEO>[0] => {
  const title = document.title
  const description = document.querySelector('meta[name="description"]')?.getAttribute('content') || ''
  const content = document.body.innerText
  
  // Extract keywords from meta tag
  const keywordsTag = document.querySelector('meta[name="keywords"]')?.getAttribute('content')
  const keywords = keywordsTag ? keywordsTag.split(',').map(k => k.trim()) : []
  
  // Extract images
  const images = Array.from(document.querySelectorAll('img')).map(img => img.src)
  
  // Extract headings
  const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(heading => ({
    level: parseInt(heading.tagName.charAt(1)),
    text: heading.textContent || ''
  }))
  
  // Extract links
  const links = Array.from(document.querySelectorAll('a[href]')).map(link => ({
    href: (link as HTMLAnchorElement).href,
    text: link.textContent || '',
    external: !(link as HTMLAnchorElement).href.startsWith(window.location.origin)
  }))

  return {
    title,
    description,
    content,
    keywords,
    images,
    headings,
    links
  }
}

export type { SEOConfig, MetaTags, ProductSEO, ArticleSEO }
export default SEOManager