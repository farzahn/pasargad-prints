import { Helmet } from 'react-helmet-async'
import { getOptimizedImageUrl } from '../utils/cdn'

interface SEOProps {
  title?: string
  description?: string
  keywords?: string
  image?: string
  url?: string
  type?: string
  author?: string
  publishedTime?: string
  modifiedTime?: string
  section?: string
  tags?: string[]
  price?: {
    amount: number
    currency: string
  }
  availability?: 'in_stock' | 'out_of_stock' | 'pre_order'
  rating?: {
    value: number
    count: number
  }
  noIndex?: boolean
  noFollow?: boolean
  canonical?: string
  alternateUrls?: { href: string; hrefLang: string }[]
}

const SEO = ({ 
  title = 'Pasargad Prints - Premium 3D Printing Store',
  description = 'Discover high-quality 3D printing products, materials, and services at Pasargad Prints. Shop printers, filaments, resins, and accessories from top brands.',
  keywords = '3D printing, 3D printers, filament, resin, PLA, ABS, PETG, 3D printing services, Pasargad Prints',
  image = '/og-image.jpg',
  url = window.location.href,
  type = 'website',
  author,
  publishedTime,
  modifiedTime,
  section,
  tags,
  price,
  availability,
  rating,
  noIndex = false,
  noFollow = false,
  canonical,
  alternateUrls
}: SEOProps) => {
  const siteTitle = title.includes('Pasargad Prints') ? title : `${title} | Pasargad Prints`
  const optimizedImage = getOptimizedImageUrl(image, { width: 1200, height: 630, format: 'webp' })
  
  // Generate robots meta content
  const robotsContent = [
    noIndex ? 'noindex' : 'index',
    noFollow ? 'nofollow' : 'follow',
    'noarchive',
    'noimageindex'
  ].join(', ')

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{siteTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      {author && <meta name="author" content={author} />}
      
      {/* Open Graph Meta Tags */}
      <meta property="og:title" content={siteTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={optimizedImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:image:type" content="image/webp" />
      <meta property="og:site_name" content="Pasargad Prints" />
      <meta property="og:locale" content="en_US" />
      
      {/* Article specific Open Graph tags */}
      {type === 'article' && (
        <>
          {publishedTime && <meta property="article:published_time" content={publishedTime} />}
          {modifiedTime && <meta property="article:modified_time" content={modifiedTime} />}
          {author && <meta property="article:author" content={author} />}
          {section && <meta property="article:section" content={section} />}
          {tags?.map(tag => (
            <meta key={tag} property="article:tag" content={tag} />
          ))}
        </>
      )}
      
      {/* Product specific Open Graph tags */}
      {type === 'product' && (
        <>
          {price && (
            <>
              <meta property="product:price:amount" content={price.amount.toString()} />
              <meta property="product:price:currency" content={price.currency} />
            </>
          )}
          {availability && <meta property="product:availability" content={availability} />}
          {rating && (
            <>
              <meta property="product:rating:value" content={rating.value.toString()} />
              <meta property="product:rating:count" content={rating.count.toString()} />
            </>
          )}
        </>
      )}
      
      {/* Twitter Card Meta Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={siteTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={optimizedImage} />
      <meta name="twitter:site" content="@pasargadprints" />
      
      {/* Additional SEO Meta Tags */}
      <meta name="robots" content={robotsContent} />
      <link rel="canonical" href={canonical || url} />
      
      {/* Alternate URLs for different languages */}
      {alternateUrls?.map(alt => (
        <link key={alt.hrefLang} rel="alternate" href={alt.href} hrefLang={alt.hrefLang} />
      ))}
      
      {/* PWA Meta Tags */}
      <meta name="theme-color" content="#2563eb" />
      <meta name="msapplication-TileColor" content="#2563eb" />
      <meta name="application-name" content="Pasargad Prints" />
      <meta name="apple-mobile-web-app-title" content="Pasargad Prints" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      <meta name="mobile-web-app-capable" content="yes" />
      <meta name="format-detection" content="telephone=no" />
      <link rel="manifest" href="/manifest.json" />
      
      {/* Apple Touch Icons */}
      <link rel="apple-touch-icon" href="/icon-192x192.png" />
      <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
      
      {/* Favicon */}
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
      <link rel="icon" href="/favicon.ico" />
      
      {/* Preconnect to external domains */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link rel="preconnect" href="https://www.google-analytics.com" />
      <link rel="preconnect" href="https://www.googletagmanager.com" />
      
      {/* DNS Prefetch */}
      <link rel="dns-prefetch" href="https://cdn.pasargadprints.com" />
      <link rel="dns-prefetch" href="https://static.pasargadprints.com" />
      
      {/* Structured Data will be handled by separate components */}
    </Helmet>
  )
}

export default SEO