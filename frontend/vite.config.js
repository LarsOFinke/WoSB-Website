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
