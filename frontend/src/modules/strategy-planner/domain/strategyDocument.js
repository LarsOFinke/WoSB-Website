export const STRATEGY_DOCUMENT_VERSION = 2
const LEGACY_STRATEGY_DOCUMENT_VERSION = 1
export const STRATEGY_COLORS = ['#f4c76b', '#ef6461', '#5cc8ff', '#65d68a', '#ffffff']
export const DEFAULT_BACKGROUND_SETTINGS = Object.freeze({
  fit: 'stretch', scale: 1, opacity: 0.82, brightness: 1, contrast: 1,
})
const STRATEGY_OBJECT_FIELDS = [
  'id', 'type', 'x', 'y', 'x2', 'y2', 'width', 'height', 'rotation', 'scale', 'color', 'text',
  'shipId', 'shipName', 'shipType', 'shipRate', 'playerName', 'buildId', 'guideId', 'formation', 'points',
]
const OBJECT_FIELD_ALIASES = {
  shipId: 'ship_id', shipName: 'ship_name', shipType: 'ship_type', shipRate: 'ship_rate',
  playerName: 'player_name', buildId: 'build_id', guideId: 'guide_id',
}
const NUMERIC_OBJECT_FIELDS = new Set(['shipId', 'shipRate', 'buildId', 'guideId'])

let sequence = 0

function objectId(type) {
  sequence += 1
  return `${type}-${Date.now().toString(36)}-${sequence.toString(36)}`
}

export function emptyStrategyDocument() {
  return { version: STRATEGY_DOCUMENT_VERSION, objects: [], background: { ...DEFAULT_BACKGROUND_SETTINGS } }
}

export function normalizeBackgroundSettings(value) {
  const source = value && typeof value === 'object' ? value : {}
  const fit = ['stretch', 'contain', 'cover'].includes(source.fit) ? source.fit : DEFAULT_BACKGROUND_SETTINGS.fit
  const clamp = (number, minimum, maximum, fallback) => {
    const parsed = Number(number)
    return Number.isFinite(parsed) ? Math.max(minimum, Math.min(maximum, parsed)) : fallback
  }
  return {
    fit,
    scale: clamp(source.scale, 0.5, 2, DEFAULT_BACKGROUND_SETTINGS.scale),
    opacity: clamp(source.opacity, 0.1, 1, DEFAULT_BACKGROUND_SETTINGS.opacity),
    brightness: clamp(source.brightness, 0.5, 1.5, DEFAULT_BACKGROUND_SETTINGS.brightness),
    contrast: clamp(source.contrast, 0.5, 2, DEFAULT_BACKGROUND_SETTINGS.contrast),
  }
}

export function parseStrategyDocument(value) {
  try {
    const parsed = typeof value === 'string' ? JSON.parse(value) : value
    if (![LEGACY_STRATEGY_DOCUMENT_VERSION, STRATEGY_DOCUMENT_VERSION].includes(parsed?.version) || !Array.isArray(parsed.objects)) return emptyStrategyDocument()
    return {
      version: STRATEGY_DOCUMENT_VERSION,
      background: normalizeBackgroundSettings(parsed.background),
      objects: parsed.objects.map((item) => {
        const normalized = { ...item, rotation: Number(item.rotation ?? 0), scale: Number(item.scale ?? 1) }
        if (parsed.version === LEGACY_STRATEGY_DOCUMENT_VERSION && normalized.type === 'formation' && normalized.formation === 'circle') {
          normalized.formation = 'oval'
        }
        for (const [field, alias] of Object.entries(OBJECT_FIELD_ALIASES)) {
          if (normalized[field] == null && normalized[alias] != null) {
            normalized[field] = NUMERIC_OBJECT_FIELDS.has(field) ? Number(normalized[alias]) : normalized[alias]
          }
          delete normalized[alias]
        }
        return normalized
      }),
    }
  } catch {
    return emptyStrategyDocument()
  }
}

export function serializeStrategyDocument(document) {
  const objects = Array.isArray(document?.objects) ? document.objects.map((object) => {
    const serialized = {}
    for (const field of STRATEGY_OBJECT_FIELDS) {
      const value = object?.[field] === undefined && OBJECT_FIELD_ALIASES[field]
        ? object?.[OBJECT_FIELD_ALIASES[field]] : object?.[field]
      if (value === undefined) continue
      serialized[field] = field === 'points' && Array.isArray(value) ? [...value] : value
    }
    return serialized
  }) : []
  return JSON.stringify({ version: STRATEGY_DOCUMENT_VERSION, background: normalizeBackgroundSettings(document?.background), objects })
}

export function invalidShipMarkers(document) {
  return (document?.objects || []).filter((object) => {
    if (object?.type !== 'ship') return false
    const shipId = Number(object.shipId ?? object.ship_id)
    return !Number.isSafeInteger(shipId) || shipId <= 0
  })
}

export function buildShipId(build) {
  return Number(build?.ship?.id ?? build?.shipId ?? build?.ship_id)
}

export function buildMatchesShip(build, shipId) {
  const expected = Number(shipId)
  return Number.isSafeInteger(expected) && expected > 0 && buildShipId(build) === expected
}

export function buildsForShip(builds, shipId) {
  return (builds || []).filter((build) => buildMatchesShip(build, shipId))
}

export function invalidBuildMarkers(document, builds) {
  const catalog = new Map((builds || []).map((build) => [Number(build.id), build]))
  return (document?.objects || []).filter((object) => {
    if (object?.type !== 'ship' || object.buildId == null || object.buildId === '') return false
    const build = catalog.get(Number(object.buildId))
    return !build || !buildMatchesShip(build, object.shipId)
  })
}

export function repairShipMarkerReferences(document, ships) {
  const catalog = ships || []
  return {
    ...document,
    objects: (document?.objects || []).map((object) => {
      if (object?.type !== 'ship' || Number(object.shipId) > 0) return object
      const name = String(object.shipName || '').trim().toLocaleLowerCase()
      let matches = name ? catalog.filter((ship) => String(ship.name).trim().toLocaleLowerCase() === name) : []
      if (matches.length !== 1 && object.shipType && object.shipRate) {
        matches = catalog.filter((ship) => ship.ship_type === object.shipType && Number(ship.rate) === Number(object.shipRate))
      }
      if (matches.length !== 1) return object
      const ship = matches[0]
      return { ...object, shipId: Number(ship.id), shipType: ship.ship_type, shipRate: Number(ship.rate) }
    }),
  }
}

export function createShipMarker(ship, options = {}) {
  if (!ship?.id) throw new Error('A ship is required for a ship marker.')
  return {
    id: objectId('ship'), type: 'ship', x: 0.5, y: 0.5, rotation: 0, scale: 1,
    color: options.color || STRATEGY_COLORS[0], shipId: Number(ship.id),
    shipName: String(options.shipName || '').trim() || ship.name,
    shipType: ship.ship_type,
    shipRate: Number(ship.rate),
    playerName: String(options.playerName || '').trim() || null,
    buildId: options.buildId ? Number(options.buildId) : null,
    guideId: options.guideId ? Number(options.guideId) : null,
  }
}

export function createLine(type = 'arrow', color = STRATEGY_COLORS[0]) {
  return { id: objectId(type), type, x: 0.3, y: 0.5, x2: 0.7, y2: 0.5, color, rotation: 0, scale: 1 }
}

export function createFormation(formation = 'line', color = STRATEGY_COLORS[2]) {
  return { id: objectId('formation'), type: 'formation', formation, x: 0.5, y: 0.5, width: 0.32, height: 0.24, rotation: 0, color, scale: 1 }
}

export function createText(text = 'Strategy note', color = '#ffffff') {
  return { id: objectId('text'), type: 'text', x: 0.5, y: 0.2, text, color, rotation: 0, scale: 1 }
}

export function createFreehand(points, color = STRATEGY_COLORS[0]) {
  return { id: objectId('freehand'), type: 'freehand', x: 0, y: 0, points, color, rotation: 0, scale: 1 }
}

export function snapshotStrategyObject(object) {
  return { ...object, points: Array.isArray(object.points) ? [...object.points] : object.points }
}

export function moveStrategyObject(object, dx, dy) {
  const clamp = (value) => Math.max(0, Math.min(1, value))
  const moved = { ...object, x: clamp(Number(object.x || 0) + dx), y: clamp(Number(object.y || 0) + dy) }
  if (object.x2 != null) moved.x2 = clamp(Number(object.x2) + dx)
  if (object.y2 != null) moved.y2 = clamp(Number(object.y2) + dy)
  if (Array.isArray(object.points)) {
    moved.points = object.points.map((point, index) => clamp(Number(point) + (index % 2 ? dy : dx)))
  }
  return moved
}

export function strategyShareUrl(publicId, locationObject = globalThis.location) {
  const origin = locationObject?.origin || 'http://localhost'
  return new URL(`/strategies/shared/${publicId}`, origin).toString()
}
