import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// Staging configuration - similar to production but with some differences
export default defineConfig(({ command, mode }) => {
  // Load env from root directory
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  
  return {
    plugins: [
      react({
        babel: {
          plugins: [
            ['babel-plugin-react-remove-properties', { properties: ['data-testid'] }]
          ]
        }
      }),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.ico', 'icon-192x192.png', 'icon-512x512.png'],
        manifest: {
          name: 'Pasargad Prints - Staging',
          short_name: 'Pasargad Staging',
          description: 'Staging environment for Pasargad Prints',
          theme_color: '#f59e0b',
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
          maximumFileSizeToCacheInBytes: 5000000,
          skipWaiting: true,
          clientsClaim: true,
          cleanupOutdatedCaches: true
        }
      })
    ],

    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
      __COMMIT_HASH__: JSON.stringify(process.env.COMMIT_HASH || 'staging'),
      __ENVIRONMENT__: JSON.stringify('staging')
    },

    // Build optimizations (less aggressive than production)
    build: {
      target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: true, // Keep sourcemaps for debugging
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: false, // Keep console logs for debugging
          drop_debugger: false,
          passes: 1
        },
        mangle: {
          safari10: true
        }
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom'],
            store: ['@reduxjs/toolkit', 'react-redux'],
            ui: ['react-toastify', 'react-hook-form'],
            charts: ['recharts']
          }
        }
      },
      // Performance
      chunkSizeWarningLimit: 1500
    },

    // Server configuration
    server: {
      host: '0.0.0.0',
      port: parseInt(env.VITE_PORT) || 3000,
      strictPort: true,
      hmr: {
        port: 3000
      },
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