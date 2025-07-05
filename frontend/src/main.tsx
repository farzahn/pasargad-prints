import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary.tsx'
import { store } from './store'
import { setStore } from './services/api'
import { registerSW } from 'virtual:pwa-register'
import { initServiceWorker } from './utils/serviceWorker'

// Setup API with store reference
setStore(store)

// Register service worker
if ('serviceWorker' in navigator) {
  // Initialize custom service worker manager
  initServiceWorker()

  // Register PWA service worker
  const updateSW = registerSW({
    onNeedRefresh() {
      // Show a prompt to reload when new content is available
      const userChoice = window.confirm(
        'New content is available! Click OK to refresh and get the latest version.'
      )
      if (userChoice) {
        updateSW(true)
      }
    },
    onOfflineReady() {
      console.log('App ready to work offline')
      // You can show a toast notification here
    },
    onRegisterError(error) {
      console.error('Service worker registration failed:', error)
    },
  })
}

const root = document.getElementById('root')
if (!root) {
  console.error('Root element not found!')
} else {
  createRoot(root).render(
    <StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </StrictMode>
  )
}
