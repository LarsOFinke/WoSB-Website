import { buildShareUrl } from './shareBuild.js'

const PAGE_WIDTH = 1240
const BASE_PAGE_HEIGHT = 1480
const FOOTER_HEIGHT = 72
const PANEL_GAP = 24
const PAGE_PADDING = 52
const CONTENT_WIDTH = PAGE_WIDTH - PAGE_PADDING * 2
const COLUMN_WIDTH = (CONTENT_WIDTH - PANEL_GAP) / 2

const COLORS = {
  page: '#08111b',
  pageGlow: '#102032',
  panel: '#101d2b',
  panelSoft: '#152537',
  border: 'rgba(221, 231, 244, 0.14)',
  borderStrong: 'rgba(241, 184, 91, 0.34)',
  text: '#f4f7fb',
  muted: '#b8c4d2',
  accent: '#f1b85b',
  accentStrong: '#ffd27a',
  success: '#9fe6b2',
  danger: '#ff9d9d',
}

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

function escapeXml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

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

function optionOrDash(labeler, value) {
  return value ? labeler(value) : '—'
}

function listLabel(slot, labeler) {
  if (!slot) return ''
  if (typeof slot === 'string') return labeler(slot)
  if (!slot.item) return ''
  const quantity = Number(slot.quantity || 1)
  return `${labeler(slot.item)}${quantity > 1 ? ` ×${quantity}` : ''}`
}

function cleanLines(items, limit = Infinity) {
  const lines = (items || [])
    .map((item) => String(item || '').trim())
    .filter(Boolean)
  if (lines.length <= limit) return lines
  return [...lines.slice(0, Math.max(0, limit - 1)), `+${lines.length - (limit - 1)} more`]
}

function wrapText(text, maxChars = 44, maxLines = Infinity) {
  const paragraphs = String(text || '').replace(/\r/g, '').split('\n')
  const lines = []
  for (const paragraph of paragraphs) {
    const normalized = paragraph.replace(/\s+/g, ' ').trim()
    if (!normalized) {
      if (lines.length && lines[lines.length - 1] !== '') lines.push('')
      continue
    }
    let current = ''
    for (const rawWord of normalized.split(' ')) {
      const chunks = []
      let word = rawWord
      while (word.length > maxChars) {
        chunks.push(word.slice(0, maxChars - 1) + '…')
        word = word.slice(maxChars - 1)
      }
      if (word) chunks.push(word)
      for (const chunk of chunks) {
        const next = current ? `${current} ${chunk}` : chunk
        if (next.length <= maxChars) {
          current = next
        } else {
          if (current) lines.push(current)
          current = chunk
        }
        if (lines.length >= maxLines) return lines.slice(0, maxLines)
      }
    }
    if (current) lines.push(current)
    if (lines.length >= maxLines) return lines.slice(0, maxLines)
  }
  while (lines.length && lines[lines.length - 1] === '') lines.pop()
  return lines
}

function sanitizeFileName(value) {
  return String(value || 'build')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
    .slice(0, 72) || 'build'
}

function renderMultilineText(lines, x, y, { fontSize = 18, fill = COLORS.text, fontWeight = 400, lineHeight = 1.4 } = {}) {
  return lines.map((line, index) => `
    <text x="${x}" y="${y + (index * fontSize * lineHeight)}" fill="${fill}" font-size="${fontSize}" font-weight="${fontWeight}">${escapeXml(line)}</text>`).join('')
}

function renderPanel({ x, y, width, height, eyebrow, title, content }) {
  return `
    <g>
      <rect x="${x}" y="${y}" width="${width}" height="${height}" rx="26" fill="${COLORS.panel}" stroke="${COLORS.border}" />
      <text x="${x + 28}" y="${y + 34}" fill="${COLORS.accent}" font-size="14" font-weight="700" letter-spacing="0.12em">${escapeXml(eyebrow.toUpperCase())}</text>
      <text x="${x + 28}" y="${y + 66}" fill="${COLORS.text}" font-size="28" font-weight="700">${escapeXml(title)}</text>
      ${content}
    </g>`
}


function lineBlockHeight(lineCount, { fontSize = 15, lineHeight = 1.22, titleGap = 20, paddingBottom = 12 } = {}) {
  const safeCount = Math.max(1, Number(lineCount || 0))
  return titleGap + (safeCount * fontSize * lineHeight) + paddingBottom
}

function createBuildPrintDocument(build, helpers = {}) {
  const model = createBuildPrintModel(build, helpers)
  const xLeft = PAGE_PADDING
  const xRight = PAGE_PADDING + COLUMN_WIDTH + PANEL_GAP
  let leftY = 340
  let rightY = 340

  const summaryCardWidth = (CONTENT_WIDTH - (PANEL_GAP * 3)) / 4
  const summaryCardsSvg = model.summaryCards.map((card, index) => {
    const x = PAGE_PADDING + ((summaryCardWidth + PANEL_GAP) * index)
    return `
      <g>
        <rect x="${x}" y="212" width="${summaryCardWidth}" height="104" rx="22" fill="${COLORS.panelSoft}" stroke="${COLORS.border}" />
        <text x="${x + 24}" y="244" fill="${COLORS.muted}" font-size="14" font-weight="600">${escapeXml(card.label)}</text>
        <text x="${x + 24}" y="278" fill="${COLORS.text}" font-size="30" font-weight="700">${escapeXml(card.value)}</text>
        <text x="${x + 24}" y="298" fill="${COLORS.accentStrong}" font-size="13">${escapeXml(card.detail)}</text>
      </g>`
  }).join('')

  const statContent = model.statRows.map((row, index) => {
    const y = leftY + 110 + index * 38
    return `
      <line x1="${xLeft + 28}" y1="${y - 18}" x2="${xLeft + COLUMN_WIDTH - 28}" y2="${y - 18}" stroke="${index === 0 ? 'transparent' : COLORS.border}" />
      <text x="${xLeft + 28}" y="${y}" fill="${COLORS.muted}" font-size="16">${escapeXml(row.label)}</text>
      <text x="${xLeft + COLUMN_WIDTH - 28}" y="${y}" text-anchor="end" fill="${COLORS.text}" font-size="18" font-weight="700">${escapeXml(formatStatValue(row.effective, row.unit, row.precision))}</text>
      <text x="${xLeft + COLUMN_WIDTH - 28}" y="${y + 18}" text-anchor="end" fill="${Number(row.modifier) ? COLORS.accentStrong : COLORS.muted}" font-size="13">${escapeXml(`${formatStatValue(row.base, row.unit, row.precision)} · ${formatModifier(row)}`)}</text>`
  }).join('')
  const statPanelHeight = 420
  const statPanel = renderPanel({ x: xLeft, y: leftY, width: COLUMN_WIDTH, height: statPanelHeight, eyebrow: model.t('builds.commandDeck.performanceEyebrow'), title: model.t('builds.commandDeck.performanceTitle'), content: statContent })
  leftY += statPanelHeight + PANEL_GAP

  const crewContent = model.crewRows.map((row, index) => {
    const y = leftY + 112 + index * 54
    return `
      <text x="${xLeft + 28}" y="${y}" fill="${COLORS.muted}" font-size="16">${escapeXml(row.label)}</text>
      <text x="${xLeft + COLUMN_WIDTH - 28}" y="${y}" text-anchor="end" fill="${COLORS.text}" font-size="22" font-weight="700">${escapeXml(row.value)}</text>
      ${row.hint ? `<text x="${xLeft + 28}" y="${y + 20}" fill="${COLORS.accentStrong}" font-size="13">${escapeXml(row.hint)}</text>` : ''}`
  }).join('')
  const crewPanelHeight = Math.max(236, 120 + (model.crewRows.length * 54))
  const crewPanel = renderPanel({ x: xLeft, y: leftY, width: COLUMN_WIDTH, height: crewPanelHeight, eyebrow: model.t('builds.crewConsole.eyebrow'), title: model.t('builds.detail.crewDistribution'), content: crewContent })
  leftY += crewPanelHeight + PANEL_GAP

  let upgradePanel = ''
  if (model.upgrades.length) {
    const upgradeLines = model.upgrades
    const upgradeContent = upgradeLines.map((line, index) => `
      <text x="${xLeft + 28}" y="${leftY + 116 + index * 32}" fill="${COLORS.text}" font-size="17">${escapeXml(`${String(index + 1).padStart(2, '0')} · ${line}`)}</text>`).join('')
    const upgradePanelHeight = Math.max(276, 116 + (upgradeLines.length * 32) + 28)
    upgradePanel = renderPanel({ x: xLeft, y: leftY, width: COLUMN_WIDTH, height: upgradePanelHeight, eyebrow: model.t('builds.commandDeck.configurationEyebrow'), title: model.t('builds.detail.upgrades'), content: upgradeContent })
    leftY += upgradePanelHeight
  }

  let equipmentPanel = ''
  if (model.equipmentRows.length || model.specialists.length) {
    const equipmentContent = model.equipmentRows.map((row, index) => {
    const y = rightY + 112 + index * 56
    return `
      <text x="${xRight + 28}" y="${y}" fill="${COLORS.muted}" font-size="16">${escapeXml(row.label)}</text>
      <text x="${xRight + 28}" y="${y + 24}" fill="${COLORS.text}" font-size="22" font-weight="700">${escapeXml(row.value)}</text>`
  }).join('') + (model.specialists.length
    ? renderMultilineText([
        model.t('builds.detail.specialCrew'),
        ...model.specialists,
      ], xRight + 28, rightY + (model.equipmentRows.length * 56) + 136, { fontSize: 16, fill: COLORS.text })
    : '')
    const equipmentPanelHeight = Math.max(228, 136 + (model.equipmentRows.length * 56) + (model.specialists.length ? 26 + (model.specialists.length * 16 * 1.4) : 0))
    equipmentPanel = renderPanel({ x: xRight, y: rightY, width: COLUMN_WIDTH, height: equipmentPanelHeight, eyebrow: model.t('builds.detail.buildType'), title: model.t('builds.print.configurationTitle'), content: equipmentContent })
    rightY += equipmentPanelHeight + PANEL_GAP
  }

  let weaponPanel = ''
  if (model.weapons.length) {
    const weaponContent = model.weapons.map((group, index) => {
    const baseY = rightY + 108 + index * 78
    const lines = group.lines.length ? group.lines : ['—']
    return `
      <text x="${xRight + 28}" y="${baseY}" fill="${COLORS.accentStrong}" font-size="15" font-weight="700">${escapeXml(group.label)}</text>
      ${renderMultilineText(lines, xRight + 28, baseY + 20, { fontSize: 15, fill: COLORS.text, lineHeight: 1.25 })}`
  }).join('')
    const weaponPanelHeight = Math.max(248, 112 + (model.weapons.length * 78))
    weaponPanel = renderPanel({ x: xRight, y: rightY, width: COLUMN_WIDTH, height: weaponPanelHeight, eyebrow: model.t('builds.detail.shipStats'), title: model.t('builds.print.weaponLoadoutTitle'), content: weaponContent })
    rightY += weaponPanelHeight + PANEL_GAP
  }

  let inventoryPanel = ''
  if (model.inventoryGroups.length) {
    let inventoryCursorY = rightY + 108
    const inventoryContent = model.inventoryGroups.map((group, index) => {
    const sectionY = inventoryCursorY
    const lines = group.lines.length ? group.lines : ['—']
    inventoryCursorY += lineBlockHeight(lines.length, { fontSize: 15, lineHeight: 1.24, titleGap: 22, paddingBottom: index === model.inventoryGroups.length - 1 ? 0 : 24 })
    return `
      <text x="${xRight + 28}" y="${sectionY}" fill="${COLORS.accentStrong}" font-size="15" font-weight="700">${escapeXml(group.title)}</text>
      ${renderMultilineText(lines, xRight + 28, sectionY + 22, { fontSize: 15, fill: COLORS.text, lineHeight: 1.24 })}`
  }).join('')
    const inventoryPanelHeight = Math.max(212, Math.ceil(inventoryCursorY - rightY + 40))
    inventoryPanel = renderPanel({ x: xRight, y: rightY, width: COLUMN_WIDTH, height: inventoryPanelHeight, eyebrow: model.t('builds.detail.inventory'), title: model.t('builds.print.inventoryTitle'), content: inventoryContent })
    rightY += inventoryPanelHeight
  }

  const hasNotes = model.notes.length > 0
  const footerLines = hasNotes ? model.notes : []
  const notesTextHeight = Math.max(1, footerLines.length) * 16 * 1.45
  const contentBottomY = Math.max(leftY, rightY)
  const notesPanelY = hasNotes ? (contentBottomY + PANEL_GAP) : 0
  const notesPanelHeight = hasNotes ? Math.max(230, Math.ceil(132 + notesTextHeight)) : 0
  const footerY = hasNotes ? (notesPanelY + notesPanelHeight + PANEL_GAP) : (contentBottomY + PANEL_GAP)
  const pageHeight = Math.max(BASE_PAGE_HEIGHT, Math.ceil(footerY + FOOTER_HEIGHT + PAGE_PADDING))

  const svg = `<?xml version="1.0" encoding="UTF-8"?>
  <svg xmlns="http://www.w3.org/2000/svg" width="${PAGE_WIDTH}" height="${pageHeight}" viewBox="0 0 ${PAGE_WIDTH} ${pageHeight}">
    <defs>
      <linearGradient id="pageGlow" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="${COLORS.pageGlow}" stop-opacity="0.78" />
        <stop offset="100%" stop-color="${COLORS.page}" stop-opacity="1" />
      </linearGradient>
      <linearGradient id="accentGlow" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="${COLORS.accent}" stop-opacity="0.92" />
        <stop offset="100%" stop-color="${COLORS.accentStrong}" stop-opacity="0.35" />
      </linearGradient>
    </defs>
    <rect width="${PAGE_WIDTH}" height="${pageHeight}" fill="${COLORS.page}" />
    <circle cx="180" cy="140" r="260" fill="${COLORS.accent}" fill-opacity="0.09" />
    <circle cx="1080" cy="120" r="220" fill="#5888bb" fill-opacity="0.11" />
    <rect x="14" y="14" width="${PAGE_WIDTH - 28}" height="${pageHeight - 28}" rx="38" fill="url(#pageGlow)" stroke="${COLORS.border}" />
    <rect x="${PAGE_PADDING}" y="${PAGE_PADDING}" width="${CONTENT_WIDTH}" height="132" rx="30" fill="${COLORS.panel}" stroke="${COLORS.borderStrong}" />
    <rect x="${PAGE_PADDING + 24}" y="${PAGE_PADDING + 24}" width="6" height="84" rx="3" fill="url(#accentGlow)" />
    <text x="${PAGE_PADDING + 48}" y="${PAGE_PADDING + 38}" fill="${COLORS.accent}" font-size="15" font-weight="700" letter-spacing="0.12em">${escapeXml(model.t('builds.print.eyebrow').toUpperCase())}</text>
    <text x="${PAGE_PADDING + 48}" y="${PAGE_PADDING + 82}" fill="${COLORS.text}" font-size="40" font-weight="800">${escapeXml(model.buildName)}</text>
    <text x="${PAGE_PADDING + 48}" y="${PAGE_PADDING + 112}" fill="${COLORS.muted}" font-size="20">${escapeXml(`${model.shipName} · ${model.t('common.rate')} ${model.shipRate} · ${model.shipType} · ${model.buildType}`)}</text>
    <text x="${PAGE_PADDING + CONTENT_WIDTH - 24}" y="${PAGE_PADDING + 38}" text-anchor="end" fill="${COLORS.muted}" font-size="14">${escapeXml(model.t('builds.print.preparedAt', { value: model.generatedAt }))}</text>
    <text x="${PAGE_PADDING + CONTENT_WIDTH - 24}" y="${PAGE_PADDING + 62}" text-anchor="end" fill="${COLORS.accentStrong}" font-size="14">${escapeXml(model.shareUrl)}</text>
    ${summaryCardsSvg}
    ${statPanel}
    ${crewPanel}
    ${upgradePanel}
    ${equipmentPanel}
    ${weaponPanel}
    ${inventoryPanel}
    ${hasNotes ? `<g>
      <rect x="${PAGE_PADDING}" y="${notesPanelY}" width="${CONTENT_WIDTH}" height="${notesPanelHeight}" rx="26" fill="${COLORS.panel}" stroke="${COLORS.border}" />
      <text x="${PAGE_PADDING + 28}" y="${notesPanelY + 34}" fill="${COLORS.accent}" font-size="14" font-weight="700" letter-spacing="0.12em">${escapeXml(model.t('builds.detail.details').toUpperCase())}</text>
      <text x="${PAGE_PADDING + 28}" y="${notesPanelY + 66}" fill="${COLORS.text}" font-size="28" font-weight="700">${escapeXml(model.t('builds.print.notesTitle'))}</text>
      ${renderMultilineText(footerLines, PAGE_PADDING + 28, notesPanelY + 104, { fontSize: 16, fill: COLORS.text, lineHeight: 1.45 })}
    </g>` : ''}
    <g>
      <line x1="${PAGE_PADDING + 28}" y1="${footerY + 16}" x2="${PAGE_PADDING + CONTENT_WIDTH - 28}" y2="${footerY + 16}" stroke="${COLORS.border}" />
      <text x="${PAGE_PADDING + 28}" y="${footerY + 48}" fill="${COLORS.muted}" font-size="14">${escapeXml(model.t('builds.print.footerHint'))}</text>
      <text x="${PAGE_PADDING + CONTENT_WIDTH - 28}" y="${footerY + 48}" text-anchor="end" fill="${COLORS.accentStrong}" font-size="14">${escapeXml(model.t('builds.print.footerBrand'))}</text>
    </g>
  </svg>`

  return { svg, width: PAGE_WIDTH, height: pageHeight, model }
}

function statRowsForBuild(build, t) {
  return (build?.ship_stats?.stat_rows || [])
    .filter((row) => CORE_STAT_KEYS.has(row.key))
    .map((row) => {
      const path = `builds.statLabels.${row.key}`
      const translated = t(path)
      return {
        ...row,
        label: translated === path ? (row.label || String(row.key).replaceAll('_', ' ')) : translated,
      }
    })
}

function formatModifier(row) {
  const value = Number(row?.modifier || 0)
  if (!Number.isFinite(value) || value === 0) return '—'
  const sign = value > 0 ? '+' : ''
  const suffix = row.modifier_kind === 'percent' || row.unit === '%' || String(row.effect_key || '').endsWith('_pct')
    ? '%'
    : (row.unit ? ` ${row.unit}` : '')
  return `${sign}${roundByPrecision(value, row.precision || 0)}${suffix}`
}

function buildTypeLabel(buildType, t) {
  return t(`builds.types.${buildType || 'balanced'}`)
}

function makeSummaryCards(build, t) {
  const stats = build?.ship_stats || {}
  const crewCapacity = stats.crew_capacity || build?.ship?.crew_capacity || 0
  const crewTotal = stats.crew_total || 0
  return [
    { label: t('builds.detail.buildType'), value: buildTypeLabel(build?.build_type, t), detail: `${t('common.rate')} ${build?.ship?.rate || '—'}` },
    { label: t('builds.detail.shipStats'), value: `${stats.weapon_total || 0}`, detail: t('builds.detail.weaponCapacity', { count: stats.weapon_capacity_total || 0 }) },
    { label: t('builds.detail.crewDistribution'), value: `${crewTotal}/${crewCapacity}`, detail: t('builds.commandDeck.crewRemaining', { value: stats.crew_remaining || 0 }) },
    { label: t('builds.detail.upgrades'), value: `${stats.upgrades_selected || [build?.upgrade_1, build?.upgrade_2, build?.upgrade_3, build?.upgrade_4, build?.upgrade_5, build?.upgrade_6, build?.upgrade_7, build?.upgrade_8].filter(Boolean).length || 0}`, detail: t('builds.list.upgradeSummary', { used: [build?.upgrade_1, build?.upgrade_2, build?.upgrade_3, build?.upgrade_4, build?.upgrade_5, build?.upgrade_6, build?.upgrade_7, build?.upgrade_8].filter(Boolean).length, max: stats.upgrade_slots_available || 0 }) },
  ]
}

function createBuildPrintModel(build, helpers = {}) {
  const t = helpers.t || ((key, params = {}) => {
    if (!params || typeof params !== 'object') return key
    return Object.entries(params).reduce((acc, [name, value]) => acc.replaceAll(`{${name}}`, value), key)
  })
  const optionLabel = helpers.optionLabel || ((value) => value || '')
  const locationObject = helpers.locationObject || globalThis.location
  const shareUrl = buildShareUrl(build?.id || 0, locationObject)
  const statRows = statRowsForBuild(build, t)
  const summaryCards = makeSummaryCards(build, t)
  const upgrades = cleanLines([
    build?.upgrade_1,
    build?.upgrade_2,
    build?.upgrade_3,
    build?.upgrade_4,
    build?.upgrade_5,
    build?.upgrade_6,
    build?.upgrade_7,
    build?.upgrade_8,
  ].filter(Boolean).map(optionLabel), 8)
  const weaponGroups = [
    { label: t('builds.detail.weapons.front'), slots: build?.front_weapon_slots || [] },
    { label: t('builds.detail.weapons.port'), slots: build?.port_weapon_slots || [] },
    { label: t('builds.detail.weapons.starboard'), slots: build?.starboard_weapon_slots || [] },
    { label: t('builds.detail.weapons.rear'), slots: build?.rear_weapon_slots || [] },
    { label: t('builds.detail.weapons.mortar'), slots: build?.mortar_weapon_slots || [] },
    { label: t('builds.detail.weapons.special'), slots: build?.special_weapon_slots || [] },
  ].map((group) => ({
    ...group,
    lines: cleanLines(group.slots.map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 3),
  })).filter((group) => group.lines.length > 0)

  const specialists = cleanLines((build?.special_crew_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 4)
  const equipmentRows = [
      build?.sails ? { label: t('builds.detail.sail'), value: optionLabel(build?.sails) } : null,
      build?.lantern ? { label: t('builds.detail.lantern'), value: optionLabel(build?.lantern) } : null,
      build?.research_upgrade_slot_unlocked ? { label: t('builds.detail.researchUpgradeSlot'), value: t('builds.detail.researchUpgradeSlotActive') } : null,
    ].filter(Boolean)
  const inventoryGroups = [
    { title: t('builds.detail.ammunition'), lines: cleanLines((build?.ammunition_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 4) },
    { title: t('builds.detail.consumables'), lines: cleanLines((build?.consumable_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 4) },
    { title: t('builds.detail.hold'), lines: cleanLines((build?.hold_slots || []).map((slot) => listLabel(slot, optionLabel)).filter(Boolean), 4) },
  ].filter((group) => group.lines.length > 0)

  const noteLines = build?.details ? wrapText(build.details, 70) : []

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
    summaryCards,
    statRows,
    crewRows: [
      { label: t('builds.create.crew.sailors'), value: `${build?.sailors ?? 0}`, hint: t('builds.list.sailorMin', { value: build?.ship_stats?.sailor_minimum || build?.ship?.sailor_minimum || 0 }) },
      ...(build?.musketeers ? [{ label: t('builds.create.crew.musketeers'), value: `${build.musketeers}`, hint: '' }] : []),
      ...(build?.soldiers ? [{ label: t('builds.create.crew.soldiers'), value: `${build.soldiers}`, hint: '' }] : []),
      ...(build?.mercenaries ? [{ label: t('builds.create.crew.mercenaries'), value: `${build.mercenaries}`, hint: '' }] : []),
    ],
    equipmentRows,
    upgrades,
    specialists,
    weapons: weaponGroups,
    inventoryGroups,
    notes: noteLines,
  }
}

export function createBuildPrintSvg(build, helpers = {}) {
  return createBuildPrintDocument(build, helpers).svg
}

export function buildPrintFileName(build, extension = 'png') {
  const base = sanitizeFileName(build?.build_name || 'build-sheet')
  return `${base}-build-sheet.${String(extension || 'png').replace(/[^a-z0-9]/gi, '')}`
}

function triggerDownload(blob, fileName) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1500)
}

export function createBuildPrintPreviewUrl(build, helpers = {}) {
  const { svg } = createBuildPrintDocument(build, helpers)
  const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
  return URL.createObjectURL(blob)
}

export function downloadBuildPrintSvg(build, helpers = {}) {
  const { svg } = createBuildPrintDocument(build, helpers)
  const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
  triggerDownload(blob, buildPrintFileName(build, 'svg'))
}

export async function downloadBuildPrintPng(build, helpers = {}) {
  const { svg, width, height } = createBuildPrintDocument(build, helpers)
  const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
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
    const pngBlob = await new Promise((resolve, reject) => {
      canvas.toBlob((result) => {
        if (result) resolve(result)
        else reject(new Error('Build image could not be encoded.'))
      }, 'image/png')
    })
    triggerDownload(pngBlob, buildPrintFileName(build, 'png'))
  } finally {
    URL.revokeObjectURL(url)
  }
}

export function openBuildPrintWindow(build, helpers = {}) {
  const { svg } = createBuildPrintDocument(build, helpers)
  const popup = window.open('', '_blank', 'noopener,noreferrer,width=1040,height=1440')
  if (!popup) throw new Error('Print preview could not be opened.')
  popup.document.write(`<!doctype html><html><head><title>${escapeXml(build?.build_name || 'Build')}</title><style>html,body{margin:0;background:#08111b;color:#f4f7fb;font-family:Inter,system-ui,sans-serif}body{display:grid;place-items:center;padding:24px}img{max-width:min(100%,1000px);height:auto;box-shadow:0 20px 60px rgba(0,0,0,.35);border-radius:20px}button{position:fixed;top:16px;right:16px;padding:10px 16px;border-radius:999px;border:1px solid rgba(241,184,91,.35);background:#101d2b;color:#f4f7fb;cursor:pointer}</style></head><body><button onclick="window.print()">Print</button><img alt="Build sheet" src="data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}" /></body></html>`)
  popup.document.close()
  return popup
}

export { createBuildPrintModel, createBuildPrintDocument }
