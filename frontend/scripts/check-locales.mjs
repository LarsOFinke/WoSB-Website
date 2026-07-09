import { createServer } from 'vite'

function flattenKeys(obj, prefix = '') {
  return Object.entries(obj || {}).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key
    return value && typeof value === 'object' && !Array.isArray(value) ? flattenKeys(value, path) : [path]
  })
}

const server = await createServer({
  root: process.cwd(),
  logLevel: 'silent',
  server: { middlewareMode: true },
  appType: 'custom',
})

try {
  const { messages } = await server.ssrLoadModule('/src/locales/messages/index.js')
  const locales = Object.keys(messages)
  const allKeys = [...new Set(locales.flatMap((locale) => flattenKeys(messages[locale])))]
  let missingTotal = 0

  for (const locale of locales) {
    const keys = new Set(flattenKeys(messages[locale]))
    const missing = allKeys.filter((key) => !keys.has(key))
    missingTotal += missing.length
    console.log(`${locale}: ${keys.size} keys, missing ${missing.length}`)
    if (missing.length > 0) console.log(missing.map((key) => `  - ${key}`).join('\n'))
  }

  if (missingTotal > 0) process.exitCode = 1
} finally {
  await server.close()
}
