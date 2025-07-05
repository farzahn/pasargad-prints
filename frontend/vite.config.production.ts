import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { visualizer } from 'rollup-plugin-visualizer'
import { createHtmlPlugin } from 'vite-plugin-html'
import { compression } from 'vite-plugin-compression'
import { resolve } from 'path'
import pwaConfig from './vite.config.sw'

// Production-optimized Vite configuration
export default defineConfig(({ command, mode }) => {
  // Load env from root directory
  const env = loadEnv(mode, resolve(__dirname, '..'), '')
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
        ...pwaConfig,
        // Override for production-specific settings
        disable: false,
        workbox: {
          ...pwaConfig.workbox,
          // Production-specific runtime caching overrides
          runtimeCaching: [
            // Use environment-specific API URL
            {
              urlPattern: new RegExp(`^${env.VITE_API_URL || 'https://api.pasargadprints.com'}/.*$`),
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
                networkTimeoutSeconds: 10
              }
            },
            ...pwaConfig.workbox?.runtimeCaching?.slice(1) || []
          ]
        }
      }),
      // HTML processing plugin
      createHtmlPlugin({
        minify: isProduction,
        inject: {
          data: {
            title: 'Pasargad Prints - Premium 3D Printing Store',
            description: 'Discover high-quality 3D printing products, materials, and services at Pasargad Prints.',
            googleAnalyticsId: env.VITE_GOOGLE_ANALYTICS_ID || '',
            googleTagManagerId: env.VITE_GOOGLE_TAG_MANAGER_ID || '',
            buildTime: new Date().toISOString(),
            version: process.env.npm_package_version || '1.0.0'
          }
        }
      }),

      // Compression plugins
      isProduction && compression({
        algorithm: 'gzip',
        ext: '.gz',
        deleteOriginFile: false,
        threshold: 1024,
        compressionOptions: {
          level: 9
        }
      }),

      isProduction && compression({
        algorithm: 'brotliCompress',
        ext: '.br',
        deleteOriginFile: false,
        threshold: 1024,
        compressionOptions: {
          params: {
            [require('zlib').constants.BROTLI_PARAM_QUALITY]: 11
          }
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
          pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.warn'],
          passes: 3,
          unsafe: true,
          unsafe_comps: true,
          unsafe_math: true,
          unsafe_symbols: true,
          unsafe_methods: true,
          unsafe_proto: true,
          unsafe_regexp: true,
          conditionals: true,
          dead_code: true,
          evaluate: true,
          if_return: true,
          join_vars: true,
          loops: true,
          negate_iife: true,
          properties: true,
          reduce_vars: true,
          sequences: true,
          side_effects: false,
          switches: true,
          top_retain: null,
          typeofs: true,
          unused: true,
          arguments: true,
          booleans: true,
          collapse_vars: true,
          comparisons: true,
          hoist_funs: true,
          hoist_props: true,
          hoist_vars: false,
          inline: true,
          keep_infinity: false,
          toplevel: true
        },
        mangle: {
          safari10: true,
          toplevel: true,
          properties: {
            regex: /^_/
          }
        },
        format: {
          comments: false,
          ecma: 2020,
          safari10: true
        }
      } : undefined,
      rollupOptions: {
        treeshake: {
          moduleSideEffects: false,
          propertyReadSideEffects: false,
          tryCatchDeoptimization: false,
          unknownGlobalSideEffects: false
        },
        output: {
          manualChunks(id) {
            // Core React chunk (most frequently used)
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-core'
            }
            
            // Store and state management
            if (id.includes('@reduxjs/toolkit') || id.includes('react-redux')) {
              return 'store-vendor'
            }
            
            // Router chunk
            if (id.includes('react-router')) {
              return 'router-vendor'
            }
            
            // UI Library chunks
            if (id.includes('react-toastify') || id.includes('react-hook-form') || id.includes('@hookform')) {
              return 'ui-vendor'
            }
            
            // Charts and visualization
            if (id.includes('recharts') || id.includes('d3-')) {
              return 'charts-vendor'
            }
            
            // Payment processing
            if (id.includes('@stripe')) {
              return 'payment-vendor'
            }
            
            // HTTP client and API
            if (id.includes('axios')) {
              return 'api-vendor'
            }
            
            // Form validation
            if (id.includes('zod') || id.includes('yup')) {
              return 'validation-vendor'
            }
            
            // Date utilities
            if (id.includes('date-fns')) {
              return 'date-vendor'
            }
            
            // PDF and document processing
            if (id.includes('jspdf') || id.includes('xlsx') || id.includes('file-saver')) {
              return 'document-vendor'
            }
            
            // Admin functionality (lazy loaded)
            if (id.includes('/src/pages/admin/') || id.includes('/src/components/admin/')) {
              return 'admin'
            }
            
            // E-commerce specific features
            if (id.includes('/src/pages/') && (id.includes('Checkout') || id.includes('Cart'))) {
              return 'checkout'
            }
            
            // Product related features
            if (id.includes('/src/pages/') && (id.includes('Product') || id.includes('Wishlist'))) {
              return 'product'
            }
            
            // Authentication features
            if (id.includes('/src/pages/') && (id.includes('Login') || id.includes('Register') || id.includes('Profile'))) {
              return 'auth'
            }
            
            // Other vendor libraries
            if (id.includes('node_modules')) {
              // Group smaller libraries together
              if (id.includes('tslib') || id.includes('scheduler') || id.includes('object-assign')) {
                return 'polyfill-vendor'
              }
              return 'vendor'
            }
            
            // Utility functions
            if (id.includes('/src/utils/')) {
              return 'utils'
            }
            
            // Store slices
            if (id.includes('/src/store/')) {
              return 'store'
            }
            
            // Services
            if (id.includes('/src/services/')) {
              return 'services'
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
      assetsInlineLimit: 4096, // 4KB inline limit
      cssCodeSplit: true,
      cssMinify: isProduction ? 'esbuild' : false,
      // Performance optimizations
      reportCompressedSize: isProduction,
      chunkSizeWarningLimit: 800, // Stricter chunk size limits
      // Improve build performance
      emptyOutDir: true,
      // Enable incremental builds
      watch: !isProduction ? {
        buildDelay: 100,
        exclude: ['node_modules/**', 'dist/**']
      } : undefined,
      // Additional build optimizations
      maxParallelFileOps: 4
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