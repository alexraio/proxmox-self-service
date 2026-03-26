import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/machines': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
