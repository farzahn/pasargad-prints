import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    hmr: {
      clientPort: 443
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
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
})