import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { visualizer } from 'rollup-plugin-visualizer'
import path from 'path'

// Production-optimized Vite configuration
export default defineConfig(({ command, mode }) => {
  // Load env from root directory
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  const isProduction = mode === 'production'
  
  return {
    plugins: [
      react({
        babel: {
          plugins: isProduction ? [
            ['babel-plugin-react-remove-properties', { properties: ['data-testid'] }]
          ] : []
        }
      }),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'icon-192x192.png', 'icon-512x512.png'],
        manifest: {
          name: 'Pasargad Prints - 3D Printing Store',
          short_name: 'Pasargad Prints',
          description: 'Premium 3D printing products and services',
          theme_color: '#2563eb',
          background_color: '#ffffff',
          display: 'standalone',
          scope: '/',
          start_url: '/',
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
            }
          ]
        },
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,jpg,jpeg,webp,woff,woff2}'],
          maximumFileSizeToCacheInBytes: 5000000, // 5MB
          skipWaiting: true,
          clientsClaim: true,
          cleanupOutdatedCaches: true,
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/api\./i,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                expiration: {
                  maxEntries: 50,
                  maxAgeSeconds: 5 * 60 // 5 minutes
                },
                cacheableResponse: {
                  statuses: [0, 200]
                },
                networkTimeoutSeconds: 3
              }
            },
            {
              urlPattern: /\.(png|jpg|jpeg|svg|webp|avif)$/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'image-cache',
                expiration: {
                  maxEntries: 200,
                  maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
                }
              }
            },
            {
              urlPattern: /\.(woff|woff2|eot|ttf|otf)$/i,
              handler: 'CacheFirst',
              options: {
                cacheName: 'font-cache',
                expiration: {
                  maxEntries: 30,
                  maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
                }
              }
            },
            {
              urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com/,
              handler: 'StaleWhileRevalidate',
              options: {
                cacheName: 'google-fonts',
                expiration: {
                  maxEntries: 20,
                  maxAgeSeconds: 365 * 24 * 60 * 60 // 1 year
                }
              }
            }
          ]
        }
      }),
      // Bundle analyzer for production builds
      isProduction && visualizer({
        filename: 'dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
        template: 'treemap'
      })
    ].filter(Boolean),

    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
      __COMMIT_HASH__: JSON.stringify(process.env.COMMIT_HASH || 'dev')
    },

    // Build optimizations
    build: {
      target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: isProduction ? false : true,
      minify: isProduction ? 'terser' : false,
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info', 'console.debug'],
          passes: 2
        },
        mangle: {
          safari10: true
        },
        format: {
          comments: false
        }
      } : undefined,
      rollupOptions: {
        output: {
          manualChunks(id) {
            // Vendor chunks
            if (id.includes('node_modules')) {
              if (id.includes('react') || id.includes('react-dom')) {
                return 'react-vendor'
              }
              if (id.includes('@reduxjs/toolkit') || id.includes('react-redux')) {
                return 'store-vendor'
              }
              if (id.includes('react-router')) {
                return 'router-vendor'
              }
              if (id.includes('recharts') || id.includes('d3-')) {
                return 'charts-vendor'
              }
              if (id.includes('react-toastify') || id.includes('react-hook-form') || id.includes('@hookform')) {
                return 'ui-vendor'
              }
              if (id.includes('axios') || id.includes('@stripe')) {
                return 'api-vendor'
              }
              return 'vendor'
            }
            
            // Feature-based chunks
            if (id.includes('/src/pages/admin/')) {
              return 'admin'
            }
            if (id.includes('/src/pages/') && (id.includes('Checkout') || id.includes('Cart'))) {
              return 'checkout'
            }
            if (id.includes('/src/components/admin/')) {
              return 'admin-components'
            }
          },
          chunkFileNames: (chunkInfo) => {
            if (chunkInfo.name.includes('vendor')) {
              return 'vendor/[name]-[hash].js'
            }
            if (chunkInfo.name === 'admin' || chunkInfo.name === 'admin-components') {
              return 'admin/[name]-[hash].js'
            }
            return 'assets/js/[name]-[hash].js'
          },
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const extType = info[info.length - 1]
            
            if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name)) {
              return 'assets/media/[name]-[hash][extname]'
            } else if (/\.(png|jpe?g|gif|svg|webp|avif|ico)$/.test(assetInfo.name)) {
              return 'assets/images/[name]-[hash][extname]'
            } else if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name)) {
              return 'assets/fonts/[name]-[hash][extname]'
            } else if (/\.css$/.test(assetInfo.name)) {
              return 'assets/css/[name]-[hash][extname]'
            }
            
            return `assets/[name]-[hash][extname]`
          }
        },
        external: isProduction ? [] : undefined
      },
      // Asset optimization
      assetsInlineLimit: 4096, // 4KB
      cssCodeSplit: true,
      cssMinify: isProduction,
      // Performance
      reportCompressedSize: isProduction,
      chunkSizeWarningLimit: 1000,
      // Improve build performance
      emptyOutDir: true
    },

    // Server configuration
    server: {
      host: '0.0.0.0',
      port: parseInt(env.VITE_PORT) || 3000,
      strictPort: true,
      hmr: {
        port: 3000
      },
      allowedHosts: [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '10.100.100.118',
        '0709-24-17-91-122.ngrok-free.app',
        '.ngrok-free.app',
        '.ngrok.io'
      ],
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
        '/admin': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
        '/static': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
        '/media': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      }
    },
    
    // Preview server for production builds
    preview: {
      host: '0.0.0.0',
      port: 3000,
      strictPort: true,
      headers: {
        'Cache-Control': 'public, max-age=31536000',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
      }
    },
    
    // Optimization
    esbuild: {
      drop: isProduction ? ['console', 'debugger'] : [],
      legalComments: 'none'
    },
    
    // CSS processing
    css: {
      devSourcemap: !isProduction,
      preprocessorOptions: {
        scss: {
          additionalData: `$env: ${mode};`
        }
      }
    },
    
    // Resolve configuration
    resolve: {
      alias: {
        '@': '/src',
        '@components': '/src/components',
        '@pages': '/src/pages',
        '@utils': '/src/utils',
        '@store': '/src/store',
        '@types': '/src/types',
        '@services': '/src/services'
      }
    },
    
    // Specify the env directory to be the root
    envDir: path.resolve(__dirname, '..')
  }
})