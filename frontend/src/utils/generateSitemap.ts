// Production-ready sitemap generator
// This utility generates XML sitemaps for SEO optimization

export interface SitemapEntry {
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
}

export interface SitemapIndex {
  loc: string
  lastmod?: string
}

export interface SitemapConfig {
  baseUrl: string
  defaultChangefreq: SitemapEntry['changefreq']
  defaultPriority: number
  maxUrlsPerSitemap: number
  enableImageSitemap: boolean
  enableAlternateLanguages: boolean
  supportedLocales: string[]
}

// Default sitemap configuration
export const getDefaultSitemapConfig = (): SitemapConfig => ({
  baseUrl: import.meta.env.VITE_SITE_URL || 'https://pasargadprints.com',
  defaultChangefreq: 'weekly',
  defaultPriority: 0.5,
  maxUrlsPerSitemap: 50000,
  enableImageSitemap: true,
  enableAlternateLanguages: import.meta.env.VITE_SUPPORTED_LOCALES !== 'en',
  supportedLocales: (import.meta.env.VITE_SUPPORTED_LOCALES || 'en').split(',')
});

// Generate standard sitemap XML
export const generateSitemapXML = (entries: SitemapEntry[], config?: Partial<SitemapConfig>): string => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  
  const namespaces = [
    'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
    cfg.enableImageSitemap ? 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' : '',
    cfg.enableAlternateLanguages ? 'xmlns:xhtml="http://www.w3.org/1999/xhtml"' : ''
  ].filter(Boolean).join(' ');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset ${namespaces}>
${entries.map(entry => {
  const images = entry.images && cfg.enableImageSitemap ? 
    entry.images.map(img => `    <image:image>
      <image:loc>${cfg.baseUrl}${img.loc}</image:loc>
      ${img.caption ? `<image:caption>${escapeXml(img.caption)}</image:caption>` : ''}
      ${img.title ? `<image:title>${escapeXml(img.title)}</image:title>` : ''}
      ${img.license ? `<image:license>${img.license}</image:license>` : ''}
    </image:image>`).join('\n') : '';

  const alternates = entry.alternates && cfg.enableAlternateLanguages ?
    entry.alternates.map(alt => `    <xhtml:link rel="alternate" hreflang="${alt.hreflang}" href="${alt.href}" />`).join('\n') : '';

  return `  <url>
    <loc>${cfg.baseUrl}${entry.loc}</loc>
    ${entry.lastmod ? `<lastmod>${entry.lastmod}</lastmod>` : ''}
    ${entry.changefreq ? `<changefreq>${entry.changefreq}</changefreq>` : ''}
    ${entry.priority !== undefined ? `<priority>${entry.priority}</priority>` : ''}
${images}
${alternates}
  </url>`;
}).join('\n')}
</urlset>`;

  return xml;
};

// Generate sitemap index XML for multiple sitemaps
export const generateSitemapIndexXML = (sitemaps: SitemapIndex[], config?: Partial<SitemapConfig>): string => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemaps.map(sitemap => `  <sitemap>
    <loc>${cfg.baseUrl}${sitemap.loc}</loc>
    ${sitemap.lastmod ? `<lastmod>${sitemap.lastmod}</lastmod>` : ''}
  </sitemap>`).join('\n')}
</sitemapindex>`;

  return xml;
};

// XML escape utility
const escapeXml = (text: string): string => {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
};

// Static pages with comprehensive SEO configuration
export const getStaticPages = (config?: Partial<SitemapConfig>): SitemapEntry[] => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  const now = new Date().toISOString();
  
  const basePages: SitemapEntry[] = [
    { 
      loc: '/', 
      changefreq: 'daily', 
      priority: 1.0,
      lastmod: now
    },
    { 
      loc: '/products', 
      changefreq: 'daily', 
      priority: 0.9,
      lastmod: now
    },
    { 
      loc: '/cart', 
      changefreq: 'weekly', 
      priority: 0.3 
    },
    { 
      loc: '/checkout', 
      changefreq: 'monthly', 
      priority: 0.2 
    },
    { 
      loc: '/login', 
      changefreq: 'yearly', 
      priority: 0.3 
    },
    { 
      loc: '/register', 
      changefreq: 'yearly', 
      priority: 0.3 
    },
    { 
      loc: '/profile', 
      changefreq: 'monthly', 
      priority: 0.4 
    },
    { 
      loc: '/wishlist', 
      changefreq: 'weekly', 
      priority: 0.4 
    },
    { 
      loc: '/orders/track', 
      changefreq: 'monthly', 
      priority: 0.4 
    }
  ];

  // Add alternate language versions if enabled
  if (cfg.enableAlternateLanguages && cfg.supportedLocales.length > 1) {
    return basePages.map(page => ({
      ...page,
      alternates: cfg.supportedLocales.map(locale => ({
        href: `${cfg.baseUrl}${locale === 'en' ? '' : `/${locale}`}${page.loc}`,
        hreflang: locale
      }))
    }));
  }

  return basePages;
};

// Generate product sitemap entries with image support
export const generateProductSitemapEntries = (
  products: Array<{
    id: number;
    slug?: string;
    name?: string;
    updated_at?: string;
    images?: Array<{
      url: string;
      alt?: string;
      title?: string;
    }>;
  }>,
  config?: Partial<SitemapConfig>
): SitemapEntry[] => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  
  return products.map(product => {
    const loc = product.slug ? `/products/${product.slug}` : `/products/${product.id}`;
    const entry: SitemapEntry = {
      loc,
      lastmod: product.updated_at,
      changefreq: 'weekly',
      priority: 0.8
    };

    // Add product images to sitemap
    if (cfg.enableImageSitemap && product.images?.length) {
      entry.images = product.images.map(img => ({
        loc: img.url,
        caption: img.alt || product.name,
        title: img.title || product.name
      }));
    }

    // Add alternate language versions
    if (cfg.enableAlternateLanguages && cfg.supportedLocales.length > 1) {
      entry.alternates = cfg.supportedLocales.map(locale => ({
        href: `${cfg.baseUrl}${locale === 'en' ? '' : `/${locale}`}${loc}`,
        hreflang: locale
      }));
    }

    return entry;
  });
};

// Generate category sitemap entries
export const generateCategorySitemapEntries = (
  categories: Array<{
    id: number;
    slug: string;
    name?: string;
    updated_at?: string;
    image?: string;
  }>,
  config?: Partial<SitemapConfig>
): SitemapEntry[] => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  
  return categories.map(category => {
    const loc = `/products/category/${category.slug}`;
    const entry: SitemapEntry = {
      loc,
      lastmod: category.updated_at,
      changefreq: 'weekly',
      priority: 0.7
    };

    // Add category image
    if (cfg.enableImageSitemap && category.image) {
      entry.images = [{
        loc: category.image,
        caption: `${category.name} category`,
        title: category.name
      }];
    }

    // Add alternate language versions
    if (cfg.enableAlternateLanguages && cfg.supportedLocales.length > 1) {
      entry.alternates = cfg.supportedLocales.map(locale => ({
        href: `${cfg.baseUrl}${locale === 'en' ? '' : `/${locale}`}${loc}`,
        hreflang: locale
      }));
    }

    return entry;
  });
};

// Generate blog/content sitemap entries
export const generateContentSitemapEntries = (
  content: Array<{
    id: number;
    slug: string;
    title?: string;
    published_at?: string;
    updated_at?: string;
    featured_image?: string;
  }>,
  config?: Partial<SitemapConfig>
): SitemapEntry[] => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  
  return content.map(post => {
    const loc = `/blog/${post.slug}`;
    const entry: SitemapEntry = {
      loc,
      lastmod: post.updated_at || post.published_at,
      changefreq: 'monthly',
      priority: 0.6
    };

    // Add featured image
    if (cfg.enableImageSitemap && post.featured_image) {
      entry.images = [{
        loc: post.featured_image,
        caption: post.title,
        title: post.title
      }];
    }

    // Add alternate language versions
    if (cfg.enableAlternateLanguages && cfg.supportedLocales.length > 1) {
      entry.alternates = cfg.supportedLocales.map(locale => ({
        href: `${cfg.baseUrl}${locale === 'en' ? '' : `/${locale}`}${loc}`,
        hreflang: locale
      }));
    }

    return entry;
  });
};

// Split large sitemaps into multiple files
export const splitSitemapEntries = (
  entries: SitemapEntry[],
  maxUrlsPerSitemap: number = 50000
): SitemapEntry[][] => {
  const chunks: SitemapEntry[][] = [];
  
  for (let i = 0; i < entries.length; i += maxUrlsPerSitemap) {
    chunks.push(entries.slice(i, i + maxUrlsPerSitemap));
  }
  
  return chunks;
};

// Generate complete sitemap structure
export const generateCompleteSitemap = async (
  data: {
    products?: any[];
    categories?: any[];
    content?: any[];
  },
  config?: Partial<SitemapConfig>
): Promise<{
  sitemaps: Array<{ name: string; content: string }>;
  index?: string;
}> => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  const sitemaps: Array<{ name: string; content: string }> = [];
  const sitemapIndex: SitemapIndex[] = [];
  
  // Static pages sitemap
  const staticEntries = getStaticPages(cfg);
  const staticChunks = splitSitemapEntries(staticEntries, cfg.maxUrlsPerSitemap);
  
  staticChunks.forEach((chunk, index) => {
    const name = index === 0 ? 'sitemap-static.xml' : `sitemap-static-${index + 1}.xml`;
    const content = generateSitemapXML(chunk, cfg);
    sitemaps.push({ name, content });
    sitemapIndex.push({
      loc: `/${name}`,
      lastmod: new Date().toISOString()
    });
  });
  
  // Products sitemap
  if (data.products?.length) {
    const productEntries = generateProductSitemapEntries(data.products, cfg);
    const productChunks = splitSitemapEntries(productEntries, cfg.maxUrlsPerSitemap);
    
    productChunks.forEach((chunk, index) => {
      const name = index === 0 ? 'sitemap-products.xml' : `sitemap-products-${index + 1}.xml`;
      const content = generateSitemapXML(chunk, cfg);
      sitemaps.push({ name, content });
      sitemapIndex.push({
        loc: `/${name}`,
        lastmod: new Date().toISOString()
      });
    });
  }
  
  // Categories sitemap
  if (data.categories?.length) {
    const categoryEntries = generateCategorySitemapEntries(data.categories, cfg);
    const content = generateSitemapXML(categoryEntries, cfg);
    sitemaps.push({ name: 'sitemap-categories.xml', content });
    sitemapIndex.push({
      loc: '/sitemap-categories.xml',
      lastmod: new Date().toISOString()
    });
  }
  
  // Content sitemap
  if (data.content?.length) {
    const contentEntries = generateContentSitemapEntries(data.content, cfg);
    const content = generateSitemapXML(contentEntries, cfg);
    sitemaps.push({ name: 'sitemap-content.xml', content });
    sitemapIndex.push({
      loc: '/sitemap-content.xml',
      lastmod: new Date().toISOString()
    });
  }
  
  // Generate sitemap index if multiple sitemaps
  const index = sitemapIndex.length > 1 
    ? generateSitemapIndexXML(sitemapIndex, cfg)
    : undefined;
  
  return { sitemaps, index };
};

// Robots.txt generator
export const generateRobotsTxt = (config?: Partial<SitemapConfig>): string => {
  const cfg = { ...getDefaultSitemapConfig(), ...config };
  
  return `User-agent: *
Allow: /

# Sitemaps
Sitemap: ${cfg.baseUrl}/sitemap.xml
${cfg.enableImageSitemap ? `Sitemap: ${cfg.baseUrl}/sitemap-images.xml` : ''}

# Disallow admin and checkout pages
Disallow: /admin/
Disallow: /checkout/
Disallow: /cart/
Disallow: /login/
Disallow: /register/
Disallow: /profile/

# Disallow search and filter URLs
Disallow: /*?*sort=
Disallow: /*?*filter=
Disallow: /*?*page=

# Crawl delay (optional)
Crawl-delay: 1

# Host directive
Host: ${cfg.baseUrl}`;
};