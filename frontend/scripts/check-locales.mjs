import { createServer } from 'vite'

const SAME_VALUE_ALLOWLIST = new Set([
  'Royal Blackwater Fleet', 'Royal Blackwater Fleet MVP', 'Royal Blackwater', 'Fleet', 'RBF', '12:00–02:00 CET', '18:00–23:00 CET', 'WoSB', 'MVP', 'API', 'PDF', 'GIF', 'MP4', 'JPEG', 'PNG', 'WebP', 'WebM', 'MOV', '-----BEGIN OPENSSH PRIVATE KEY-----',
  'Forum', 'Guides', 'Admin', 'PvE', 'PvP', 'Support', 'Builds', 'Hold', 'Lanterns', 'Sails', 'Sources', 'Fleet', 'Profiles', 'Weapons',
  'Rate', 'Type', 'Crew', 'Upgrades', 'Status', 'Details', 'Thread', 'Threads', 'Video', 'Text', 'Image', 'Training', 'Operation',
  'Focus', 'Description', 'Contact', 'Combat', 'General', 'API online', 'Upgrade {index}', 'Crew {current}/{max}',
  'Rate {value}', '{value}', 'Crew {value}', 'Crew: {current} / {max}', '1 build', '{count} builds', '1 guide', '{count} guides',
])


const DYNAMIC_KEY_CONTRACTS = [
  'forum.categories.all',
  'forum.categories.general',
  'forum.categories.builds',
  'forum.categories.events',
  'forum.categories.support',
  'forum.categories.training',
  'forum.categories.logistics',
  'forum.categories.loistics',
  'guides.categories.all',
  'guides.categories.general',
  'guides.categories.builds',
  'guides.categories.combat',
  'guides.categories.economy',
  'groups.status.open',
  'groups.status.full',
  'groups.status.closed',
  'focus.pve_farming',
  'focus.pve_imp_hunting',
  'focus.pve_general',
  'focus.pvp_open_world',
  'focus.pvp_arena',
  'focus.pvp_general',
  'focus.trading',
  'focus.other',
  'fleets.status.pending',
  'fleets.status.active',
  'fleets.status.inactive',
]

const PSEUDO_PREFIX_PATTERN = /^(DE|FR|ES|PT|RU|CN)\s*[·:]\s*/

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
    const pseudoLocalized = Object.entries(entries).filter(([, value]) => typeof value === 'string' && PSEUDO_PREFIX_PATTERN.test(value))
    const missingDynamicKeys = DYNAMIC_KEY_CONTRACTS.filter((key) => !(key in entries))

    errorTotal += missing.length + englishFallbacks.length + pseudoLocalized.length + missingDynamicKeys.length
    console.log(`${locale}: ${Object.keys(entries).length} keys, missing ${missing.length}, english-fallback ${englishFallbacks.length}, pseudo ${pseudoLocalized.length}, dynamic-missing ${missingDynamicKeys.length}`)
    if (missing.length > 0) console.log(missing.map((key) => `  - missing ${key}`).join('\n'))
    if (missingDynamicKeys.length > 0) console.log(missingDynamicKeys.map((key) => `  - missing dynamic ${key}`).join('\n'))
    if (pseudoLocalized.length > 0) {
      console.log(pseudoLocalized.slice(0, 50).map(([key, value]) => `  - pseudo ${key}: ${value}`).join('\n'))
      if (pseudoLocalized.length > 50) console.log(`  ... ${pseudoLocalized.length - 50} more`)
    }
    if (englishFallbacks.length > 0) {
      console.log(englishFallbacks.slice(0, 50).map(([key, value]) => `  - fallback ${key}: ${value}`).join('\n'))
      if (englishFallbacks.length > 50) console.log(`  ... ${englishFallbacks.length - 50} more`)
    }
  }

  if (errorTotal > 0) process.exitCode = 1
} finally {
  await server.close()
}
