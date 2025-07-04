// Enhanced Sitemap Generation System

export interface SitemapEntry {
  loc: string;
  lastmod?: string;
  changefreq?: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  priority?: number;
  images?: SitemapImage[];
}

export interface SitemapImage {
  loc: string;
  caption?: string;
  geoLocation?: string;
  title?: string;
  license?: string;
}

export interface SitemapIndex {
  loc: string;
  lastmod?: string;
}

// Generate XML sitemap
export const generateSitemapXML = (baseUrl: string, entries: SitemapEntry[]): string => {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" 
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
${entries.map(entry => `  <url>
    <loc>${baseUrl}${entry.loc}</loc>
    ${entry.lastmod ? `<lastmod>${entry.lastmod}</lastmod>` : ''}
    ${entry.changefreq ? `<changefreq>${entry.changefreq}</changefreq>` : ''}
    ${entry.priority ? `<priority>${entry.priority}</priority>` : ''}
    ${entry.images ? entry.images.map(img => `<image:image>
      <image:loc>${img.loc}</image:loc>
      ${img.caption ? `<image:caption>${img.caption}</image:caption>` : ''}
      ${img.title ? `<image:title>${img.title}</image:title>` : ''}
      ${img.license ? `<image:license>${img.license}</image:license>` : ''}
    </image:image>`).join('\n    ') : ''}
  </url>`).join('\n')}
</urlset>`;

  return xml;
};

// Generate sitemap index
export const generateSitemapIndex = (baseUrl: string, sitemaps: SitemapIndex[]): string => {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemaps.map(sitemap => `  <sitemap>
    <loc>${baseUrl}${sitemap.loc}</loc>
    ${sitemap.lastmod ? `<lastmod>${sitemap.lastmod}</lastmod>` : ''}
  </sitemap>`).join('\n')}
</sitemapindex>`;

  return xml;
};

// Static pages sitemap
export const getStaticPagesSitemap = (): SitemapEntry[] => [
  { 
    loc: '/', 
    changefreq: 'daily', 
    priority: 1.0,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/products', 
    changefreq: 'daily', 
    priority: 0.9,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/about', 
    changefreq: 'monthly', 
    priority: 0.6,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/contact', 
    changefreq: 'monthly', 
    priority: 0.5,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/terms', 
    changefreq: 'yearly', 
    priority: 0.3,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/privacy', 
    changefreq: 'yearly', 
    priority: 0.3,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/shipping', 
    changefreq: 'monthly', 
    priority: 0.4,
    lastmod: new Date().toISOString().split('T')[0]
  },
  { 
    loc: '/returns', 
    changefreq: 'monthly', 
    priority: 0.4,
    lastmod: new Date().toISOString().split('T')[0]
  }
];

// Generate product sitemap entries
export const generateProductsSitemap = (products: any[]): SitemapEntry[] => {
  return products.map(product => ({
    loc: `/products/${product.id}`,
    lastmod: product.updated_at ? new Date(product.updated_at).toISOString().split('T')[0] : undefined,
    changefreq: 'weekly' as const,
    priority: 0.8,
    images: product.images?.map((img: any) => ({
      loc: img.image_url || img.image,
      caption: img.alt_text || product.name,
      title: product.name
    }))
  }));
};

// Generate category sitemap entries
export const generateCategoriesSitemap = (categories: any[]): SitemapEntry[] => {
  return categories.map(category => ({
    loc: `/products?category=${category.id}`,
    lastmod: category.updated_at ? new Date(category.updated_at).toISOString().split('T')[0] : undefined,
    changefreq: 'weekly' as const,
    priority: 0.7
  }));
};

// Generate blog sitemap entries (if blog exists)
export const generateBlogSitemap = (posts: any[]): SitemapEntry[] => {
  return posts.map(post => ({
    loc: `/blog/${post.slug}`,
    lastmod: post.updated_at ? new Date(post.updated_at).toISOString().split('T')[0] : undefined,
    changefreq: 'monthly' as const,
    priority: 0.6,
    images: post.featured_image ? [{
      loc: post.featured_image,
      caption: post.title,
      title: post.title
    }] : undefined
  }));
};

// Generate complete sitemap
export const generateCompleteSitemap = async (baseUrl: string): Promise<{
  mainSitemap: string;
  productsSitemap: string;
  categoriesSitemap: string;
  sitemapIndex: string;
}> => {
  try {
    // Fetch data from API
    const [productsResponse, categoriesResponse] = await Promise.all([
      fetch('/api/products/'),
      fetch('/api/categories/')
    ]);

    const products = await productsResponse.json();
    const categories = await categoriesResponse.json();

    // Generate individual sitemaps
    const staticEntries = getStaticPagesSitemap();
    const productEntries = generateProductsSitemap(products.results || products);
    const categoryEntries = generateCategoriesSitemap(categories.results || categories);

    const mainSitemap = generateSitemapXML(baseUrl, staticEntries);
    const productsSitemap = generateSitemapXML(baseUrl, productEntries);
    const categoriesSitemap = generateSitemapXML(baseUrl, categoryEntries);

    // Generate sitemap index
    const sitemapIndex = generateSitemapIndex(baseUrl, [
      { loc: '/sitemap.xml', lastmod: new Date().toISOString().split('T')[0] },
      { loc: '/sitemap-products.xml', lastmod: new Date().toISOString().split('T')[0] },
      { loc: '/sitemap-categories.xml', lastmod: new Date().toISOString().split('T')[0] }
    ]);

    return {
      mainSitemap,
      productsSitemap,
      categoriesSitemap,
      sitemapIndex
    };
  } catch (error) {
    console.error('Error generating sitemap:', error);
    throw error;
  }
};

// Generate robots.txt
export const generateRobotsTxt = (baseUrl: string): string => {
  return `# Robots.txt for Pasargad Prints

User-agent: *
Allow: /

# Directories
Allow: /products/
Allow: /categories/
Allow: /blog/
Allow: /about/
Allow: /contact/

# Disallow admin and sensitive paths
Disallow: /admin/
Disallow: /api/
Disallow: /checkout/
Disallow: /cart/
Disallow: /profile/
Disallow: /login/
Disallow: /register/
Disallow: /orders/
Disallow: /wishlist/
Disallow: /search?*
Disallow: /*?*
Disallow: /assets/
Disallow: /fonts/
Disallow: /images/private/

# Crawl delay
Crawl-delay: 1

# Sitemap
Sitemap: ${baseUrl}/sitemap-index.xml
Sitemap: ${baseUrl}/sitemap.xml
Sitemap: ${baseUrl}/sitemap-products.xml
Sitemap: ${baseUrl}/sitemap-categories.xml

# Specific bots
User-agent: Googlebot
Allow: /
Crawl-delay: 1

User-agent: Bingbot
Allow: /
Crawl-delay: 1

User-agent: Slurp
Allow: /
Crawl-delay: 2

User-agent: facebookexternalhit
Allow: /

User-agent: Twitterbot
Allow: /`;
};

// Build-time sitemap generation
export const buildSitemaps = async (outputDir: string, baseUrl: string): Promise<void> => {
  try {
    const { mainSitemap, productsSitemap, categoriesSitemap, sitemapIndex } = 
      await generateCompleteSitemap(baseUrl);

    const robotsTxt = generateRobotsTxt(baseUrl);

    // Write files (this would typically be done in a build script)
    console.log('Generated sitemaps and robots.txt');
    
    // In a real implementation, you would write these to the output directory
    // const fs = require('fs');
    // fs.writeFileSync(path.join(outputDir, 'sitemap.xml'), mainSitemap);
    // fs.writeFileSync(path.join(outputDir, 'sitemap-products.xml'), productsSitemap);
    // fs.writeFileSync(path.join(outputDir, 'sitemap-categories.xml'), categoriesSitemap);
    // fs.writeFileSync(path.join(outputDir, 'sitemap-index.xml'), sitemapIndex);
    // fs.writeFileSync(path.join(outputDir, 'robots.txt'), robotsTxt);
    
  } catch (error) {
    console.error('Error building sitemaps:', error);
    throw error;
  }
};