import { createServer } from 'vite'

const SAME_VALUE_ALLOWLIST = new Set([
  'Iron Crown Fleet Hub', 'Iron Crown Fleet Hub MVP', 'WoSB', 'MVP', 'API', 'PDF', 'GIF', 'MP4', 'JPEG', 'PNG', 'WebP', 'WebM', 'MOV',
  'Forum', 'Guides', 'Admin', 'PvE', 'PvP', 'Support', 'Builds', 'Hold', 'Lanterns', 'Sails', 'Sources', 'Fleet', 'Profiles', 'Weapons',
  'Rate', 'Type', 'Crew', 'Upgrades', 'Status', 'Details', 'Thread', 'Threads', 'Video', 'Text', 'Image', 'Training', 'Operation',
  'Focus', 'Description', 'Contact', 'Combat', 'General', 'API online', 'Upgrade {index}', 'Crew {current}/{max}',
  'Rate {value}', '{value}', 'Crew {value}', 'Crew: {current} / {max}', '1 build', '{count} builds', '1 guide', '{count} guides',
])

function flattenEntries(obj, prefix = '') {
  return Object.entries(obj || {}).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key
    return value && typeof value === 'object' && !Array.isArray(value) ? flattenEntries(value, path) : [[path, value]]
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
  const englishEntries = Object.fromEntries(flattenEntries(messages.en))
  const allKeys = [...new Set(locales.flatMap((locale) => flattenEntries(messages[locale]).map(([key]) => key)))]
  let errorTotal = 0

  for (const locale of locales) {
    const entries = Object.fromEntries(flattenEntries(messages[locale]))
    const missing = allKeys.filter((key) => !(key in entries))
    const englishFallbacks = locale === 'en'
      ? []
      : Object.entries(englishEntries).filter(([key, englishValue]) => {
        const localizedValue = entries[key]
        return typeof englishValue === 'string'
          && englishValue === localizedValue
          && !SAME_VALUE_ALLOWLIST.has(englishValue)
      })

    errorTotal += missing.length + englishFallbacks.length
    console.log(`${locale}: ${Object.keys(entries).length} keys, missing ${missing.length}, english-fallback ${englishFallbacks.length}`)
    if (missing.length > 0) console.log(missing.map((key) => `  - missing ${key}`).join('\n'))
    if (englishFallbacks.length > 0) {
      console.log(englishFallbacks.slice(0, 50).map(([key, value]) => `  - fallback ${key}: ${value}`).join('\n'))
      if (englishFallbacks.length > 50) console.log(`  ... ${englishFallbacks.length - 50} more`)
    }
  }

  if (errorTotal > 0) process.exitCode = 1
} finally {
  await server.close()
}
