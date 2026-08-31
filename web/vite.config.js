import path from 'node:path'
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { demoApiMiddleware } from './demo-api.mjs'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

function sentinelDemoApiPlugin() {
  return {
    name: 'sentinel-demo-api',
    configureServer(server) {
      server.middlewares.use(demoApiMiddleware)
    },
    configurePreviewServer(server) {
      server.middlewares.use(demoApiMiddleware)
    },
  }
}

export default defineConfig({
  plugins: [sentinelDemoApiPlugin(), react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(rootDir, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass(req) {
          if (req.url?.split('?')[0].startsWith('/api/demo')) return req.url
        },
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
})
