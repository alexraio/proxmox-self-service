/**
 * Axios client pre-configured for the Proxmox Self-Service API.
 * - Automatically attaches the JWT from localStorage as a Bearer token.
 * - Clears auth state and redirects to /login on 401 responses.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: '/',           // Vite proxy rewrites /auth, /machines, /config → FastAPI
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

/** Attach JWT to every outgoing request. */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** Handle 401 globally: clear storage and bounce to login. */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api
