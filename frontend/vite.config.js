import { readFileSync } from 'node:fs'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

function loadDevServerConfig() {
  const configUrl = new URL('./config/dev-server.json', import.meta.url)
  return JSON.parse(readFileSync(configUrl, 'utf8'))
}

const devServer = loadDevServerConfig()

export default defineConfig({
  plugins: [vue()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: 'vue-vendor',
              test: /node_modules[\\/](?:vue|vue-router|@vue)[\\/]/,
              priority: 30,
            },
            {
              name: 'rich-text-vendor',
              test: /node_modules[\\/](?:markdown-it|dompurify|linkify-it|mdurl|uc\.micro)[\\/]/,
              priority: 20,
            },
            {
              name: 'vendor',
              test: /node_modules[\\/]/,
              priority: 10,
            },
          ],
        },
      },
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: devServer.host,
    port: devServer.port,
    strictPort: Boolean(devServer.strictPort),
    proxy: {
      '/api': devServer.proxyTarget,
      '/uploads': devServer.proxyTarget,
    },
  },
})
