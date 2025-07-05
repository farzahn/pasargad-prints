// Advanced Sitemap Generator for React SPA
import { getOptimizedImageUrl } from './cdn'

interface SitemapUrl {
  loc: string
  lastmod?: string
  changefreq?: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never'
  priority?: number
  images?: Array<{
    loc: string
    caption?: string
    title?: string
    license?: string
  }>
  alternates?: Array<{
    href: string
    hreflang: string
  }>
  news?: {
    publication: {
      name: string
      language: string
    }
    publication_date: string
    title: string
    keywords?: string
  }
  video?: Array<{
    thumbnail_loc: string
    title: string
    description: string
    content_loc?: string
    player_loc?: string
    duration?: number
    expiration_date?: string
    rating?: number
    view_count?: number
    publication_date?: string
    family_friendly?: boolean
    restriction?: {
      relationship: 'allow' | 'deny'
      countries: string[]
    }
    platform?: {
      relationship: 'allow' | 'deny'
      platforms: string[]
    }
    requires_subscription?: boolean
    uploader?: {
      name: string
      info?: string
    }
    live?: boolean
  }>
}

interface SitemapConfig {
  baseUrl: string
  defaultChangefreq: SitemapUrl['changefreq']
  defaultPriority: number
  enableImages: boolean
  enableNews: boolean
  enableVideo: boolean
  enableAlternates: boolean
  supportedLanguages: string[]
  excludePatterns: RegExp[]
  includeLastmod: boolean
  prettyPrint: boolean
}

class SitemapGenerator {
  private config: SitemapConfig
  private urls: SitemapUrl[] = []

  constructor(config: Partial<SitemapConfig> = {}) {
    this.config = {
      baseUrl: import.meta.env.VITE_SITE_URL || 'https://pasargadprints.com',
      defaultChangefreq: 'weekly',
      defaultPriority: 0.5,
      enableImages: true,
      enableNews: false,
      enableVideo: false,
      enableAlternates: true,
      supportedLanguages: ['en'],
      excludePatterns: [
        /\/admin\//,
        /\/api\//,
        /\/private\//,
        /\?.*$/,
        /\/test\//,
        /\/dev\//
      ],
      includeLastmod: true,
      prettyPrint: true,
      ...config
    }
  }

  // Add a single URL to the sitemap
  addUrl(url: SitemapUrl): void {
    // Validate and normalize URL
    const normalizedUrl = this.normalizeUrl(url)
    if (!this.shouldIncludeUrl(normalizedUrl.loc)) {
      return
    }

    // Check for duplicates
    const existingIndex = this.urls.findIndex(u => u.loc === normalizedUrl.loc)
    if (existingIndex !== -1) {
      // Update existing URL
      this.urls[existingIndex] = normalizedUrl
    } else {
      this.urls.push(normalizedUrl)
    }
  }

  // Add multiple URLs
  addUrls(urls: SitemapUrl[]): void {
    urls.forEach(url => this.addUrl(url))
  }

  // Add static pages
  addStaticPages(): void {
    const staticPages = [
      {
        loc: '/',
        priority: 1.0,
        changefreq: 'daily' as const
      },
      {
        loc: '/products',
        priority: 0.9,
        changefreq: 'daily' as const
      },
      {
        loc: '/about',
        priority: 0.7,
        changefreq: 'monthly' as const
      },
      {
        loc: '/contact',
        priority: 0.6,
        changefreq: 'monthly' as const
      },
      {
        loc: '/help',
        priority: 0.6,
        changefreq: 'weekly' as const
      },
      {
        loc: '/privacy',
        priority: 0.3,
        changefreq: 'yearly' as const
      },
      {
        loc: '/terms',
        priority: 0.3,
        changefreq: 'yearly' as const
      },
      {
        loc: '/shipping',
        priority: 0.5,
        changefreq: 'monthly' as const
      },
      {
        loc: '/returns',
        priority: 0.5,
        changefreq: 'monthly' as const
      }
    ]

    this.addUrls(staticPages.map(page => ({
      ...page,
      lastmod: this.config.includeLastmod ? new Date().toISOString() : undefined
    })))
  }

  // Add product pages from API
  async addProductPages(products?: any[]): Promise<void> {
    try {
      let productData = products
      
      if (!productData) {
        // Fetch products from API
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/products/sitemap/`)
        if (!response.ok) {
          throw new Error('Failed to fetch products')
        }
        productData = await response.json()
      }

      const productUrls: SitemapUrl[] = productData.map((product: any) => ({
        loc: `/products/${product.id}`,
        lastmod: product.updated_at || product.created_at,
        changefreq: 'weekly' as const,
        priority: 0.8,
        images: product.images?.map((image: any) => ({
          loc: getOptimizedImageUrl(image.url, { width: 1200, height: 1200 }),
          caption: image.caption || product.name,
          title: `${product.name} - ${image.caption || 'Product Image'}`,
          license: `${this.config.baseUrl}/license`
        })) || []
      }))

      this.addUrls(productUrls)
    } catch (error) {
      console.error('Error adding product pages to sitemap:', error)
    }
  }

  // Add category pages
  async addCategoryPages(categories?: any[]): Promise<void> {
    try {
      let categoryData = categories
      
      if (!categoryData) {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/categories/`)
        if (!response.ok) {
          throw new Error('Failed to fetch categories')
        }
        categoryData = await response.json()
      }

      const categoryUrls: SitemapUrl[] = categoryData.map((category: any) => ({
        loc: `/products?category=${category.slug}`,
        lastmod: category.updated_at || new Date().toISOString(),
        changefreq: 'daily' as const,
        priority: 0.7
      }))

      this.addUrls(categoryUrls)
    } catch (error) {
      console.error('Error adding category pages to sitemap:', error)
    }
  }

  // Add blog/article pages
  async addBlogPages(articles?: any[]): Promise<void> {
    try {
      let articleData = articles
      
      if (!articleData) {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/blog/sitemap/`)
        if (!response.ok) {
          console.warn('No blog endpoint available')
          return
        }
        articleData = await response.json()
      }

      const articleUrls: SitemapUrl[] = articleData.map((article: any) => ({
        loc: `/blog/${article.slug}`,
        lastmod: article.updated_at || article.published_at,
        changefreq: 'monthly' as const,
        priority: 0.6,
        images: article.featured_image ? [{
          loc: getOptimizedImageUrl(article.featured_image, { width: 1200, height: 630 }),
          caption: article.title,
          title: article.title
        }] : [],
        ...(this.config.enableNews && {
          news: {
            publication: {
              name: 'Pasargad Prints Blog',
              language: 'en'
            },
            publication_date: article.published_at,
            title: article.title,
            keywords: article.tags?.join(', ')
          }
        })
      }))

      this.addUrls(articleUrls)
    } catch (error) {
      console.error('Error adding blog pages to sitemap:', error)
    }
  }

  // Generate sitemap index for large sites
  generateSitemapIndex(sitemaps: Array<{ loc: string; lastmod?: string }>): string {
    const xml = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    sitemaps.forEach(sitemap => {
      xml.push('  <sitemap>')
      xml.push(`    <loc>${this.escapeXml(sitemap.loc)}</loc>`)
      if (sitemap.lastmod) {
        xml.push(`    <lastmod>${sitemap.lastmod}</lastmod>`)
      }
      xml.push('  </sitemap>')
    })

    xml.push('</sitemapindex>')
    return xml.join(this.config.prettyPrint ? '\n' : '')
  }

  // Generate main sitemap XML
  generateSitemap(): string {
    const sortedUrls = [...this.urls].sort((a, b) => {
      // Sort by priority (high to low), then by URL
      const priorityDiff = (b.priority || 0.5) - (a.priority || 0.5)
      if (priorityDiff !== 0) return priorityDiff
      return a.loc.localeCompare(b.loc)
    })

    const xml = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
    ]

    // Add namespace declarations based on enabled features
    if (this.config.enableImages) {
      xml[1] += ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"'
    }
    if (this.config.enableNews) {
      xml[1] += ' xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"'
    }
    if (this.config.enableVideo) {
      xml[1] += ' xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"'
    }
    if (this.config.enableAlternates) {
      xml[1] += ' xmlns:xhtml="http://www.w3.org/1999/xhtml"'
    }

    xml[1] += '>'

    sortedUrls.forEach(url => {
      xml.push('  <url>')
      xml.push(`    <loc>${this.escapeXml(this.getAbsoluteUrl(url.loc))}</loc>`)
      
      if (url.lastmod) {
        xml.push(`    <lastmod>${this.formatDate(url.lastmod)}</lastmod>`)
      }
      
      if (url.changefreq) {
        xml.push(`    <changefreq>${url.changefreq}</changefreq>`)
      }
      
      if (url.priority !== undefined) {
        xml.push(`    <priority>${url.priority.toFixed(1)}</priority>`)
      }

      // Add alternate language links
      if (this.config.enableAlternates && url.alternates) {
        url.alternates.forEach(alt => {
          xml.push(`    <xhtml:link rel="alternate" hreflang="${alt.hreflang}" href="${this.escapeXml(alt.href)}" />`)
        })
      }

      // Add images
      if (this.config.enableImages && url.images) {
        url.images.forEach(image => {
          xml.push('    <image:image>')
          xml.push(`      <image:loc>${this.escapeXml(this.getAbsoluteUrl(image.loc))}</image:loc>`)
          if (image.caption) {
            xml.push(`      <image:caption>${this.escapeXml(image.caption)}</image:caption>`)
          }
          if (image.title) {
            xml.push(`      <image:title>${this.escapeXml(image.title)}</image:title>`)
          }
          if (image.license) {
            xml.push(`      <image:license>${this.escapeXml(image.license)}</image:license>`)
          }
          xml.push('    </image:image>')
        })
      }

      // Add news information
      if (this.config.enableNews && url.news) {
        xml.push('    <news:news>')
        xml.push('      <news:publication>')
        xml.push(`        <news:name>${this.escapeXml(url.news.publication.name)}</news:name>`)
        xml.push(`        <news:language>${url.news.publication.language}</news:language>`)
        xml.push('      </news:publication>')
        xml.push(`      <news:publication_date>${this.formatDate(url.news.publication_date)}</news:publication_date>`)
        xml.push(`      <news:title>${this.escapeXml(url.news.title)}</news:title>`)
        if (url.news.keywords) {
          xml.push(`      <news:keywords>${this.escapeXml(url.news.keywords)}</news:keywords>`)
        }
        xml.push('    </news:news>')
      }

      // Add video information
      if (this.config.enableVideo && url.video) {
        url.video.forEach(video => {
          xml.push('    <video:video>')
          xml.push(`      <video:thumbnail_loc>${this.escapeXml(this.getAbsoluteUrl(video.thumbnail_loc))}</video:thumbnail_loc>`)
          xml.push(`      <video:title>${this.escapeXml(video.title)}</video:title>`)
          xml.push(`      <video:description>${this.escapeXml(video.description)}</video:description>`)
          
          if (video.content_loc) {
            xml.push(`      <video:content_loc>${this.escapeXml(this.getAbsoluteUrl(video.content_loc))}</video:content_loc>`)
          }
          if (video.player_loc) {
            xml.push(`      <video:player_loc>${this.escapeXml(this.getAbsoluteUrl(video.player_loc))}</video:player_loc>`)
          }
          if (video.duration) {
            xml.push(`      <video:duration>${video.duration}</video:duration>`)
          }
          if (video.rating) {
            xml.push(`      <video:rating>${video.rating}</video:rating>`)
          }
          if (video.view_count) {
            xml.push(`      <video:view_count>${video.view_count}</video:view_count>`)
          }
          if (video.publication_date) {
            xml.push(`      <video:publication_date>${this.formatDate(video.publication_date)}</video:publication_date>`)
          }
          if (video.family_friendly !== undefined) {
            xml.push(`      <video:family_friendly>${video.family_friendly ? 'yes' : 'no'}</video:family_friendly>`)
          }
          if (video.requires_subscription !== undefined) {
            xml.push(`      <video:requires_subscription>${video.requires_subscription ? 'yes' : 'no'}</video:requires_subscription>`)
          }
          if (video.live !== undefined) {
            xml.push(`      <video:live>${video.live ? 'yes' : 'no'}</video:live>`)
          }
          
          xml.push('    </video:video>')
        })
      }

      xml.push('  </url>')
    })

    xml.push('</urlset>')
    return xml.join(this.config.prettyPrint ? '\n' : '')
  }

  // Generate robots.txt content
  generateRobotsTxt(): string {
    const lines = [
      'User-agent: *',
      'Allow: /',
      '',
      '# Disallow admin and private areas',
      'Disallow: /admin/',
      'Disallow: /api/',
      'Disallow: /private/',
      'Disallow: /*?*',
      '',
      '# Allow specific crawlers for CSS and JS',
      'User-agent: Googlebot',
      'Allow: *.css',
      'Allow: *.js',
      '',
      '# Sitemap location',
      `Sitemap: ${this.config.baseUrl}/sitemap.xml`,
      '',
      '# Crawl delay',
      'Crawl-delay: 1'
    ]

    return lines.join('\n')
  }

  // Helper methods
  private normalizeUrl(url: SitemapUrl): SitemapUrl {
    return {
      ...url,
      loc: url.loc.replace(/\/$/, '') || '/', // Remove trailing slash except for root
      lastmod: url.lastmod || (this.config.includeLastmod ? new Date().toISOString() : undefined),
      changefreq: url.changefreq || this.config.defaultChangefreq,
      priority: url.priority !== undefined ? url.priority : this.config.defaultPriority
    }
  }

  private shouldIncludeUrl(url: string): boolean {
    return !this.config.excludePatterns.some(pattern => pattern.test(url))
  }

  private getAbsoluteUrl(url: string): string {
    if (url.startsWith('http')) {
      return url
    }
    return `${this.config.baseUrl}${url.startsWith('/') ? '' : '/'}${url}`
  }

  private escapeXml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;')
  }

  private formatDate(date: string): string {
    return new Date(date).toISOString().split('T')[0]
  }

  // Get current URLs
  getUrls(): SitemapUrl[] {
    return [...this.urls]
  }

  // Clear all URLs
  clear(): void {
    this.urls = []
  }

  // Get statistics
  getStats() {
    const stats = {
      totalUrls: this.urls.length,
      byPriority: {} as Record<string, number>,
      byChangefreq: {} as Record<string, number>,
      withImages: 0,
      withNews: 0,
      withVideo: 0,
      withAlternates: 0
    }

    this.urls.forEach(url => {
      // Priority stats
      const priority = (url.priority || 0.5).toFixed(1)
      stats.byPriority[priority] = (stats.byPriority[priority] || 0) + 1

      // Changefreq stats
      const changefreq = url.changefreq || 'weekly'
      stats.byChangefreq[changefreq] = (stats.byChangefreq[changefreq] || 0) + 1

      // Feature stats
      if (url.images && url.images.length > 0) stats.withImages++
      if (url.news) stats.withNews++
      if (url.video && url.video.length > 0) stats.withVideo++
      if (url.alternates && url.alternates.length > 0) stats.withAlternates++
    })

    return stats
  }
}

// Create and configure sitemap generator
export const createSitemapGenerator = (config?: Partial<SitemapConfig>) => {
  return new SitemapGenerator(config)
}

// Generate complete sitemap for the application
export const generateCompleteSitemap = async (): Promise<string> => {
  const generator = createSitemapGenerator()

  // Add static pages
  generator.addStaticPages()

  // Add dynamic content
  await Promise.all([
    generator.addProductPages(),
    generator.addCategoryPages(),
    generator.addBlogPages()
  ])

  return generator.generateSitemap()
}

// Generate robots.txt
export const generateRobotsTxt = (): string => {
  const generator = createSitemapGenerator()
  return generator.generateRobotsTxt()
}

// Utility function to download sitemap as file
export const downloadSitemap = async (filename = 'sitemap.xml'): Promise<void> => {
  const sitemap = await generateCompleteSitemap()
  const blob = new Blob([sitemap], { type: 'application/xml' })
  const url = URL.createObjectURL(blob)
  
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  try {
    if (document.body.contains(a)) {
      a.remove()
    }
  } catch (error) {
    console.debug('Download link cleanup error:', error)
  }
  URL.revokeObjectURL(url)
}

// Utility function to validate sitemap
export const validateSitemap = (xml: string): { valid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  try {
    // Basic XML validation
    const parser = new DOMParser()
    const doc = parser.parseFromString(xml, 'application/xml')
    const parseError = doc.querySelector('parsererror')
    
    if (parseError) {
      errors.push('Invalid XML format')
    }

    // Check for required elements
    const urlset = doc.querySelector('urlset')
    if (!urlset) {
      errors.push('Missing urlset element')
    }

    const urls = doc.querySelectorAll('url')
    if (urls.length === 0) {
      errors.push('No URLs found in sitemap')
    }

    // Validate each URL
    urls.forEach((urlElement, index) => {
      const loc = urlElement.querySelector('loc')
      if (!loc || !loc.textContent) {
        errors.push(`URL ${index + 1}: Missing loc element`)
      }

      const priority = urlElement.querySelector('priority')
      if (priority && priority.textContent) {
        const priorityValue = parseFloat(priority.textContent)
        if (priorityValue < 0 || priorityValue > 1) {
          errors.push(`URL ${index + 1}: Priority must be between 0.0 and 1.0`)
        }
      }
    })

  } catch (error) {
    errors.push(`Validation error: ${error.message}`)
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

export default SitemapGenerator