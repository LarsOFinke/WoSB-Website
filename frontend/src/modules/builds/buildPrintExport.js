import { buildCrewVisualUrl, buildVisualUrl } from './buildVisuals.js'
import { buildShareUrl } from './shareBuild.js'
import {
  CORE_BUILD_STAT_KEYS,
  formatBuildModifier,
  formatStatValue,
  roundByPrecision,
} from './domain/buildStatPresentation.js'
import {
  createPrintDocumentHtml,
  createPrintLabels,
  escapePrintMarkup,
  resolvePrintUrl,
  sanitizePrintFileName,
  triggerPrintDownload,
} from '../../shared/printing/printDocument.js'

const PAGE_WIDTH = 1400
const BASE_PAGE_HEIGHT = 1980
const PAGE_PADDING = 46
const CONTENT_WIDTH = PAGE_WIDTH - (PAGE_PADDING * 2)
const COLUMN_GAP = 22
const COLUMN_WIDTH = (CONTENT_WIDTH - COLUMN_GAP) / 2
const SECTION_GAP = 22
const FOOTER_HEIGHT = 86

const BUILD_PRINT_THEMES = Object.freeze({
  dark: Object.freeze({
    page: '#07111a', panel: '#0d1a26', panelSoft: '#112231', border: '#263847',
    borderStrong: '#8f713f', text: '#f4f7fa', muted: '#9babb9', faint: '#647889',
    accent: '#e8be70', accentSoft: '#2c281f', danger: '#d88980',
  }),
  light: Object.freeze({
    page: '#f8fafc', panel: '#ffffff', panelSoft: '#f1f4f7', border: '#c7d0d9',
    borderStrong: '#a87516', text: '#10243d', muted: '#526170', faint: '#748391',
    accent: '#94620b', accentSoft: '#fbf4e5', danger: '#a6413a',
  }),
})

const PRINT_VISUALS = {
  ship: buildVisualUrl('ship'),
  sail: buildVisualUrl('sail'),
  lantern: buildVisualUrl('lantern'),
  upgrade: buildVisualUrl('upgrade'),
  weapon: buildVisualUrl('weapon'),
  specialist: buildVisualUrl('specialist'),
  ammunition: buildVisualUrl('ammunition'),
  consumable: buildVisualUrl('consumable'),
  hold: buildVisualUrl('hold'),
  notes: buildVisualUrl('specialist'),
  crew: {
    sailors: buildCrewVisualUrl('sailors'),
    musketeers: buildCrewVisualUrl('musketeers'),
    soldiers: buildCrewVisualUrl('soldiers'),
    mercenaries: buildCrewVisualUrl('mercenaries'),
  },
}

const escapeXml = escapePrintMarkup


function xmlAttributeValue(value) {
  return String(value || '')
    .replaceAll('&amp;', '&')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'")
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunkSize = 0x8000
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize))
  }
  return btoa(binary)
}

function blobToDataUrl(blob) {
  if (typeof FileReader === 'function') {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result || ''))
      reader.onerror = () => reject(reader.error || new Error('Print image could not be read.'))
      reader.readAsDataURL(blob)
    })
  }
  return blob.arrayBuffer().then((buffer) => {
    const mimeType = String(blob.type || 'application/octet-stream').split(';')[0].trim() || 'application/octet-stream'
    return `data:${mimeType};${'base64,'}${arrayBufferToBase64(buffer)}`
  })
}

async function fetchPrintImageDataUrl(url, fetchImpl) {
  const response = await fetchImpl(url, {
    credentials: 'same-origin',
    cache: 'no-store',
    mode: 'same-origin',
  })
  if (!response?.ok) throw new Error(`Print image request failed (${response?.status || 'network'}): ${url}`)
  const blob = await response.blob()
  if (!blob?.size) throw new Error(`Print image response was empty: ${url}`)
  return blobToDataUrl(blob)
}

function loadHtmlImage(url, ImageImpl) {
  return new Promise((resolve, reject) => {
    const image = new ImageImpl()
    let settled = false
    const finish = (callback, value) => {
      if (settled) return
      settled = true
      image.onload = null
      image.onerror = null
      callback(value)
    }
    image.onload = () => finish(resolve, image)
    image.onerror = () => finish(reject, new Error(`Print image element failed to load: ${url}`))
    image.decoding = 'async'
    image.src = url
    if (image.complete && image.naturalWidth > 0) finish(resolve, image)
  })
}

async function rasterizePrintImageDataUrl(url, { ImageImpl = globalThis.Image, documentObject = globalThis.document } = {}) {
  if (typeof ImageImpl !== 'function' || !documentObject?.createElement) {
    throw new Error('Print image raster fallback is unavailable.')
  }
  const image = await loadHtmlImage(url, ImageImpl)
  const width = Math.max(1, Number(image.naturalWidth || image.width || 96))
  const height = Math.max(1, Number(image.naturalHeight || image.height || 96))
  const canvas = documentObject.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext?.('2d')
  if (!context) throw new Error('Print image raster fallback has no canvas context.')
  context.drawImage(image, 0, 0, width, height)
  const dataUrl = canvas.toDataURL?.('image/png') || ''
  if (!dataUrl.startsWith('data:image/')) throw new Error('Print image raster fallback could not encode the image.')
  return dataUrl
}

async function resolvePrintImageDataUrl(url, options = {}) {
  const errors = []
  if (typeof options.fetchImpl === 'function') {
    try {
      return await fetchPrintImageDataUrl(url, options.fetchImpl)
    } catch (error) {
      errors.push(error)
    }
  }
  try {
    return await rasterizePrintImageDataUrl(url, options)
  } catch (error) {
    errors.push(error)
  }
  const error = new Error(`Print image could not be embedded: ${url}`)
  error.causes = errors
  throw error
}

async function inlinePrintImageResources(svg, {
  fetchImpl = typeof globalThis.fetch === 'function' ? globalThis.fetch.bind(globalThis) : null,
  ImageImpl = globalThis.Image,
  documentObject = globalThis.document,
  cache = new Map(),
} = {}) {
  const hrefs = [...String(svg || '').matchAll(/\bhref="([^"]+)"/g)]
    .map((match) => match[1])
    .filter((href, index, values) => values.indexOf(href) === index)
  const externalHrefs = hrefs.filter((href) => /^https?:\/\//i.test(xmlAttributeValue(href)))
  if (!externalHrefs.length) return svg

  const replacements = new Map()
  const failures = []
  await Promise.all(externalHrefs.map(async (escapedHref) => {
    const href = xmlAttributeValue(escapedHref)
    let task = cache.get(href)
    if (!task) {
      task = resolvePrintImageDataUrl(href, { fetchImpl, ImageImpl, documentObject })
      cache.set(href, task)
    }
    try {
      replacements.set(escapedHref, await task)
    } catch (error) {
      cache.delete(href)
      failures.push({ href, error })
    }
  }))

  if (failures.length) {
    const failedUrls = failures.map(({ href }) => href).join(', ')
    console.error('Build print image embedding failed.', failures)
    throw new Error(`Build print image embedding failed for: ${failedUrls}`)
  }

  return externalHrefs.reduce(
    (result, escapedHref) => result.replaceAll(`href="${escapedHref}"`, `href="${replacements.get(escapedHref)}"`),
    svg,
  )
}

function listLabel(slot, labeler, { includeQuantity = true } = {}) {
  if (!slot) return ''
  if (typeof slot === 'string') return labeler(slot)
  if (!slot.item) return ''
  const quantity = Number(slot.quantity || 1)
  return `${labeler(slot.item)}${includeQuantity && quantity > 1 ? ` ×${quantity}` : ''}`
}

function cleanLines(items, limit = Infinity) {
  const lines = (items || []).map((item) => String(item || '').trim()).filter(Boolean)
  if (lines.length <= limit) return lines
  return [...lines.slice(0, Math.max(0, limit - 1)), `+${lines.length - (limit - 1)} more`]
}

function cleanEntries(items, limit = Infinity) {
  const entries = (items || []).filter((item) => item && String(item.value || '').trim())
  if (entries.length <= limit) return entries
  return [
    ...entries.slice(0, Math.max(0, limit - 1)),
    { name: '', value: `+${entries.length - (limit - 1)} more`, iconHref: '' },
  ]
}

function rawSlotItem(slot) {
  if (!slot) return ''
  return typeof slot === 'string' ? slot : String(slot.item || '')
}

function wrapText(text, maxChars = 58) {
  const paragraphs = String(text || '').replace(/\r/g, '').split('\n')
  const lines = []
  for (const paragraph of paragraphs) {
    const normalized = paragraph.replace(/\s+/g, ' ').trim()
    if (!normalized) {
      if (lines.length && lines.at(-1) !== '') lines.push('')
      continue
    }
    let current = ''
    for (const word of normalized.split(' ')) {
      const next = current ? `${current} ${word}` : word
      if (next.length <= maxChars) {
        current = next
        continue
      }
      if (current) lines.push(current)
      if (word.length <= maxChars) {
        current = word
        continue
      }
      let rest = word
      while (rest.length > maxChars) {
        lines.push(`${rest.slice(0, maxChars - 1)}…`)
        rest = rest.slice(maxChars - 1)
      }
      current = rest
    }
    if (current) lines.push(current)
  }
  while (lines.at(-1) === '') lines.pop()
  return lines
}

function renderIcon(href, x, y, size = 38, accented = false, colors = BUILD_PRINT_THEMES.dark) {
  if (!href) return ''
  return `<g>
    <rect x="${x}" y="${y}" width="${size}" height="${size}" rx="5" fill="${accented ? colors.accentSoft : colors.panelSoft}" stroke="${accented ? colors.borderStrong : colors.border}" />
    <image href="${escapeXml(href)}" x="${x + 3}" y="${y + 3}" width="${size - 6}" height="${size - 6}" preserveAspectRatio="xMidYMid meet" />
  </g>`
}

function renderSectionHeader(x, y, width, index, eyebrow, title, iconHref, colors) {
  return `<g>
    <rect x="${x}" y="${y}" width="${width}" height="76" fill="${colors.panelSoft}" />
    <circle cx="${x + 34}" cy="${y + 38}" r="16" fill="none" stroke="${colors.borderStrong}" />
    <text x="${x + 34}" y="${y + 43}" text-anchor="middle" class="index">${String(index).padStart(2, '0')}</text>
    ${renderIcon(iconHref, x + width - 58, y + 19, 38, true, colors)}
    <text x="${x + 62}" y="${y + 27}" class="eyebrow">${escapeXml(String(eyebrow || '').toUpperCase())}</text>
    <text x="${x + 62}" y="${y + 55}" class="section-title">${escapeXml(title)}</text>
  </g>`
}

function renderRowsPanel({ x, y, width, index, eyebrow, title, iconHref, rows, accentLast = false, colors }) {
  const rowHeight = 62
  const height = 76 + (rows.length * rowHeight) + 12
  const rowSvg = rows.map((row, rowIndex) => {
    const rowY = y + 76 + (rowIndex * rowHeight)
    const accented = Boolean(row.accent || (accentLast && rowIndex === rows.length - 1))
    return `<g>
      ${rowIndex ? `<line x1="${x + 18}" y1="${rowY}" x2="${x + width - 18}" y2="${rowY}" stroke="${colors.border}" />` : ''}
      ${accented ? `<rect x="${x + 10}" y="${rowY + 6}" width="${width - 20}" height="${rowHeight - 10}" rx="5" fill="${colors.accentSoft}" stroke="${colors.borderStrong}" stroke-dasharray="5 5" />` : ''}
      ${renderIcon(row.iconHref, x + 20, rowY + 12, 38, accented, colors)}
      <text x="${x + 72}" y="${rowY + 26}" class="row-label" fill="${accented ? colors.accent : colors.muted}">${escapeXml(row.label)}</text>
      <text x="${x + 72}" y="${rowY + 48}" class="row-value">${escapeXml(row.value)}</text>
      ${row.meta ? `<text x="${x + width - 20}" y="${rowY + 38}" text-anchor="end" class="row-meta">${escapeXml(row.meta)}</text>` : ''}
    </g>`
  }).join('')
  return {
    height,
    svg: `<g><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="7" fill="${colors.panel}" stroke="${colors.border}" />${renderSectionHeader(x, y, width, index, eyebrow, title, iconHref, colors)}${rowSvg}</g>`,
  }
}

function renderGroupedPanel({ x, y, width, index, eyebrow, title, iconHref, groups, colors }) {
  const normalizedGroups = groups.map((group) => ({ ...group, wrapped: wrapText(group.lines.join(' · '), 49) }))
  const groupHeights = normalizedGroups.map((group) => 48 + (Math.max(1, group.wrapped.length) * 23))
  const height = 76 + groupHeights.reduce((total, value) => total + value, 0) + 12
  let cursorY = y + 76
  const groupsSvg = normalizedGroups.map((group, groupIndex) => {
    const groupY = cursorY
    cursorY += groupHeights[groupIndex]
    const lines = group.wrapped.length ? group.wrapped : ['—']
    return `<g>
      ${groupIndex ? `<line x1="${x + 18}" y1="${groupY}" x2="${x + width - 18}" y2="${groupY}" stroke="${colors.border}" />` : ''}
      ${renderIcon(group.iconHref, x + 20, groupY + 14, 34, false, colors)}
      <text x="${x + 66}" y="${groupY + 28}" class="row-label">${escapeXml(group.label)}</text>
      ${lines.map((line, lineIndex) => `<text x="${x + 66}" y="${groupY + 52 + (lineIndex * 23)}" class="group-line">${escapeXml(line)}</text>`).join('')}
    </g>`
  }).join('')
  return {
    height,
    svg: `<g><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="7" fill="${colors.panel}" stroke="${colors.border}" />${renderSectionHeader(x, y, width, index, eyebrow, title, iconHref, colors)}${groupsSvg}</g>`,
  }
}

function renderPerformancePanel({ x, y, width, index, eyebrow, title, iconHref, rows, colors }) {
  if (!rows.length) return { height: 0, svg: '' }
  const columns = 3
  const cellGap = 10
  const cellHeight = 92
  const gridPadding = 14
  const cellWidth = (width - (gridPadding * 2) - (cellGap * (columns - 1))) / columns
  const rowCount = Math.ceil(rows.length / columns)
  const height = 76 + (gridPadding * 2) + (rowCount * cellHeight) + ((rowCount - 1) * cellGap)
  const cells = rows.map((row, rowIndex) => {
    const column = rowIndex % columns
    const gridRow = Math.floor(rowIndex / columns)
    const cellX = x + gridPadding + (column * (cellWidth + cellGap))
    const cellY = y + 76 + gridPadding + (gridRow * (cellHeight + cellGap))
    const modifier = formatBuildModifier(row)
    const modified = Boolean(modifier)
    const debuff = Boolean(row.isDebuff ?? row.is_debuff)
    const statusColor = debuff ? colors.danger : colors.accent
    const baseValue = formatStatValue(row.base, row.unit, row.precision)
    return `<g data-performance-stat="${escapeXml(row.key)}">
      <rect x="${cellX}" y="${cellY}" width="${cellWidth}" height="${cellHeight}" rx="5" fill="${colors.panelSoft}" stroke="${modified ? statusColor : colors.border}" />
      <text x="${cellX + 16}" y="${cellY + 24}" class="performance-label">${escapeXml(row.label)}</text>
      <text x="${cellX + 16}" y="${cellY + 61}" class="performance-value">${escapeXml(formatStatValue(row.effective, row.unit, row.precision))}</text>
      <text x="${cellX + cellWidth - 16}" y="${cellY + 59}" text-anchor="end" class="performance-base">${escapeXml(baseValue)}</text>
      ${modified ? `<text x="${cellX + cellWidth - 16}" y="${cellY + 79}" text-anchor="end" class="performance-modifier" fill="${statusColor}">${escapeXml(modifier)}</text>` : ''}
      <line x1="${cellX + 16}" y1="${cellY + 78}" x2="${cellX + (modified ? 80 : cellWidth - 16)}" y2="${cellY + 78}" stroke="${modified ? statusColor : colors.border}" />
    </g>`
  }).join('')
  return {
    height,
    svg: `<g data-build-performance-panel="true"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="7" fill="${colors.panel}" stroke="${colors.border}" />${renderSectionHeader(x, y, width, index, eyebrow, title, iconHref, colors)}${cells}</g>`,
  }
}

function renderInventoryPanel({ x, y, width, index, eyebrow, title, iconHref, groups, colors }) {
  const normalizedGroups = groups.map((group) => ({
    ...group,
    items: (group.items || group.lines.map((value) => ({ value, iconHref: group.iconHref }))).map((item) => ({
      ...item,
      wrapped: wrapText(item.value, 38),
    })),
  }))
  const itemHeight = (item) => Math.max(42, 18 + (Math.max(1, item.wrapped.length) * 22))
  const groupHeights = normalizedGroups.map((group) => 52 + group.items.reduce((total, item) => total + itemHeight(item) + 6, 0))
  const height = 76 + groupHeights.reduce((total, value) => total + value, 0) + 12
  let cursorY = y + 76
  const groupsSvg = normalizedGroups.map((group, groupIndex) => {
    const groupY = cursorY
    cursorY += groupHeights[groupIndex]
    let itemY = groupY + 48
    const items = group.items.map((item, itemIndex) => {
      const rowHeight = itemHeight(item)
      const rowY = itemY
      itemY += rowHeight + 6
      const visibleLines = item.wrapped.length ? item.wrapped : ['—']
      return `<g data-inventory-item="${escapeXml(group.iconKey || group.label)}-${itemIndex + 1}">
        <rect x="${x + 64}" y="${rowY}" width="${width - 84}" height="${rowHeight}" rx="4" fill="${colors.panelSoft}" stroke="${colors.border}" />
        ${renderIcon(item.iconHref || group.iconHref, x + 72, rowY + 6, 30, false, colors)}
        ${visibleLines.map((line, lineIndex) => `<text x="${x + 116}" y="${rowY + 25 + (lineIndex * 22)}" class="group-line">${escapeXml(line)}</text>`).join('')}
        <text x="${x + width - 24}" y="${rowY + 25}" text-anchor="end" class="inventory-index">${String(itemIndex + 1).padStart(2, '0')}</text>
      </g>`
    }).join('')
    return `<g>
      ${groupIndex ? `<line x1="${x + 18}" y1="${groupY}" x2="${x + width - 18}" y2="${groupY}" stroke="${colors.border}" />` : ''}
      ${renderIcon(group.iconHref, x + 20, groupY + 8, 34, false, colors)}
      <text x="${x + 66}" y="${groupY + 30}" class="row-label">${escapeXml(group.label)}</text>
      ${items}
    </g>`
  }).join('')
  return {
    height,
    svg: `<g data-build-inventory-panel="true"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="7" fill="${colors.panel}" stroke="${colors.border}" />${renderSectionHeader(x, y, width, index, eyebrow, title, iconHref, colors)}${groupsSvg}</g>`,
  }
}

function renderNotesPanel(model, x, y, width, index, colors) {
  const lineHeight = 25
  const height = 102 + (model.notes.length * lineHeight) + 22
  return {
    height,
    svg: `<g>
      <rect x="${x}" y="${y}" width="${width}" height="${height}" rx="7" fill="${colors.panel}" stroke="${colors.border}" />
      ${renderSectionHeader(x, y, width, index, model.t('builds.detail.details'), model.t('builds.print.notesTitle'), PRINT_VISUALS.notes, colors)}
      ${model.notes.map((line, lineIndex) => `<text x="${x + 22}" y="${y + 108 + (lineIndex * lineHeight)}" class="note-line">${escapeXml(line || ' ')}</text>`).join('')}
    </g>`,
  }
}

function statRowsForBuild(build, t) {
  return (build?.ship_stats?.stat_rows || [])
    .filter((row) => CORE_BUILD_STAT_KEYS.has(row.key))
    .map((row) => {
      const path = `builds.statLabels.${row.key}`
      const translated = t(path)
      return { ...row, label: translated === path ? (row.label || String(row.key).replaceAll('_', ' ')) : translated }
    })
}

function buildTypeLabel(buildType, t) {
  return t(`builds.types.${buildType || 'balanced'}`)
}

function makeSummaryCards(build, t) {
  const stats = build?.ship_stats || {}
  const crewCapacity = stats.crew_capacity || build?.ship?.crew_capacity || 0
  const crewTotal = stats.crew_total || 0
  const upgrades = [build?.upgrade_1, build?.upgrade_2, build?.upgrade_3, build?.upgrade_4, build?.upgrade_5, build?.upgrade_6, build?.upgrade_7, build?.upgrade_8].filter(Boolean)
  return [
    { label: t('builds.detail.buildType'), value: buildTypeLabel(build?.build_type, t), detail: `${t('common.rate')} ${build?.ship?.rate || '—'}` },
    { label: t('builds.detail.shipStats'), value: `${stats.weapon_total || 0}`, detail: t('builds.detail.weaponCapacity', { count: stats.weapon_capacity_total || 0 }) },
    { label: t('builds.detail.crewDistribution'), value: `${crewTotal}/${crewCapacity}`, detail: t('builds.commandDeck.crewRemaining', { value: stats.crew_remaining || 0 }) },
    { label: t('builds.detail.upgrades'), value: `${upgrades.length}`, detail: t('builds.list.upgradeSummary', { used: upgrades.length, max: stats.upgrade_slots_available || 0 }) },
  ]
}

function headlineStatsForBuild(build, statRows, t) {
  const byKey = new Map(statRows.map((row) => [row.key, row]))
  const statCard = (keys, fallbackLabel) => {
    const row = keys.map((key) => byKey.get(key)).find(Boolean)
    return { label: row?.label || fallbackLabel, value: row ? formatStatValue(row.effective, row.unit, row.precision) : '—' }
  }
  const stats = build?.ship_stats || {}
  return [
    statCard(['speed_knots', 'speed_min_knots'], t('builds.statLabels.speed_knots')),
    statCard(['durability'], t('builds.statLabels.durability')),
    statCard(['armor'], t('builds.statLabels.armor')),
    { label: t('builds.detail.crewDistribution'), value: `${stats.crew_total || 0}/${stats.crew_capacity || build?.ship?.crew_capacity || 0}` },
    statCard(['hold_capacity'], t('builds.detail.hold')),
  ]
}

function createBuildPrintModel(build, helpers = {}) {
  const t = helpers.t || ((key, params = {}) => Object.entries(params || {}).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, value), key))
  const optionLabel = helpers.optionLabel || ((value) => value || '')
  const locationObject = helpers.locationObject || globalThis.location
  const rawOptionImage = helpers.optionImage || (() => '')
  const optionImage = (categoryKey, name) => resolvePrintUrl(rawOptionImage(categoryKey, name), locationObject)
  const shareUrl = buildShareUrl(build?.id || 0, locationObject)
  const statRows = statRowsForBuild(build, t)
  const upgradeRows = cleanEntries([
    build?.upgrade_1, build?.upgrade_2, build?.upgrade_3, build?.upgrade_4,
    build?.upgrade_5, build?.upgrade_6, build?.upgrade_7, build?.upgrade_8,
  ].filter(Boolean).map((name) => ({
    name,
    value: optionLabel(name),
    iconHref: optionImage('upgrade', name),
  })), 8)
  const upgrades = upgradeRows.map((row) => row.value)
  const weapons = [
    ['front', build?.front_weapon_slots], ['port', build?.port_weapon_slots],
    ['starboard', build?.starboard_weapon_slots], ['rear', build?.rear_weapon_slots],
    ['mortar', build?.mortar_weapon_slots], ['special', build?.special_weapon_slots],
  ].map(([key, slots]) => {
    const items = cleanEntries((slots || []).map((slot) => {
      const name = rawSlotItem(slot)
      return {
        name,
        value: listLabel(slot, optionLabel),
        iconHref: optionImage('weapon', name),
      }
    }), 4)
    return {
      key,
      label: t(`builds.detail.weapons.${key}`),
      items,
      lines: items.map((item) => item.value),
    }
  }).filter((group) => group.lines.length)

  const allSpecialistRows = cleanEntries((build?.special_crew_slots || []).map((slot) => {
    const name = rawSlotItem(slot)
    return {
      name,
      value: listLabel(slot, optionLabel),
      iconHref: optionImage('special_crew', name),
    }
  }), 5)
  const gingerSpecialistRow = allSpecialistRows.find((row) => row.name === 'Ginger') || null
  const specialistRows = allSpecialistRows.filter((row) => row !== gingerSpecialistRow)
  const gingerSpecialist = gingerSpecialistRow?.value || ''
  const specialists = specialistRows.map((row) => row.value)
  const equipmentRows = [
    build?.sails ? { key: 'sail', label: t('builds.detail.sail'), value: optionLabel(build.sails), iconHref: optionImage('sail', build.sails) } : null,
    build?.lantern ? { key: 'lantern', label: t('builds.detail.lantern'), value: optionLabel(build.lantern), iconHref: optionImage('lantern', build.lantern) } : null,
    build?.research_upgrade_slot_unlocked ? { key: 'upgrade', label: t('builds.detail.researchUpgradeSlot'), value: t('builds.detail.researchUpgradeSlotActive') } : null,
    build?.mortar_modification_installed ? { key: 'mortar', label: t('builds.detail.mortarModification'), value: t('builds.detail.mortarModificationActive') } : null,
  ].filter(Boolean)
  const inventoryGroups = [
    ['ammunition', t('builds.detail.ammunition'), build?.ammunition_slots, true],
    ['consumable', t('builds.detail.consumables'), build?.consumable_slots, false],
    ['hold', t('builds.detail.hold'), build?.hold_slots, true],
  ].map(([iconKey, title, slots, includeQuantity]) => {
    const items = cleanEntries((slots || []).map((slot) => {
      const name = rawSlotItem(slot)
      return {
        name,
        value: listLabel(slot, optionLabel, { includeQuantity }),
        iconHref: optionImage(iconKey, name),
      }
    }), 6)
    return { iconKey, title, items, lines: items.map((item) => item.value) }
  }).filter((group) => group.lines.length)
  const classificationLabels = (build?.classification_tags || []).map((value) => {
    const path = `discovery.builds.tags.${value}.label`
    const translated = t(path)
    return translated === path ? value.replaceAll('_', ' ') : translated
  })

  return {
    t,
    optionLabel,
    optionImage,
    shareUrl,
    buildName: build?.build_name || t('builds.print.fallbackTitle'),
    buildType: buildTypeLabel(build?.build_type, t),
    shipName: build?.ship?.name || '—',
    shipRate: build?.ship?.rate || '—',
    shipType: build?.ship?.ship_type || '—',
    // A saved build must render byte-identically until the build itself changes;
    // otherwise the server-side checksum cache would miss on every publication.
    generatedAt: new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(build?.updated_at || build?.created_at || 0),
    ),
    classificationLabels,
    summaryCards: makeSummaryCards(build, t),
    headlineStats: headlineStatsForBuild(build, statRows, t),
    statRows,
    crewRows: [
      { key: 'sailors', label: t('builds.create.crew.sailors'), value: `${build?.sailors ?? 0}`, hint: t('builds.list.sailorMin', { value: build?.ship_stats?.sailor_minimum || build?.ship?.sailor_minimum || 0 }) },
      ...(build?.musketeers ? [{ key: 'musketeers', label: t('builds.create.crew.musketeers'), value: `${build.musketeers}`, hint: '' }] : []),
      ...(build?.soldiers ? [{ key: 'soldiers', label: t('builds.create.crew.soldiers'), value: `${build.soldiers}`, hint: '' }] : []),
      ...(build?.mercenaries ? [{ key: 'mercenaries', label: t('builds.create.crew.mercenaries'), value: `${build.mercenaries}`, hint: '' }] : []),
    ],
    equipmentRows,
    upgrades,
    upgradeRows,
    specialists,
    specialistRows,
    gingerSpecialist,
    gingerSpecialistRow,
    weapons,
    inventoryGroups,
    notes: build?.details ? wrapText(build.details, 112) : [],
  }
}

function createBuildPrintDocument(build, helpers = {}) {
  const model = createBuildPrintModel(build, helpers)
  const theme = helpers.theme === 'light' ? 'light' : 'dark'
  const colors = BUILD_PRINT_THEMES[theme]
  const leftX = PAGE_PADDING
  const rightX = PAGE_PADDING + COLUMN_WIDTH + COLUMN_GAP
  let sectionIndex = 1
  const panels = []
  const performancePanel = renderPerformancePanel({
    x: PAGE_PADDING,
    y: 278,
    width: CONTENT_WIDTH,
    index: sectionIndex++,
    eyebrow: model.t('builds.commandDeck.performanceEyebrow'),
    title: model.t('builds.commandDeck.performanceTitle'),
    iconHref: PRINT_VISUALS.ship,
    rows: model.statRows,
    colors,
  })
  if (performancePanel.svg) panels.push(performancePanel.svg)
  const columnStartY = performancePanel.height ? 278 + performancePanel.height + SECTION_GAP : 278
  let leftY = columnStartY
  let rightY = columnStartY

  if (model.equipmentRows.length || model.upgrades.length) {
    const rows = [
      ...model.equipmentRows.map((row) => ({ ...row, iconHref: row.iconHref || PRINT_VISUALS[row.key] || PRINT_VISUALS.sail })),
      ...model.upgradeRows.map((upgrade, index) => ({ label: `${String(index + 1).padStart(2, '0')} · ${model.t('builds.detail.upgrades')}`, value: upgrade.value, iconHref: upgrade.iconHref || PRINT_VISUALS.upgrade })),
    ]
    const panel = renderRowsPanel({ x: leftX, y: leftY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.commandDeck.configurationEyebrow'), title: model.t('builds.print.configurationTitle'), iconHref: PRINT_VISUALS.sail, rows, colors })
    panels.push(panel.svg)
    leftY += panel.height + SECTION_GAP
  }

  if (model.weapons.length) {
    const panel = renderGroupedPanel({ x: leftX, y: leftY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.detail.shipStats'), title: model.t('builds.print.weaponLoadoutTitle'), iconHref: PRINT_VISUALS.weapon, groups: model.weapons.map((group) => ({ label: group.label, lines: group.lines, iconHref: group.items.find((item) => item.iconHref)?.iconHref || PRINT_VISUALS.weapon })), colors })
    panels.push(panel.svg)
    leftY += panel.height + SECTION_GAP
  }

  const crewRows = [
    ...model.crewRows.map((row) => ({ label: row.label, value: row.value, meta: row.hint, iconHref: PRINT_VISUALS.crew[row.key] })),
    ...model.specialistRows.map((row) => ({ label: model.t('builds.detail.specialCrew'), value: row.value, iconHref: row.iconHref || PRINT_VISUALS.specialist })),
    ...(model.gingerSpecialistRow ? [{ label: '+1 · Ginger', value: model.gingerSpecialistRow.value, iconHref: model.gingerSpecialistRow.iconHref || PRINT_VISUALS.specialist, accent: true }] : []),
  ]
  const crewPanel = renderRowsPanel({ x: rightX, y: rightY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.crewConsole.eyebrow'), title: model.t('builds.detail.crewDistribution'), iconHref: PRINT_VISUALS.crew.sailors, rows: crewRows, colors })
  panels.push(crewPanel.svg)
  rightY += crewPanel.height + SECTION_GAP

  if (model.inventoryGroups.length) {
    const inventoryOnLeft = leftY <= rightY
    const inventoryX = inventoryOnLeft ? leftX : rightX
    const inventoryY = inventoryOnLeft ? leftY : rightY
    const panel = renderInventoryPanel({ x: inventoryX, y: inventoryY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.detail.inventory'), title: model.t('builds.print.inventoryTitle'), iconHref: PRINT_VISUALS.hold, groups: model.inventoryGroups.map((group) => ({ iconKey: group.iconKey, label: group.title, lines: group.lines, items: group.items, iconHref: PRINT_VISUALS[group.iconKey] })), colors })
    panels.push(panel.svg)
    if (inventoryOnLeft) leftY += panel.height + SECTION_GAP
    else rightY += panel.height + SECTION_GAP
  }

  const contentBottom = Math.max(leftY, rightY)
  let notesBottom = contentBottom
  if (model.notes.length) {
    const notesPanel = renderNotesPanel(model, PAGE_PADDING, contentBottom, CONTENT_WIDTH, sectionIndex++, colors)
    panels.push(notesPanel.svg)
    notesBottom += notesPanel.height + SECTION_GAP
  }
  const footerY = Math.max(notesBottom + 12, BASE_PAGE_HEIGHT - FOOTER_HEIGHT - PAGE_PADDING)
  const pageHeight = Math.max(BASE_PAGE_HEIGHT, Math.ceil(footerY + FOOTER_HEIGHT + PAGE_PADDING))
  const classifications = model.classificationLabels.length ? model.classificationLabels.join('  ·  ') : model.buildType

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns="http://www.w3.org/2000/svg" width="${PAGE_WIDTH}" height="${pageHeight}" viewBox="0 0 ${PAGE_WIDTH} ${pageHeight}" data-build-sheet-version="2" data-build-sheet-theme="${theme}">
    <style>
      text{font-family:Inter,Segoe UI,Arial,sans-serif}.brand{fill:${colors.accent};font-size:17px;font-weight:800;letter-spacing:3px}.title{fill:${colors.text};font-family:Georgia,serif;font-size:51px;font-weight:500}.meta{fill:${colors.muted};font-size:19px}.share{fill:${colors.accent};font-size:14px}.eyebrow{fill:${colors.accent};font-size:12px;font-weight:800;letter-spacing:2px}.section-title{fill:${colors.text};font-family:Georgia,serif;font-size:24px}.index{fill:${colors.accent};font-size:11px;font-weight:800}.row-label{fill:${colors.muted};font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase}.row-value{fill:${colors.text};font-size:18px;font-weight:700}.row-meta{fill:${colors.faint};font-size:13px}.group-line{fill:${colors.text};font-size:16px}.inventory-index{fill:${colors.accent};font-size:11px;font-weight:800}.note-line{fill:${colors.muted};font-family:Georgia,serif;font-size:17px}.performance-label{fill:${colors.muted};font-size:13px;font-weight:700;letter-spacing:.7px;text-transform:uppercase}.performance-value{fill:${colors.text};font-family:Georgia,serif;font-size:29px}.performance-base{fill:${colors.faint};font-size:13px}.performance-modifier{font-size:13px;font-weight:800}.footer{fill:${colors.faint};font-size:13px}
    </style>
    <rect width="${PAGE_WIDTH}" height="${pageHeight}" fill="${colors.page}" />
    <rect x="14" y="14" width="${PAGE_WIDTH - 28}" height="${pageHeight - 28}" fill="none" stroke="${colors.borderStrong}" stroke-width="2" />
    <line x1="${PAGE_PADDING}" y1="${PAGE_PADDING}" x2="${PAGE_WIDTH - PAGE_PADDING}" y2="${PAGE_PADDING}" stroke="${colors.accent}" stroke-width="4" />
    ${renderIcon(PRINT_VISUALS.ship, PAGE_PADDING, 77, 92, true, colors)}
    <text x="${PAGE_PADDING + 116}" y="92" class="brand">${escapeXml(model.t('builds.print.eyebrow').toUpperCase())}</text>
    <text x="${PAGE_PADDING + 116}" y="146" class="title">${escapeXml(model.buildName)}</text>
    <text x="${PAGE_PADDING + 116}" y="184" class="meta">${escapeXml(`${model.shipName} · ${model.t('common.rate')} ${model.shipRate} · ${model.shipType} · ${model.buildType}`)}</text>
    <text x="${PAGE_PADDING + 116}" y="218" class="eyebrow">${escapeXml(classifications.toUpperCase())}</text>
    <text x="${PAGE_WIDTH - PAGE_PADDING}" y="93" text-anchor="end" class="meta">${escapeXml(model.t('builds.print.preparedAt', { value: model.generatedAt }))}</text>
    <text x="${PAGE_WIDTH - PAGE_PADDING}" y="120" text-anchor="end" class="share">${escapeXml(model.shareUrl)}</text>
    <line x1="${PAGE_PADDING}" y1="252" x2="${PAGE_WIDTH - PAGE_PADDING}" y2="252" stroke="${colors.border}" />
    ${panels.join('')}
    <line x1="${PAGE_PADDING}" y1="${footerY}" x2="${PAGE_WIDTH - PAGE_PADDING}" y2="${footerY}" stroke="${colors.border}" />
    <text x="${PAGE_PADDING}" y="${footerY + 39}" class="footer">${escapeXml(model.t('builds.print.footerHint'))}</text>
    <text x="${PAGE_WIDTH - PAGE_PADDING}" y="${footerY + 39}" text-anchor="end" class="share">${escapeXml(model.t('builds.print.footerBrand'))}</text>
  </svg>`

  return { svg, width: PAGE_WIDTH, height: pageHeight, model }
}

export function createBuildPrintSvg(build, helpers = {}) {
  return createBuildPrintDocument(build, helpers).svg
}

export function buildPrintFileName(build, extension = 'png') {
  const base = sanitizePrintFileName(build?.build_name || 'build-sheet', 'build-sheet')
  return `${base}-build-sheet.${String(extension || 'png').replace(/[^a-z0-9]/gi, '')}`
}

export async function createEmbeddedBuildPrintDocument(build, helpers = {}) {
  const document = createBuildPrintDocument(build, helpers)
  return {
    ...document,
    svg: await inlinePrintImageResources(document.svg, {
      fetchImpl: helpers.fetchImpl || (typeof globalThis.fetch === 'function' ? globalThis.fetch.bind(globalThis) : null),
      ImageImpl: helpers.ImageImpl || globalThis.Image,
      documentObject: helpers.documentObject || globalThis.document,
      cache: helpers.resourceCache || new Map(),
    }),
  }
}

export async function createBuildPrintPreviewUrl(build, helpers = {}) {
  const { svg } = await createEmbeddedBuildPrintDocument(build, helpers)
  return URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }))
}

export async function downloadBuildPrintSvg(build, helpers = {}) {
  const { svg } = await createEmbeddedBuildPrintDocument(build, helpers)
  triggerPrintDownload(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }), buildPrintFileName(build, 'svg'))
}

export async function createBuildPrintPngBlob(build, helpers = {}) {
  const { svg, width, height } = await createEmbeddedBuildPrintDocument(build, helpers)
  const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }))
  try {
    const image = await new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = () => reject(new Error('Build image could not be rendered.'))
      img.src = url
    })
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Canvas context is unavailable.')
    context.drawImage(image, 0, 0, width, height)
    return await new Promise((resolve, reject) => canvas.toBlob((result) => result ? resolve(result) : reject(new Error('Build image could not be encoded.')), 'image/png'))
  } finally {
    URL.revokeObjectURL(url)
  }
}

export async function downloadBuildPrintPng(build, helpers = {}) {
  const pngBlob = await createBuildPrintPngBlob(build, helpers)
  triggerPrintDownload(pngBlob, buildPrintFileName(build, 'png'))
}

export async function createBuildPrintHtml(build, helpers = {}) {
  const t = helpers.t || ((key) => key)
  const resourceCache = new Map()
  const lightDocument = await createEmbeddedBuildPrintDocument(build, { ...helpers, theme: 'light', resourceCache })
  const darkDocument = await createEmbeddedBuildPrintDocument(build, { ...helpers, theme: 'dark', resourceCache })
  const lightSvg = lightDocument.svg
  const darkSvg = darkDocument.svg
  const alt = escapeXml(t('builds.print.previewTitle'))
  const body = `<main class="build-print-document">
    <img class="build-print-sheet build-print-sheet-light" data-build-print-theme="light" alt="${alt}" src="data:image/svg+xml;charset=utf-8,${encodeURIComponent(lightSvg)}">
    <img class="build-print-sheet build-print-sheet-dark" data-build-print-theme="dark" alt="${alt}" src="data:image/svg+xml;charset=utf-8,${encodeURIComponent(darkSvg)}">
  </main>`
  const styles = `
    .build-print-document{width:min(calc(100% - 2rem),990px);margin:5.2rem auto 2rem}
    .build-print-sheet{display:block;width:100%;height:auto;box-shadow:0 1.5rem 4.4rem var(--document-shadow)}
    .build-print-sheet-dark{display:none}
    html[data-theme="dark"] .build-print-sheet-light{display:none}
    html[data-theme="dark"] .build-print-sheet-dark{display:block}
    @media(prefers-color-scheme:dark){html:not([data-theme]) .build-print-sheet-light{display:none}html:not([data-theme]) .build-print-sheet-dark{display:block}}
    @media print{.build-print-document{width:100%;margin:0}.build-print-sheet{width:100%;max-width:none;box-shadow:none}@page{margin:0}}
    @media screen and (max-width:760px){.build-print-document{width:calc(100% - 1rem);margin:7.8rem .5rem 1rem}}
  `
  return createPrintDocumentHtml({
    lang: helpers.lang || (typeof document !== 'undefined' ? document.documentElement.lang : 'en') || 'en',
    title: build?.build_name || t('builds.print.fallbackTitle'),
    body,
    styles,
    labels: createPrintLabels(t),
  })
}

export async function openBuildPrintWindow(build, helpers = {}) {
  const popup = window.open('', '_blank', 'width=1040,height=1440')
  if (!popup) throw new Error('Print preview could not be opened.')
  popup.opener = null
  popup.document.open()
  popup.document.write('<!doctype html><title>Preparing print preview…</title><p style="font-family:sans-serif;padding:2rem">Preparing print preview…</p>')
  popup.document.close()
  try {
    const html = await createBuildPrintHtml(build, helpers)
    popup.document.open()
    popup.document.write(html)
    popup.document.close()
    popup.focus()
    return popup
  } catch (error) {
    popup.close()
    throw error
  }
}

export { createBuildPrintModel, createBuildPrintDocument, inlinePrintImageResources }
