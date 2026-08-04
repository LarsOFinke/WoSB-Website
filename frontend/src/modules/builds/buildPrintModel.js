import { buildShareUrl } from './shareBuild.js'
import { CORE_BUILD_STAT_KEYS, formatStatValue } from './domain/buildStatPresentation.js'
import { resolvePrintUrl } from '../../shared/printing/printDocument.js'

function listLabel(slot, labeler, { includeQuantity = true } = {}) {
  if (!slot) return ''
  if (typeof slot === 'string') return labeler(slot)
  if (!slot.item) return ''
  const quantity = Number(slot.quantity || 1)
  return `${labeler(slot.item)}${includeQuantity && quantity > 1 ? ` ×${quantity}` : ''}`
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

export function wrapText(text, maxChars = 58) {
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

export function createBuildPrintModel(build, helpers = {}) {
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
  ].filter(Boolean).map((name) => ({ name, value: optionLabel(name), iconHref: optionImage('upgrade', name) })), 8)
  const upgrades = upgradeRows.map((row) => row.value)
  const weapons = [
    ['front', build?.front_weapon_slots], ['port', build?.port_weapon_slots],
    ['starboard', build?.starboard_weapon_slots], ['rear', build?.rear_weapon_slots],
    ['mortar', build?.mortar_weapon_slots], ['special', build?.special_weapon_slots],
  ].map(([key, slots]) => {
    const items = cleanEntries((slots || []).map((slot) => {
      const name = rawSlotItem(slot)
      return { name, value: listLabel(slot, optionLabel), iconHref: optionImage('weapon', name) }
    }), 4)
    return { key, label: t(`builds.detail.weapons.${key}`), items, lines: items.map((item) => item.value) }
  }).filter((group) => group.lines.length)

  const allSpecialistRows = cleanEntries((build?.special_crew_slots || []).map((slot) => {
    const name = rawSlotItem(slot)
    return { name, value: listLabel(slot, optionLabel), iconHref: optionImage('special_crew', name) }
  }), 5)
  const gingerSpecialistRow = allSpecialistRows.find((row) => row.name === 'Ginger') || null
  const specialistRows = allSpecialistRows.filter((row) => row !== gingerSpecialistRow)
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
      return { name, value: listLabel(slot, optionLabel, { includeQuantity }), iconHref: optionImage(iconKey, name) }
    }), 6)
    return { iconKey, title, items, lines: items.map((item) => item.value) }
  }).filter((group) => group.lines.length)
  const classificationLabels = (build?.classification_tags || []).map((value) => {
    const path = `discovery.builds.tags.${value}.label`
    const translated = t(path)
    return translated === path ? value.replaceAll('_', ' ') : translated
  })

  return {
    t, optionLabel, optionImage, shareUrl,
    buildName: build?.build_name || t('builds.print.fallbackTitle'),
    buildType: buildTypeLabel(build?.build_type, t),
    shipName: build?.ship?.name || '—',
    shipRate: build?.ship?.rate || '—',
    shipType: build?.ship?.ship_type || '—',
    generatedAt: new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(build?.updated_at || build?.created_at || 0)),
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
    specialists: specialistRows.map((row) => row.value),
    specialistRows,
    gingerSpecialist: gingerSpecialistRow?.value || '',
    gingerSpecialistRow,
    weapons,
    inventoryGroups,
    notes: build?.details ? wrapText(build.details, 112) : [],
  }
}
