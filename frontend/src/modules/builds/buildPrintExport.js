import { buildCrewVisualUrl, buildVisualUrl } from './buildVisuals.js'
import { buildShareUrl } from './shareBuild.js'
import {
  createPrintDocumentHtml,
  createPrintLabels,
  escapePrintMarkup,
  openPrintWindow,
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

const CORE_STAT_KEYS = new Set([
  'durability',
  'speed_min_knots',
  'speed_knots',
  'maneuverability',
  'armor',
  'hold_capacity',
  'crew_capacity',
  'sailor_minimum',
  'displacement_tons',
])

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

function roundByPrecision(value, precision = 0) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  const factor = 10 ** Number(precision || 0)
  const rounded = Math.round(Number(value) * factor) / factor
  return Number(precision || 0) === 0 ? Math.round(rounded) : rounded
}

function formatStatValue(value, unit, precision = 0) {
  const number = roundByPrecision(value, precision)
  if (number === null) return '—'
  return `${number}${unit ? ` ${unit}` : ''}`
}

function listLabel(slot, labeler) {
  if (!slot) return ''
  if (typeof slot === 'string') return labeler(slot)
  if (!slot.item) return ''
  const quantity = Number(slot.quantity || 1)
  return `${labeler(slot.item)}${quantity > 1 ? ` ×${quantity}` : ''}`
}

function cleanLines(items, limit = Infinity) {
  const lines = (items || []).map((item) => String(item || '').trim()).filter(Boolean)
  if (lines.length <= limit) return lines
  return [...lines.slice(0, Math.max(0, limit - 1)), `+${lines.length - (limit - 1)} more`]
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
    .filter((row) => CORE_STAT_KEYS.has(row.key))
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
  const shareUrl = buildShareUrl(build?.id || 0, helpers.locationObject || globalThis.location)
  const statRows = statRowsForBuild(build, t)
  const upgrades = cleanLines([
    build?.upgrade_1, build?.upgrade_2, build?.upgrade_3, build?.upgrade_4,
    build?.upgrade_5, build?.upgrade_6, build?.upgrade_7, build?.upgrade_8,
  ].filter(Boolean).map(optionLabel), 8)
  const weapons = [
    ['front', build?.front_weapon_slots], ['port', build?.port_weapon_slots],
    ['starboard', build?.starboard_weapon_slots], ['rear', build?.rear_weapon_slots],
    ['mortar', build?.mortar_weapon_slots], ['special', build?.special_weapon_slots],
  ].map(([key, slots]) => ({
    key,
    label: t(`builds.detail.weapons.${key}`),
    lines: cleanLines((slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 4),
  })).filter((group) => group.lines.length)

  const allSpecialists = cleanLines((build?.special_crew_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 5)
  const gingerSpecialist = allSpecialists.find((name) => name.replace(/ ×\d+$/, '') === 'Ginger') || ''
  const specialists = allSpecialists.filter((name) => name !== gingerSpecialist)
  const equipmentRows = [
    build?.sails ? { key: 'sail', label: t('builds.detail.sail'), value: optionLabel(build.sails) } : null,
    build?.lantern ? { key: 'lantern', label: t('builds.detail.lantern'), value: optionLabel(build.lantern) } : null,
    build?.research_upgrade_slot_unlocked ? { key: 'upgrade', label: t('builds.detail.researchUpgradeSlot'), value: t('builds.detail.researchUpgradeSlotActive') } : null,
  ].filter(Boolean)
  const inventoryGroups = [
    { iconKey: 'ammunition', title: t('builds.detail.ammunition'), lines: cleanLines((build?.ammunition_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 6) },
    { iconKey: 'consumable', title: t('builds.detail.consumables'), lines: cleanLines((build?.consumable_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 6) },
    { iconKey: 'hold', title: t('builds.detail.hold'), lines: cleanLines((build?.hold_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 6) },
  ].filter((group) => group.lines.length)
  const classificationLabels = (build?.classification_tags || []).map((value) => {
    const path = `discovery.builds.tags.${value}.label`
    const translated = t(path)
    return translated === path ? value.replaceAll('_', ' ') : translated
  })

  return {
    t,
    optionLabel,
    shareUrl,
    buildName: build?.build_name || t('builds.print.fallbackTitle'),
    buildType: buildTypeLabel(build?.build_type, t),
    shipName: build?.ship?.name || '—',
    shipRate: build?.ship?.rate || '—',
    shipType: build?.ship?.ship_type || '—',
    generatedAt: new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date()),
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
    specialists,
    gingerSpecialist,
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
  let leftY = 416
  let rightY = 416
  let sectionIndex = 1
  const panels = []

  if (model.equipmentRows.length || model.upgrades.length) {
    const rows = [
      ...model.equipmentRows.map((row) => ({ ...row, iconHref: PRINT_VISUALS[row.key] || PRINT_VISUALS.sail })),
      ...model.upgrades.map((upgrade, index) => ({ label: `${String(index + 1).padStart(2, '0')} · ${model.t('builds.detail.upgrades')}`, value: upgrade, iconHref: PRINT_VISUALS.upgrade })),
    ]
    const panel = renderRowsPanel({ x: leftX, y: leftY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.commandDeck.configurationEyebrow'), title: model.t('builds.print.configurationTitle'), iconHref: PRINT_VISUALS.sail, rows, colors })
    panels.push(panel.svg)
    leftY += panel.height + SECTION_GAP
  }

  if (model.weapons.length) {
    const panel = renderGroupedPanel({ x: leftX, y: leftY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.detail.shipStats'), title: model.t('builds.print.weaponLoadoutTitle'), iconHref: PRINT_VISUALS.weapon, groups: model.weapons.map((group) => ({ label: group.label, lines: group.lines, iconHref: PRINT_VISUALS.weapon })), colors })
    panels.push(panel.svg)
    leftY += panel.height + SECTION_GAP
  }

  const crewRows = [
    ...model.crewRows.map((row) => ({ label: row.label, value: row.value, meta: row.hint, iconHref: PRINT_VISUALS.crew[row.key] })),
    ...model.specialists.map((name) => ({ label: model.t('builds.detail.specialCrew'), value: name, iconHref: PRINT_VISUALS.specialist })),
    ...(model.gingerSpecialist ? [{ label: '+1 · Ginger', value: model.gingerSpecialist, iconHref: PRINT_VISUALS.specialist, accent: true }] : []),
  ]
  const crewPanel = renderRowsPanel({ x: rightX, y: rightY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.crewConsole.eyebrow'), title: model.t('builds.detail.crewDistribution'), iconHref: PRINT_VISUALS.crew.sailors, rows: crewRows, colors })
  panels.push(crewPanel.svg)
  rightY += crewPanel.height + SECTION_GAP

  if (model.inventoryGroups.length) {
    const inventoryOnLeft = leftY <= rightY
    const inventoryX = inventoryOnLeft ? leftX : rightX
    const inventoryY = inventoryOnLeft ? leftY : rightY
    const panel = renderGroupedPanel({ x: inventoryX, y: inventoryY, width: COLUMN_WIDTH, index: sectionIndex++, eyebrow: model.t('builds.detail.inventory'), title: model.t('builds.print.inventoryTitle'), iconHref: PRINT_VISUALS.hold, groups: model.inventoryGroups.map((group) => ({ label: group.title, lines: group.lines, iconHref: PRINT_VISUALS[group.iconKey] })), colors })
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
  const statWidth = (CONTENT_WIDTH - (4 * 12)) / 5
  const statCards = model.headlineStats.map((stat, index) => {
    const x = PAGE_PADDING + (index * (statWidth + 12))
    return `<g>
      <rect x="${x}" y="278" width="${statWidth}" height="112" rx="5" fill="${colors.panel}" stroke="${index === 0 ? colors.borderStrong : colors.border}" />
      <text x="${x + 18}" y="312" class="stat-label">${escapeXml(stat.label)}</text>
      <text x="${x + 18}" y="357" class="stat-value">${escapeXml(stat.value)}</text>
      <line x1="${x + 18}" y1="373" x2="${x + statWidth - 18}" y2="373" stroke="${index === 0 ? colors.accent : colors.border}" />
    </g>`
  }).join('')
  const classifications = model.classificationLabels.length ? model.classificationLabels.join('  ·  ') : model.buildType

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns="http://www.w3.org/2000/svg" width="${PAGE_WIDTH}" height="${pageHeight}" viewBox="0 0 ${PAGE_WIDTH} ${pageHeight}" data-build-sheet-version="2" data-build-sheet-theme="${theme}">
    <style>
      text{font-family:Inter,Segoe UI,Arial,sans-serif}.brand{fill:${colors.accent};font-size:17px;font-weight:800;letter-spacing:3px}.title{fill:${colors.text};font-family:Georgia,serif;font-size:51px;font-weight:500}.meta{fill:${colors.muted};font-size:19px}.share{fill:${colors.accent};font-size:14px}.eyebrow{fill:${colors.accent};font-size:12px;font-weight:800;letter-spacing:2px}.section-title{fill:${colors.text};font-family:Georgia,serif;font-size:24px}.index{fill:${colors.accent};font-size:11px;font-weight:800}.row-label{fill:${colors.muted};font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase}.row-value{fill:${colors.text};font-size:18px;font-weight:700}.row-meta{fill:${colors.faint};font-size:13px}.group-line{fill:${colors.text};font-size:16px}.note-line{fill:${colors.muted};font-family:Georgia,serif;font-size:17px}.stat-label{fill:${colors.muted};font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase}.stat-value{fill:${colors.text};font-family:Georgia,serif;font-size:32px}.footer{fill:${colors.faint};font-size:13px}
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
    ${statCards}
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

export function createBuildPrintPreviewUrl(build, helpers = {}) {
  const { svg } = createBuildPrintDocument(build, helpers)
  return URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }))
}

export function downloadBuildPrintSvg(build, helpers = {}) {
  const { svg } = createBuildPrintDocument(build, helpers)
  triggerPrintDownload(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }), buildPrintFileName(build, 'svg'))
}

export async function downloadBuildPrintPng(build, helpers = {}) {
  const { svg, width, height } = createBuildPrintDocument(build, helpers)
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
    const pngBlob = await new Promise((resolve, reject) => canvas.toBlob((result) => result ? resolve(result) : reject(new Error('Build image could not be encoded.')), 'image/png'))
    triggerPrintDownload(pngBlob, buildPrintFileName(build, 'png'))
  } finally {
    URL.revokeObjectURL(url)
  }
}

export function createBuildPrintHtml(build, helpers = {}) {
  const t = helpers.t || ((key) => key)
  const lightSvg = createBuildPrintDocument(build, { ...helpers, theme: 'light' }).svg
  const darkSvg = createBuildPrintDocument(build, { ...helpers, theme: 'dark' }).svg
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

export function openBuildPrintWindow(build, helpers = {}) {
  return openPrintWindow(createBuildPrintHtml(build, helpers), {
    features: 'width=1040,height=1440',
    errorMessage: 'Print preview could not be opened.',
  })
}

export { createBuildPrintModel, createBuildPrintDocument }
