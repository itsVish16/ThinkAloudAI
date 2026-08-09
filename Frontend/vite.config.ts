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
      '/chat': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/users': {
        target: 'http://44.244.222.102:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api/v1/admin': {
        target: 'http://44.244.222.102:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api/token': {
        target: 'http://44.244.222.102:8002',
        changeOrigin: true,
        secure: false,
      },
      '/api/interview-types': {
        target: 'http://44.244.222.102:8002',
        changeOrigin: true,
        secure: false,
      },
      '/api/interview': {
        target: 'http://44.244.222.102:8002',
        changeOrigin: true,
        secure: false,
      },
      '/api/interviews': {
        target: 'http://44.244.222.102:8002',
        changeOrigin: true,
        secure: false,
      },
      '/api/admin': {
        target: 'http://44.244.222.102:8002',
        changeOrigin: true,
        secure: false,
      },
      '/api/leaderboard': {
        target: 'http://44.244.222.102:8002',
        changeOrigin: true,
        secure: false,
      },
      '/sessions': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/roadmaps': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/dsa': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/users': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/admin/coding': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      },
      '/admin/roadmaps': {
        target: 'http://44.244.222.102:8001',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
