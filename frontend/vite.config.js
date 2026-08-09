import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

const gameAssetSource = resolve(fileURLToPath(new URL('./game-assets', import.meta.url)))

function gameAssetFiles(directory, prefix = '') {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name)
    const name = prefix ? `${prefix}/${entry.name}` : entry.name
    return entry.isDirectory() ? gameAssetFiles(path, name) : [{ name, path }]
  })
}

function gameAssetPlugin(assetMode) {
  return {
    name: 'authorized-game-assets',
    configureServer(server) {
      server.middlewares.use('/build-assets/game', (request, response, next) => {
        if (assetMode !== 'game') return next()
        const requestPath = decodeURIComponent((request.url || '').split('?')[0]).replace(/^\/+/, '')
        const candidate = resolve(gameAssetSource, requestPath)
        if (!candidate.startsWith(`${gameAssetSource}/`) || !statSafe(candidate)) return next()
        response.setHeader('Content-Type', contentType(candidate))
        response.end(readFileSync(candidate))
      })
    },
    generateBundle() {
      if (assetMode !== 'game') return
      for (const asset of gameAssetFiles(gameAssetSource)) {
        this.emitFile({ type: 'asset', fileName: `build-assets/game/${asset.name}`, source: readFileSync(asset.path) })
      }
    },
  }
}

function statSafe(path) {
  try { return statSync(path).isFile() } catch { return false }
}

function contentType(path) {
  if (path.endsWith('.png')) return 'image/png'
  if (path.endsWith('.svg')) return 'image/svg+xml'
  return 'application/octet-stream'
}

function loadDevServerConfig() {
  const configUrl = new URL('./config/dev-server.json', import.meta.url)
  return JSON.parse(readFileSync(configUrl, 'utf8'))
}

const devServer = loadDevServerConfig()

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const assetMode = env.VITE_BUILD_ASSET_MODE === 'game' ? 'game' : 'neutral'
  return {
    plugins: [vue(), gameAssetPlugin(assetMode)],
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
  }
})
