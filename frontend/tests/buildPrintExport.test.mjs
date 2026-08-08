import test from 'node:test'
import assert from 'node:assert/strict'

import {
  BUILD_PRINT_RENDERER_VERSION,
  buildPrintFileName,
  createBuildPrintDocument,
  createBuildPrintHtml,
  createEmbeddedBuildPrintDocument,
  createBuildPrintModel,
  createBuildPrintSvg,
  inlinePrintImageResources,
} from '../src/modules/builds/buildPrintExport.js'
import { createBuildPrintCacheDescriptor, fetchBuildPrintPngBlob } from '../src/modules/builds/buildPrintCache.js'

const translations = {
  'builds.statLabels.durability': 'Durability',
  'builds.statLabels.speed_knots': 'Speed',
  'builds.statLabels.maneuverability': 'Maneuverability',
  'builds.statLabels.armor': 'Armor',
  'builds.statLabels.hold_capacity': 'Hold',
  'builds.statLabels.crew_capacity': 'Crew capacity',
  'builds.statLabels.sailor_minimum': 'Sailor minimum',
  'builds.statLabels.displacement_tons': 'Displacement',
  'builds.types.balanced': 'Balanced',
  'builds.detail.buildType': 'Build type',
  'builds.detail.shipStats': 'Ship stats',
  'builds.detail.weaponCapacity': 'Capacity {count}',
  'builds.detail.crewDistribution': 'Crew distribution',
  'builds.commandDeck.crewRemaining': '{value} crew remaining',
  'common.rate': 'Rate',
  'builds.list.upgradeSummary': '{used}/{max} upgrades',
  'builds.detail.weapons.front': 'Front weapons',
  'builds.detail.weapons.port': 'Port weapons',
  'builds.detail.weapons.starboard': 'Starboard weapons',
  'builds.detail.weapons.rear': 'Rear weapons',
  'builds.detail.weapons.mortar': 'Mortar weapons',
  'builds.detail.weapons.special': 'Special weapons',
  'builds.detail.noDetails': 'No details',
  'builds.create.crew.sailors': 'Sailors',
  'builds.create.crew.musketeers': 'Musketeers',
  'builds.create.crew.soldiers': 'Soldiers',
  'builds.create.crew.mercenaries': 'Mercenaries',
  'builds.list.sailorMin': 'Min {value}',
  'builds.detail.sail': 'Sail',
  'builds.detail.lantern': 'Lantern',
  'builds.detail.researchUpgradeSlot': 'Research slot',
  'builds.detail.researchUpgradeSlotActive': 'Unlocked',
  'builds.detail.researchUpgradeSlotInactive': 'Locked',
  'builds.commandDeck.performanceEyebrow': 'Performance',
  'builds.commandDeck.performanceTitle': 'Ship performance',
  'builds.crewConsole.eyebrow': 'Crew operations',
  'builds.commandDeck.configurationEyebrow': 'Configuration',
  'builds.detail.upgrades': 'Upgrades',
  'builds.detail.specialCrew': 'Special crew',
  'builds.detail.inventory': 'Inventory',
  'builds.detail.ammunition': 'Ammunition',
  'builds.detail.consumables': 'Consumables',
  'builds.detail.hold': 'Hold',
  'builds.detail.details': 'Details',
  'builds.print.eyebrow': 'Offline build sheet',
  'builds.print.fallbackTitle': 'Build sheet',
  'builds.print.preparedAt': 'Prepared {value}',
  'builds.print.configurationTitle': 'Configuration snapshot',
  'builds.print.weaponLoadoutTitle': 'Weapon loadout',
  'builds.print.inventoryTitle': 'Ammunition and hold',
  'builds.print.notesTitle': 'Captain notes',
  'builds.print.footerHint': 'Prepared from the live build designer for offline review and print distribution.',
  'builds.print.footerBrand': 'Royal Blackwater Fleet · Build Designer',
  'builds.print.previewTitle': 'Build sheet preview',
  'print.themeLabel': 'Appearance',
  'print.themeSystem': 'System',
  'print.themeLight': 'Light',
  'print.themeDark': 'Dark',
  'print.action': 'Print or save as PDF',
  'discovery.builds.tags.pvp_group.label': 'PvP Group',
  'discovery.builds.tags.heavy.label': 'Heavy',
}

function t(key, params = {}) {
  const template = translations[key] || key
  return Object.entries(params).reduce((acc, [name, value]) => acc.replaceAll(`{${name}}`, value), template)
}

const build = {
  id: 42,
  build_name: 'Leopard Event Build',
  build_type: 'balanced',
  sails: 'Raiding Sails',
  lantern: 'Ice Lantern',
  research_upgrade_slot_unlocked: true,
  sailors: 80,
  musketeers: 10,
  soldiers: 30,
  mercenaries: 5,
  upgrade_1: 'Copper Sheathing',
  upgrade_2: 'Trim',
  ship: {
    name: 'Leopard',
    rate: 'III',
    ship_type: 'Medium',
    crew_capacity: 160,
    sailor_minimum: 80,
  },
  ship_stats: {
    crew_total: 125,
    crew_capacity: 160,
    crew_remaining: 35,
    weapon_total: 29,
    weapon_capacity_total: 29,
    upgrade_slots_available: 5,
    sailor_minimum: 80,
    stat_rows: [
      { key: 'durability', base: 2040, effective: 2142, modifier: 5, modifier_kind: 'percent', precision: 0 },
      { key: 'speed_knots', base: 9.6, effective: 10.1, modifier: 5, modifier_kind: 'percent', precision: 1 },
      { key: 'maneuverability', base: 72, effective: 78, modifier: 8, modifier_kind: 'percent', precision: 0 },
      { key: 'armor', base: 18, effective: 20, modifier: 2, modifier_kind: 'flat', precision: 1 },
      { key: 'hold_capacity', base: 650, effective: 650, modifier: 0, modifier_kind: 'flat', precision: 0 },
      { key: 'crew_capacity', base: 160, effective: 170, modifier: 10, modifier_kind: 'flat', precision: 0 },
      { key: 'sailor_minimum', base: 80, effective: 76, modifier: -5, modifier_kind: 'percent', precision: 0 },
      { key: 'displacement_tons', base: 780, effective: 780, modifier: 0, modifier_kind: 'flat', precision: 0, unit: 't' },
    ],
  },
  front_weapon_slots: [{ item: 'Bow Chaser', quantity: 2 }],
  port_weapon_slots: [{ item: 'Long 18-pdr', quantity: 12 }],
  starboard_weapon_slots: [{ item: 'Long 18-pdr', quantity: 12 }],
  rear_weapon_slots: [{ item: 'Stern Chaser', quantity: 3 }],
  special_crew_slots: [{ item: 'Doctor', quantity: 1 }],
  ammunition_slots: [{ item: 'Round Shot', quantity: 200 }],
  consumable_slots: [{ item: 'Repair Kit', quantity: 3 }],
  hold_slots: [{ item: 'Oak Logs', quantity: 50 }],
  details: 'Prepared for the current event and tuned for speed with a balanced broadside.',
}

test('build print model exposes export-ready sections', () => {
  const model = createBuildPrintModel(build, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.equal(model.buildName, 'Leopard Event Build')
  assert.equal(model.shipName, 'Leopard')
  assert.equal(model.shareUrl, 'https://fleet.example/builds/42')
  assert.deepEqual(model.upgrades, ['Copper Sheathing', 'Trim'])
  assert.equal(model.weapons[1].lines[0], 'Long 18-pdr ×12')
  assert.equal(model.inventoryGroups[0].title, 'Ammunition')
  assert.deepEqual(model.inventoryGroups[0].lines, ['Round Shot ×200'])
  assert.deepEqual(model.inventoryGroups[1].lines, ['Repair Kit'])
  assert.deepEqual(model.inventoryGroups[2].lines, ['Oak Logs ×50'])
})

test('build print svg contains the key build identifiers', () => {
  const svg = createBuildPrintSvg(build, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.match(svg, /Leopard Event Build/)
  assert.match(svg, /https:\/\/fleet\.example\/builds\/42/)
  assert.match(svg, /Weapon loadout/)
  assert.match(svg, /Copper Sheathing/)
  assert.match(svg, /data-build-sheet-version="3"/)
  assert.match(svg, /data-build-sheet-theme="dark"/)
  assert.match(svg, /data-build-performance-panel="true"/)
  assert.match(svg, /data-performance-stat="maneuverability"/)
  assert.match(svg, /data-performance-stat="sailor_minimum"/)
  assert.match(svg, />\+8%<\/text>/)
})

test('build print inventory renders each entry vertically and hides consumable quantities', () => {
  const inventoryBuild = {
    ...build,
    ammunition_slots: [
      { item: 'Round Shot', quantity: 200 },
      { item: 'Chain Shot', quantity: 120 },
    ],
    consumable_slots: [
      { item: 'Repair Kit', quantity: 3 },
      { item: 'Rum Ration', quantity: 5 },
    ],
  }
  const svg = createBuildPrintSvg(inventoryBuild, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })

  assert.match(svg, /data-build-inventory-panel="true"/)
  assert.match(svg, /data-inventory-item="ammunition-1"/)
  assert.match(svg, /data-inventory-item="ammunition-2"/)
  assert.match(svg, />Round Shot ×200<\/text>/)
  assert.match(svg, />Chain Shot ×120<\/text>/)
  assert.match(svg, />Repair Kit<\/text>/)
  assert.match(svg, />Rum Ration<\/text>/)
  assert.doesNotMatch(svg, /Repair Kit ×3/)
  assert.doesNotMatch(svg, /Rum Ration ×5/)
  assert.doesNotMatch(svg, /Round Shot ×200 · Chain Shot ×120/)
})

test('build print uses the shared themed document shell', async () => {
  const lightSvg = createBuildPrintDocument(build, { t, optionLabel: (value) => value, theme: 'light' }).svg
  const html = await createBuildPrintHtml(build, { t, optionLabel: (value) => value })

  assert.match(lightSvg, /data-build-sheet-theme="light"/)
  assert.match(lightSvg, /#f8fafc/)
  assert.match(html, /class="print-toolbar"/)
  assert.match(html, /data-build-print-theme="light"/)
  assert.match(html, /data-build-print-theme="dark"/)
  assert.match(html, /Print or save as PDF/)
})

test('build print file names are sanitized for downloads', () => {
  assert.equal(buildPrintFileName({ build_name: 'Santisima Trinidad #1' }, 'png'), 'santisima-trinidad-1-build-sheet.png')
})


test('build print omits unselected optional sections and values', () => {
  const sparseBuild = {
    ...build,
    sails: null,
    lantern: null,
    research_upgrade_slot_unlocked: false,
    upgrade_1: null,
    upgrade_2: null,
    special_crew_slots: [],
    ammunition_slots: [],
    consumable_slots: [],
    hold_slots: [],
    front_weapon_slots: [],
    rear_weapon_slots: [],
    port_weapon_slots: [],
    starboard_weapon_slots: [],
    mortar_weapon_slots: [],
    special_weapon_slots: [],
    musketeers: 0,
    soldiers: 0,
    mercenaries: 0,
    details: '',
  }
  const model = createBuildPrintModel(sparseBuild, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.deepEqual(model.equipmentRows, [])
  assert.deepEqual(model.upgrades, [])
  assert.deepEqual(model.weapons, [])
  assert.deepEqual(model.inventoryGroups, [])
  assert.deepEqual(model.notes, [])
  assert.equal(model.crewRows.length, 1)

  const svg = createBuildPrintSvg(sparseBuild, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.doesNotMatch(svg, /Configuration snapshot/)
  assert.doesNotMatch(svg, /Weapon loadout/)
  assert.doesNotMatch(svg, /Ammunition and hold/)
  assert.doesNotMatch(svg, /Captain notes/)
  assert.doesNotMatch(svg, /Research slot/)
})


test('build print renders the complete long captain note without truncation', () => {
  const finalToken = 'FINAL-AUDIT-NOTE-TOKEN'
  const longDetails = `${'A detailed captain note with operational context. '.repeat(55)}${finalToken}`
  const svg = createBuildPrintSvg({ ...build, details: longDetails }, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.match(svg, new RegExp(finalToken))
})

test('build print preserves four regular specialists plus Ginger as an extra slot', () => {
  const specialistBuild = {
    ...build,
    classification_tags: ['pvp_group', 'heavy'],
    special_crew_slots: [
      { item: 'Doctor', quantity: 1 },
      { item: 'Gunner', quantity: 1 },
      { item: 'Navigator', quantity: 1 },
      { item: 'Carpenter', quantity: 1 },
      { item: 'Ginger', quantity: 1 },
    ],
  }
  const model = createBuildPrintModel(specialistBuild, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.equal(model.specialists.length, 4)
  assert.equal(model.gingerSpecialist, 'Ginger')
  assert.deepEqual(model.classificationLabels, ['PvP Group', 'Heavy'])

  const svg = createBuildPrintSvg(specialistBuild, { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } })
  assert.match(svg, /\+1 · Ginger/)
  assert.match(svg, /PVP GROUP\s+·\s+HEAVY/)
})

test('build print renders catalog icons for selected equipment, upgrades, and specialists', () => {
  const iconUrl = (category, name) => `/icons/${category}/${encodeURIComponent(name)}.png`
  const iconBuild = {
    ...build,
    special_crew_slots: [{ item: 'Doctor', quantity: 1 }],
  }
  const svg = createBuildPrintSvg(iconBuild, {
    t,
    optionLabel: (value) => value,
    optionImage: iconUrl,
    locationObject: { origin: 'https://fleet.example' },
  })

  assert.match(svg, /https:\/\/fleet\.example\/icons\/sail\/Raiding%20Sails\.png/)
  assert.match(svg, /https:\/\/fleet\.example\/icons\/lantern\/Ice%20Lantern\.png/)
  assert.match(svg, /https:\/\/fleet\.example\/icons\/upgrade\/Copper%20Sheathing\.png/)
  assert.match(svg, /https:\/\/fleet\.example\/icons\/upgrade\/Trim\.png/)
  assert.match(svg, /https:\/\/fleet\.example\/icons\/special_crew\/Doctor\.png/)
  assert.match(svg, /https:\/\/fleet\.example\/icons\/consumable\/Repair%20Kit\.png/)
  assert.doesNotMatch(svg, /href="\/icons\//)
})


test('build print embeds catalog images so SVG image mode does not need external requests', async () => {
  const requested = []
  const document = await createEmbeddedBuildPrintDocument(build, {
    t,
    optionLabel: (value) => value,
    optionImage: (category, name) => `/icons/${category}/${encodeURIComponent(name)}.png`,
    locationObject: { origin: 'https://fleet.example' },
    fetchImpl: async (url) => {
      requested.push(url)
      return {
        ok: true,
        status: 200,
        headers: { get: () => 'image/png' },
        blob: async () => new Blob([new Uint8Array([137, 80, 78, 71])], { type: 'image/png' }),
      }
    },
  })

  assert.ok(requested.some((url) => url.includes('/icons/upgrade/Copper%20Sheathing.png')))
  assert.ok(document.svg.includes(`href="${['data:image/png', 'base64,iVBORw=='].join(';')}"`))
  assert.doesNotMatch(document.svg, /href="https:\/\/fleet\.example\/icons\//)
})

test('build print binds the browser fetch function before embedding catalog images', async () => {
  const originalFetch = globalThis.fetch
  const requested = []
  globalThis.fetch = async function fetchWithRequiredReceiver(url) {
    assert.equal(this, globalThis)
    requested.push(url)
    return {
      ok: true,
      status: 200,
      headers: { get: () => 'image/png' },
      blob: async () => new Blob([new Uint8Array([137, 80, 78, 71])], { type: 'image/png' }),
    }
  }

  try {
    const document = await createEmbeddedBuildPrintDocument(build, {
      t,
      optionLabel: (value) => value,
      optionImage: (category, name) => `/icons/${category}/${encodeURIComponent(name)}.png`,
      locationObject: { origin: 'https://fleet.example' },
    })
    assert.ok(requested.length > 0)
    assert.ok(document.svg.includes(`href="${['data:image/png', 'base64,iVBORw=='].join(';')}"`))
    assert.doesNotMatch(document.svg, /href="https:\/\/fleet\.example\/icons\//)
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('build print falls back to same-origin image rasterization when fetch conversion fails', async () => {
  class FakeImage {
    naturalWidth = 96
    naturalHeight = 96
    complete = false
    set src(value) {
      this._src = value
      this.complete = true
      queueMicrotask(() => this.onload?.())
    }
  }
  const drawCalls = []
  const documentObject = {
    createElement(tagName) {
      assert.equal(tagName, 'canvas')
      return {
        width: 0,
        height: 0,
        getContext: () => ({ drawImage: (...args) => drawCalls.push(args) }),
        toDataURL: () => ['data:image/png', 'base64,RkFMTEJBQ0s='].join(';'),
      }
    },
  }

  const document = await createEmbeddedBuildPrintDocument(build, {
    t,
    optionLabel: (value) => value,
    optionImage: (category, name) => `/icons/${category}/${encodeURIComponent(name)}.png`,
    locationObject: { origin: 'https://fleet.example' },
    fetchImpl: async () => { throw new TypeError('Illegal invocation') },
    ImageImpl: FakeImage,
    documentObject,
  })

  assert.ok(drawCalls.length > 0)
  assert.ok(document.svg.includes(`href="${['data:image/png', 'base64,RkFMTEJBQ0s='].join(';')}"`))
  assert.doesNotMatch(document.svg, /href="https:\/\/fleet\.example\/icons\//)
})


test('build print embedding uses HTTP cache and bounds parallel image fetches', async () => {
  let active = 0
  let peakActive = 0
  const requested = []
  const hrefs = Array.from({ length: 24 }, (_, index) => `https://fleet.example/api/files/${index + 1}/content`)
  const svg = `<svg>${hrefs.map((href) => `<image href="${href}" />`).join('')}</svg>`

  const embedded = await inlinePrintImageResources(svg, {
    fetchImpl: async (url, options) => {
      assert.equal(options.cache, 'force-cache')
      assert.equal(options.credentials, 'same-origin')
      assert.equal(options.mode, 'same-origin')
      requested.push(url)
      active += 1
      peakActive = Math.max(peakActive, active)
      await new Promise((resolve) => setTimeout(resolve, 2))
      active -= 1
      return {
        ok: true,
        status: 200,
        blob: async () => new Blob([new Uint8Array([137, 80, 78, 71])], { type: 'image/png' }),
      }
    },
  })

  assert.equal(requested.length, hrefs.length)
  assert.ok(peakActive <= 6, `expected at most 6 concurrent fetches, got ${peakActive}`)
  assert.doesNotMatch(embedded, /href="https:\/\/fleet\.example\/api\/files\//)
})

test('build print embedding reuses a supplied resource cache across renders', async () => {
  const cache = new Map()
  let requests = 0
  const svg = '<svg><image href="https://fleet.example/api/files/7/content" /></svg>'
  const options = {
    cache,
    fetchImpl: async () => {
      requests += 1
      return {
        ok: true,
        status: 200,
        blob: async () => new Blob([new Uint8Array([137, 80, 78, 71])], { type: 'image/png' }),
      }
    },
  }

  await inlinePrintImageResources(svg, options)
  await inlinePrintImageResources(svg, options)
  assert.equal(requests, 1)
})


test('build print cache descriptor is stable for the same rendered build version', async () => {
  const current = { ...build, updated_at: '2026-08-08T10:00:00' }
  const helpers = { t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' } }
  const first = await createBuildPrintCacheDescriptor(current, helpers)
  const second = await createBuildPrintCacheDescriptor({ ...current }, helpers)

  assert.equal(BUILD_PRINT_RENDERER_VERSION, '3')
  assert.equal(first.sourceUpdatedAt, current.updated_at)
  assert.equal(first.cacheKey, second.cacheKey)
  assert.match(first.cacheKey, /^print-v3:[a-f0-9]{64}$/)
})

test('build print cache descriptor changes with build content or rendered language', async () => {
  const current = { ...build, updated_at: '2026-08-08T10:00:00' }
  const english = await createBuildPrintCacheDescriptor(current, {
    t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' },
  })
  const changedBuild = await createBuildPrintCacheDescriptor({ ...current, sailors: 81 }, {
    t, optionLabel: (value) => value, locationObject: { origin: 'https://fleet.example' },
  })
  const localized = await createBuildPrintCacheDescriptor(current, {
    t: (key, params = {}) => `DE:${t(key, params)}`,
    optionLabel: (value) => `DE:${value}`,
    locationObject: { origin: 'https://fleet.example' },
  })

  assert.notEqual(english.cacheKey, changedBuild.cacheKey)
  assert.notEqual(english.cacheKey, localized.cacheKey)
})


test('server-wide build print cache fetch uses the versioned URL and browser cache', async () => {
  const calls = []
  const url = 'https://fleet.example/api/builds/42/printout?cache_key=print-v3%3Aabc'
  const blob = new Blob([new Uint8Array([137, 80, 78, 71])], { type: 'image/png' })
  const result = await fetchBuildPrintPngBlob(url, async (requestedUrl, options) => {
    calls.push({ requestedUrl, options })
    return { ok: true, status: 200, blob: async () => blob }
  })

  assert.equal(result, blob)
  assert.deepEqual(calls, [{
    requestedUrl: url,
    options: { credentials: 'include', cache: 'force-cache' },
  }])
})
