import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary.tsx'
import { store } from './store'
import { setStore } from './services/api'

// Setup API with store reference
setStore(store)

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
