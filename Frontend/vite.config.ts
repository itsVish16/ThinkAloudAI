import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api/v1/users': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/v1/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/dsa': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/roadmaps': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/system-design': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/behavioral': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/pm': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/aiml': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/dashboard': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/sessions': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      }
    }
  }
})
