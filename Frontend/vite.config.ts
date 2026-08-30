import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const SPA_ROUTES = new Set([
  '/',
  '/about',
  '/interview-types',
  '/code-arena',
  '/roadmaps',
  '/dashboard',
  '/practice',
  '/dsa-interview',
  '/general-interview',
  '/system-design-interview',
  '/discussion',
  '/chat',
  '/login',
  '/signup',
  '/pre-join',
  '/profile',
  '/analysis',
  '/admin',
]);

const createProxyRule = (target: string) => ({
  target,
  changeOrigin: true,
  secure: false,
  ws: true,
  bypass: (req: any) => {
    const url = (req.url || '').split('?')[0];
    const accept = req.headers?.accept || '';
    const secFetchDest = req.headers?.['sec-fetch-dest'] || '';
    const secFetchMode = req.headers?.['sec-fetch-mode'] || '';

    // If it's a direct HTML navigation / refresh or matches a frontend SPA route
    if (
      req.method === 'GET' &&
      (
        accept.includes('text/html') ||
        secFetchDest === 'document' ||
        secFetchMode === 'navigate' ||
        SPA_ROUTES.has(url) ||
        url.startsWith('/profile/') ||
        url.startsWith('/dsa-practice')
      )
    ) {
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
      '/api/v1': createProxyRule('http://localhost:8000'),
      '/api/admin': createProxyRule('http://localhost:8002'),
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
