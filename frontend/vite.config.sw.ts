// Advanced Service Worker Configuration for VitePWA
import type { VitePWAOptions } from 'vite-plugin-pwa'

export const pwaConfig: Partial<VitePWAOptions> = {
  registerType: 'autoUpdate',
  workbox: {
    // Cache configuration
    globPatterns: [
      '**/*.{js,css,html,ico,png,svg,jpg,jpeg,webp,avif,woff,woff2,ttf,eot}'
    ],
    globIgnores: [
      '**/node_modules/**/*',
      'sw.js',
      'workbox-*.js'
    ],
    
    // Maximum file size to cache (5MB)
    maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
    
    // Service Worker options
    skipWaiting: true,
    clientsClaim: true,
    cleanupOutdatedCaches: true,
    
    // Navigation fallback
    navigateFallback: '/index.html',
    navigateFallbackDenylist: [
      /^\/api\/.*/,
      /^\/admin\/.*/,
      /\.(?:png|jpg|jpeg|svg|gif|webp|avif|ico|woff|woff2|ttf|eot)$/
    ],
    
    // Runtime caching strategies
    runtimeCaching: [
      // API calls - Network First strategy
      {
        urlPattern: /^https:\/\/api\.pasargadprints\.com\/.*$/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-cache',
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 5 * 60 // 5 minutes
          },
          cacheableResponse: {
            statuses: [0, 200, 404]
          },
          networkTimeoutSeconds: 10,
          plugins: [
            {
              cacheKeyWillBeUsed: async ({ request }) => {
                // Remove auth tokens from cache keys for privacy
                const url = new URL(request.url)
                url.searchParams.delete('token')
                url.searchParams.delete('auth')
                return url.toString()
              },
              cachedResponseWillBeUsed: async ({ cachedResponse, request }) => {
                // Check if cached response is still valid
                if (cachedResponse) {
                  const dateHeader = cachedResponse.headers.get('date')
                  if (dateHeader) {
                    const date = new Date(dateHeader)
                    const now = new Date()
                    const age = now.getTime() - date.getTime()
                    // If older than 5 minutes, don't use cached response
                    if (age > 5 * 60 * 1000) {
                      return null
                    }
                  }
                }
                return cachedResponse
              }
            }
          ]
        }
      },
      
      // Product images - Cache First strategy
      {
        urlPattern: /^https:\/\/(cdn|static)\.pasargadprints\.com\/.*\.(png|jpg|jpeg|webp|avif)$/,
        handler: 'CacheFirst',
        options: {
          cacheName: 'product-images',
          expiration: {
            maxEntries: 500,
            maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
          },
          cacheableResponse: {
            statuses: [0, 200]
          }
        }
      },
      
      // Static assets - Cache First strategy
      {
        urlPattern: /.*\.(css|js|woff|woff2|ttf|eot|ico|svg)$/,
        handler: 'CacheFirst',
        options: {
          cacheName: 'static-assets',
          expiration: {
            maxEntries: 200,
            maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
          }
        }
      },
      
      // Google Fonts - Stale While Revalidate
      {
        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'google-fonts-stylesheets',
          expiration: {
            maxEntries: 10,
            maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
          }
        }
      },
      
      // Google Fonts - Cache First
      {
        urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/,
        handler: 'CacheFirst',
        options: {
          cacheName: 'google-fonts-webfonts',
          expiration: {
            maxEntries: 30,
            maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
          },
          cacheableResponse: {
            statuses: [0, 200]
          }
        }
      },
      
      // Third-party analytics - Network Only
      {
        urlPattern: /^https:\/\/(www\.google-analytics\.com|www\.googletagmanager\.com)\/.*/,
        handler: 'NetworkOnly'
      },
      
      // Stripe - Network Only for security
      {
        urlPattern: /^https:\/\/js\.stripe\.com\/.*/,
        handler: 'NetworkOnly'
      },
      
      // Document generation - Network First
      {
        urlPattern: /^https:\/\/api\.pasargadprints\.com\/.*\/(pdf|excel|csv)$/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'documents-cache',
          expiration: {
            maxEntries: 20,
            maxAgeSeconds: 60 * 60 // 1 hour
          },
          networkTimeoutSeconds: 30
        }
      },
      
      // User profile data - Network First
      {
        urlPattern: /^https:\/\/api\.pasargadprints\.com\/.*\/profile\/.*/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'profile-cache',
          expiration: {
            maxEntries: 10,
            maxAgeSeconds: 10 * 60 // 10 minutes
          },
          networkTimeoutSeconds: 5
        }
      },
      
      // Cart data - Network First (short cache)
      {
        urlPattern: /^https:\/\/api\.pasargadprints\.com\/.*\/cart\/.*/,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'cart-cache',
          expiration: {
            maxEntries: 5,
            maxAgeSeconds: 2 * 60 // 2 minutes
          },
          networkTimeoutSeconds: 3
        }
      },
      
      // Search results - Stale While Revalidate
      {
        urlPattern: /^https:\/\/api\.pasargadprints\.com\/.*\/search\/.*/,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'search-cache',
          expiration: {
            maxEntries: 50,
            maxAgeSeconds: 15 * 60 // 15 minutes
          }
        }
      },
      
      // Product catalog - Stale While Revalidate
      {
        urlPattern: /^https:\/\/api\.pasargadprints\.com\/.*\/products\/.*/,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'products-cache',
          expiration: {
            maxEntries: 200,
            maxAgeSeconds: 30 * 60 // 30 minutes
          }
        }
      },
      
      // Same-origin requests - Network First
      {
        urlPattern: ({ request }) => request.destination === 'document',
        handler: 'NetworkFirst',
        options: {
          cacheName: 'pages-cache',
          expiration: {
            maxEntries: 50,
            maxAgeSeconds: 24 * 60 * 60 // 24 hours
          },
          networkTimeoutSeconds: 3
        }
      }
    ],
    
    // Offline fallback pages
    offlineFallback: '/offline.html',
    
    // Additional Workbox configuration
    mode: 'production',
    sourcemap: false,
    
    // Background sync for form submissions
    // This requires custom service worker code
    additionalManifestEntries: [
      {
        url: '/offline.html',
        revision: null
      }
    ]
  },
  
  // Manifest configuration
  manifest: {
    name: 'Pasargad Prints - Premium 3D Printing Store',
    short_name: 'Pasargad Prints',
    description: 'Discover high-quality 3D printing products, materials, and services at Pasargad Prints. Shop printers, filaments, resins, and accessories from top brands.',
    theme_color: '#2563eb',
    background_color: '#ffffff',
    display: 'standalone',
    scope: '/',
    start_url: '/',
    orientation: 'portrait-primary',
    
    // Icons
    icons: [
      {
        src: '/icon-192x192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any maskable'
      },
      {
        src: '/icon-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any maskable'
      },
      {
        src: '/icon-apple-touch.png',
        sizes: '180x180',
        type: 'image/png',
        purpose: 'any'
      }
    ],
    
    // Categories
    categories: ['shopping', 'business', 'productivity'],
    
    // Screenshots for app stores
    screenshots: [
      {
        src: '/screenshot-desktop.png',
        sizes: '1920x1080',
        type: 'image/png',
        form_factor: 'wide',
        label: 'Desktop view of Pasargad Prints'
      },
      {
        src: '/screenshot-mobile.png',
        sizes: '390x844',
        type: 'image/png',
        form_factor: 'narrow',
        label: 'Mobile view of Pasargad Prints'
      }
    ],
    
    // Shortcuts
    shortcuts: [
      {
        name: 'Browse Products',
        short_name: 'Products',
        description: 'Browse our 3D printing products',
        url: '/products',
        icons: [
          {
            src: '/shortcut-products.png',
            sizes: '96x96',
            type: 'image/png'
          }
        ]
      },
      {
        name: 'My Cart',
        short_name: 'Cart',
        description: 'View items in your cart',
        url: '/cart',
        icons: [
          {
            src: '/shortcut-cart.png',
            sizes: '96x96',
            type: 'image/png'
          }
        ]
      },
      {
        name: 'My Profile',
        short_name: 'Profile',
        description: 'View your account and orders',
        url: '/profile',
        icons: [
          {
            src: '/shortcut-profile.png',
            sizes: '96x96',
            type: 'image/png'
          }
        ]
      }
    ],
    
    // Protocol handlers
    protocol_handlers: [
      {
        protocol: 'web+pasargadprints',
        url: '/product/%s'
      }
    ],
    
    // Related applications
    related_applications: [
      {
        platform: 'play',
        url: 'https://play.google.com/store/apps/details?id=com.pasargadprints.app',
        id: 'com.pasargadprints.app'
      }
    ],
    
    // Prefer related applications
    prefer_related_applications: false,
    
    // Share target
    share_target: {
      action: '/share-target',
      method: 'POST',
      enctype: 'multipart/form-data',
      params: {
        title: 'title',
        text: 'text',
        url: 'url',
        files: [
          {
            name: 'files',
            accept: ['image/*', '.pdf', '.stl', '.obj']
          }
        ]
      }
    }
  },
  
  // Development configuration
  devOptions: {
    enabled: false,
    type: 'module',
    navigateFallback: 'index.html'
  },
  
  // Build configuration
  includeAssets: [
    'favicon.ico',
    'apple-touch-icon.png',
    'icon-192x192.png',
    'icon-512x512.png',
    'manifest.json',
    'robots.txt',
    'sitemap.xml'
  ],
  
  // Disable service worker registration in development
  disable: process.env.NODE_ENV === 'development',
  
  // Use inject mode for better debugging
  injectRegister: 'auto',
  
  // Generate service worker
  strategies: 'generateSW',
  
  // Self-destroying service worker
  selfDestroying: false,
  
  // Filename for the service worker
  filename: 'sw.js',
  
  // Scope for the service worker
  scope: '/',
  
  // Base path
  base: '/'
}

export default pwaConfig