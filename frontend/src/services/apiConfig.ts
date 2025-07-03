import axios from 'axios'

// When VITE_API_URL is empty, use relative URLs which work with ngrok
// This allows the frontend to work with any domain/tunnel without hardcoding URLs
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CORS with credentials
})

export default api