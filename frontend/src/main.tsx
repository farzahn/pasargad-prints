import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary.tsx'
import { store } from './store'
import { setStore } from './services/api'
// import { registerSW } from 'virtual:pwa-register'

// Setup API with store reference
setStore(store)

// Register service worker
// if ('serviceWorker' in navigator) {
//   const updateSW = registerSW({
//     onNeedRefresh() {
//       // Show a prompt to reload when new content is available
//       if (confirm('New content available. Reload?')) {
//         updateSW(true)
//       }
//     },
//     onOfflineReady() {
//       console.log('App ready to work offline')
//     },
//   })
// }

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
