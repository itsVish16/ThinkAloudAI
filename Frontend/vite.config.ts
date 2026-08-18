import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const createProxyRule = (target: string) => ({
  target,
  changeOrigin: true,
  bypass: (req: any) => {
    if (req.headers.accept?.includes('text/html')) {
      return '/index.html';
    }
  },
});

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
      '/api/v1/users': createProxyRule('http://localhost:8000'),
      '/api/v1/admin': createProxyRule('http://localhost:8000'),
      '/api': createProxyRule('http://localhost:8002'),
      '/chat': createProxyRule('http://localhost:8001'),
      '/dsa': createProxyRule('http://localhost:8001'),
      '/roadmaps': createProxyRule('http://localhost:8001'),
      '/system-design': createProxyRule('http://localhost:8001'),
      '/behavioral': createProxyRule('http://localhost:8001'),
      '/pm': createProxyRule('http://localhost:8001'),
      '/aiml': createProxyRule('http://localhost:8001'),
      '/dashboard': createProxyRule('http://localhost:8001'),
      '/admin': createProxyRule('http://localhost:8001'),
      '/sessions': createProxyRule('http://localhost:8001'),
      '/users': createProxyRule('http://localhost:8001'),
    }
  }
})
