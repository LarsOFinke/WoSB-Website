import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import {
  buildMatchesShip,
  buildsForShip,
  createFormation,
  createLine,
  createShipMarker,
  emptyStrategyDocument,
  invalidShipMarkers,
  invalidBuildMarkers,
  moveStrategyObject,
  parseStrategyDocument,
  repairShipMarkerReferences,
  serializeStrategyDocument,
  snapshotStrategyObject,
  strategyShareUrl,
  STRATEGY_DOCUMENT_VERSION,
} from '../src/modules/strategy-planner/domain/strategyDocument.js'
import { strategyCanvasPoint } from '../src/modules/strategy-planner/domain/canvasCoordinates.js'
import { strategyFormationPath, strategyLineGeometry } from '../src/modules/strategy-planner/domain/strategyGeometry.js'

const toolbarSource = await readFile(new URL('../src/modules/strategy-planner/components/StrategyToolbar.vue', import.meta.url), 'utf8')
const inspectorSource = await readFile(new URL('../src/modules/strategy-planner/components/StrategyInspector.vue', import.meta.url), 'utf8')
const canvasSource = await readFile(new URL('../src/modules/strategy-planner/components/StrategyCanvas.vue', import.meta.url), 'utf8')
const plannerPageSource = await readFile(new URL('../src/modules/strategy-planner/pages/StrategyPlannerPage.vue', import.meta.url), 'utf8')

test('strategy tools are grouped into independently collapsible command and inspector sections', () => {
  assert.equal(toolbarSource.match(/<details\b/g)?.length, 4)
  assert.equal(inspectorSource.match(/<details\b/g)?.length, 5)
  assert.match(toolbarSource, /strategy-command-sections/)
  assert.match(inspectorSource, /strategy-selection-section/)
  assert.match(inspectorSource, /strategy-transform-section/)
  assert.doesNotMatch(inspectorSource.match(/strategy-selection-section[\s\S]*?<\/details>/)?.[0] || '', /type="range"/)
  assert.match(inspectorSource, /strategy-text-color-field/)
  assert.match(plannerPageSource, /class="strategy-tools-toggle"/)
  assert.match(plannerPageSource, /aria-controls="strategy-tool-rail"/)
  assert.match(plannerPageSource, /:aria-expanded="toolsOpen"/)
})

test('strategy ship markers require website ships while player names remain optional', () => {
  assert.throws(() => createShipMarker(null), /ship is required/i)
  const marker = createShipMarker({ id: 17, name: 'Leopard', ship_type: 'Frigate', rate: 3 }, { buildId: 42, guideId: 8 })
  assert.equal(marker.shipId, 17)
  assert.equal(marker.shipName, 'Leopard')
  assert.equal(marker.shipType, 'Frigate')
  assert.equal(marker.shipRate, 3)
  assert.equal(marker.playerName, null)
  assert.equal(marker.buildId, 42)
  assert.equal(marker.guideId, 8)
})

test('strategy documents preserve the drawing layer independently', () => {
  const document = emptyStrategyDocument()
  document.objects.push({ ...createFormation('wedge'), vueOnlyState: { selected: true } })
  const serialized = serializeStrategyDocument(document)
  const restored = parseStrategyDocument(serialized)
  assert.equal(restored.version, STRATEGY_DOCUMENT_VERSION)
  assert.equal(restored.objects[0].formation, 'wedge')
  assert.equal(serialized.includes('vueOnlyState'), false)
})

test('legacy oval formations migrate without changing shape while new circles stay round', () => {
  const legacy = parseStrategyDocument('{"version":1,"objects":[{"id":"formation-1","type":"formation","formation":"circle","x":0.5,"y":0.5,"width":0.32,"height":0.24}]}')
  const current = parseStrategyDocument('{"version":2,"objects":[{"id":"formation-2","type":"formation","formation":"circle","x":0.5,"y":0.5,"width":0.32,"height":0.24}]}')
  assert.equal(legacy.objects[0].formation, 'oval')
  assert.equal(current.objects[0].formation, 'circle')
  assert.match(strategyFormationPath(legacy.objects[0], 625), /A 160 75/)
  assert.match(strategyFormationPath(current.objects[0], 625), /A 75 75/)
})

test('legacy reference names are normalized and invalid ship markers are found before saving', () => {
  const restored = parseStrategyDocument('{"version":1,"objects":[{"id":"ship-1","type":"ship","x":0.5,"y":0.5,"ship_id":17,"ship_name":"Leopard","ship_type":"Frigate","ship_rate":3,"player_name":"Captain","build_id":42}]}')
  assert.equal(restored.objects[0].shipId, 17)
  assert.equal(restored.objects[0].shipName, 'Leopard')
  assert.equal(restored.objects[0].playerName, 'Captain')
  assert.equal(restored.objects[0].buildId, 42)
  assert.equal(invalidShipMarkers(restored).length, 0)
  assert.equal(invalidShipMarkers({ version: 1, objects: [{ id: 'ship-2', type: 'ship', x: 0.5, y: 0.5 }] }).length, 1)
  assert.equal(serializeStrategyDocument(restored).includes('ship_id'), false)
})

test('legacy ship markers are repaired only from an unambiguous catalog match', () => {
  const legacy = { version: 1, objects: [{ id: 'ship-1', type: 'ship', x: 0.5, y: 0.5, shipName: 'Leopard', shipType: 'Frigate', shipRate: 3 }] }
  const repaired = repairShipMarkerReferences(legacy, [
    { id: 17, name: 'Leopard', ship_type: 'Frigate', rate: 3 },
    { id: 18, name: 'Defiance', ship_type: 'Frigate', rate: 3 },
  ])
  assert.equal(repaired.objects[0].shipId, 17)
  assert.equal(invalidShipMarkers(repaired).length, 0)
})

test('moving strategy objects keeps normalized coordinates in bounds', () => {
  const moved = moveStrategyObject({ id: 'line-1', type: 'line', x: 0.9, y: 0.1, x2: 1, y2: 0.2 }, 0.5, -0.5)
  assert.deepEqual({ x: moved.x, y: moved.y, x2: moved.x2, y2: moved.y2 }, { x: 1, y: 0, x2: 1, y2: 0 })
})

test('strategy objects are scalable and reactive proxies can be snapshotted for dragging', () => {
  const line = createLine()
  const reactiveLikeObject = new Proxy({ ...line, points: [0.1, 0.2, 0.3, 0.4] }, {})
  const snapshot = snapshotStrategyObject(reactiveLikeObject)

  assert.equal(line.scale, 1)
  assert.equal(line.rotation, 0)
  assert.notEqual(snapshot.points, reactiveLikeObject.points)
  assert.deepEqual(snapshot.points, reactiveLikeObject.points)
  const legacy = parseStrategyDocument('{"version":1,"objects":[{"id":"legacy","type":"line","x":0.2,"y":0.5,"x2":0.8,"y2":0.5}]}').objects[0]
  assert.equal(legacy.scale, 1)
  assert.equal(legacy.rotation, 0)
})

test('line scale changes its extent without shrinking arrowhead and stroke geometry', () => {
  const geometry = strategyLineGeometry({ x: 0.3, y: 0.5, x2: 0.7, y2: 0.5, scale: 0.25 }, 625)
  assert.deepEqual({ x1: geometry.x1, x2: geometry.x2, angle: geometry.angle }, { x1: 450, x2: 550, angle: 0 })
  assert.match(canvasSource, /d="M 5 0 L -30 -17 L -22 0 L -30 17 Z"/)
  assert.match(canvasSource, /stroke-width="7"/)
  assert.doesNotMatch(canvasSource, /lineTransform\(object\)[\s\S]{0,120}scale/)
})

test('strategy sharing uses the non-sequential public identifier', () => {
  assert.equal(strategyShareUrl('8dbca839-49eb-49cc-a732-118d17802dcb', { origin: 'https://fleet.example' }),
    'https://fleet.example/strategies/shared/8dbca839-49eb-49cc-a732-118d17802dcb')
})

test('canvas coordinates follow the rendered SVG transform instead of its letterboxed CSS bounds', () => {
  const svg = {
    createSVGPoint: () => ({
      x: 0,
      y: 0,
      matrixTransform(transform) { return transform.map(this.x, this.y) },
    }),
    getScreenCTM: () => ({
      inverse: () => ({ map: (x, y) => ({ x: (x - 100) / 2, y: (y - 250) / 2 }) }),
    }),
    getBoundingClientRect: () => ({ left: 100, top: 0, width: 2000, height: 1000 }),
  }

  assert.deepEqual(strategyCanvasPoint(svg, { clientX: 600, clientY: 500 }, 500), { x: 0.25, y: 0.25 })
})

test('strategy build references are limited to builds for the marker ship', () => {
  const leopard = { id: 21, build_name: 'Leopard broadside', ship: { id: 11, name: 'Leopard' } }
  const brig = { id: 22, build_name: 'Brig pursuit', ship: { id: 12, name: 'Brig' } }
  assert.equal(buildMatchesShip(leopard, 11), true)
  assert.deepEqual(buildsForShip([leopard, brig], 11), [leopard])
  assert.equal(invalidBuildMarkers({
    version: 1,
    objects: [{ id: 'ship-1', type: 'ship', shipId: 11, buildId: 22 }],
  }, [leopard, brig]).length, 1)
  assert.equal(invalidBuildMarkers({
    version: 1,
    objects: [{ id: 'ship-1', type: 'ship', shipId: 11, buildId: 21 }],
  }, [leopard, brig]).length, 0)
})
