import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocale } from '@/locales'
import { listBuilds } from '@/modules/builds/api/builds'
import { absoluteFileUrl } from '@/modules/files/api/files'
import { listGuides } from '@/modules/guides/api/guides'
import { listShips } from '@/modules/ships/api/ships'
import { createStrategy, getStrategy, publishStrategy, unpublishStrategy, updateStrategy } from '../api/strategies.js'
import {
  createFormation, createLine, createShipMarker, createText, emptyStrategyDocument,
  buildMatchesShip, buildsForShip, invalidBuildMarkers, invalidShipMarkers,
  parseStrategyDocument, repairShipMarkerReferences, serializeStrategyDocument,
  strategyShareUrl, STRATEGY_COLORS,
} from '../domain/strategyDocument.js'
import { downloadStrategySvg } from '../strategySvgExport.js'

export function useStrategyPlannerPage() {
  const route = useRoute()
  const router = useRouter()
  const { t } = useLocale()
  const strategy = ref({ title: '', description: '', is_published: false })
  const background = ref(null)
  const document = ref(emptyStrategyDocument())
  const ships = ref([])
  const builds = ref([])
  const guides = ref([])
  const selectedId = ref('')
  const mode = ref('select')
  const color = ref(STRATEGY_COLORS[0])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const status = ref('')
  const canvas = ref(null)
  const marker = reactive({ shipId: '', shipName: '', playerName: '', buildId: '', guideId: '' })
  const formation = ref('line')
  const textValue = ref('Strategy note')
  const history = ref([serializeStrategyDocument(document.value)])
  const historyIndex = ref(0)

  const strategyId = computed(() => route.params.id ? Number(route.params.id) : null)
  const isEditing = computed(() => Number.isInteger(strategyId.value) && strategyId.value > 0)
  const backgroundUrl = computed(() => absoluteFileUrl(background.value?.public_url || ''))
  const selectedObject = computed(() => document.value.objects.find((item) => item.id === selectedId.value) || null)
  const markerBuilds = computed(() => buildsForShip(builds.value, marker.shipId))
  const selectedBuilds = computed(() => buildsForShip(builds.value, selectedObject.value?.shipId))
  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)
  const shareUrl = computed(() => strategy.value?.public_id ? strategyShareUrl(strategy.value.public_id) : '')

  function resetHistory() {
    history.value = [serializeStrategyDocument(document.value)]
    historyIndex.value = 0
  }

  function recordHistory() {
    const snapshot = serializeStrategyDocument(document.value)
    if (history.value[historyIndex.value] === snapshot) return
    history.value = [...history.value.slice(0, historyIndex.value + 1), snapshot].slice(-60)
    historyIndex.value = history.value.length - 1
  }

  function setDocument(value) { document.value = value }
  function commitDocument(value) { document.value = value; recordHistory() }
  function undo() {
    if (!canUndo.value) return
    historyIndex.value -= 1
    document.value = parseStrategyDocument(history.value[historyIndex.value])
  }
  function redo() {
    if (!canRedo.value) return
    historyIndex.value += 1
    document.value = parseStrategyDocument(history.value[historyIndex.value])
  }

  function addObject(object) {
    commitDocument({ ...document.value, objects: [...document.value.objects, object] })
    selectedId.value = object.id
    mode.value = 'select'
  }

  function addShip() {
    const ship = ships.value.find((item) => Number(item.id) === Number(marker.shipId))
    if (!ship) { error.value = t('strategyPlanner.missingShip'); return }
    const build = builds.value.find((item) => Number(item.id) === Number(marker.buildId))
    if (marker.buildId && !buildMatchesShip(build, ship.id)) {
      error.value = t('strategyPlanner.invalidBuildReference')
      return
    }
    addObject(createShipMarker(ship, { ...marker, color: color.value }))
  }

  function updateMarkerShipReference() {
    const build = builds.value.find((item) => Number(item.id) === Number(marker.buildId))
    if (marker.buildId && !buildMatchesShip(build, marker.shipId)) marker.buildId = ''
  }

  function updateSelectedShipReference() {
    if (selectedObject.value?.type !== 'ship') return
    const ship = ships.value.find((item) => Number(item.id) === Number(selectedObject.value.shipId))
    if (!ship) return
    selectedObject.value.shipId = Number(ship.id)
    selectedObject.value.shipName ||= ship.name
    selectedObject.value.shipType = ship.ship_type
    selectedObject.value.shipRate = Number(ship.rate)
    const build = builds.value.find((item) => Number(item.id) === Number(selectedObject.value.buildId))
    if (selectedObject.value.buildId && !buildMatchesShip(build, ship.id)) selectedObject.value.buildId = null
    recordHistory()
  }

  function addLine(type) { addObject(createLine(type, color.value)) }
  function addFormation() { addObject(createFormation(formation.value, color.value)) }
  function addText() { addObject(createText(textValue.value.trim() || t('strategyPlanner.text'), color.value)) }
  function deleteSelected() {
    if (!selectedId.value) return
    commitDocument({ ...document.value, objects: document.value.objects.filter((item) => item.id !== selectedId.value) })
    selectedId.value = ''
  }

  function useBackground(file) { background.value = file }

  async function loadCatalogs() {
    try {
      const [shipRows, buildPage, guideRows] = await Promise.all([listShips(), listBuilds('', '', '', 100, 0), listGuides('', '', 100, 0)])
      ships.value = shipRows || []
      builds.value = buildPage.items || []
      guides.value = guideRows || []
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.catalogError')
    }
  }

  function applyStrategy(value) {
    strategy.value = value
    background.value = value.background_file
    document.value = repairShipMarkerReferences(parseStrategyDocument(value.overlay_json), ships.value)
    resetHistory()
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      await loadCatalogs()
      if (isEditing.value) applyStrategy(await getStrategy(strategyId.value))
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.loadError')
    } finally {
      loading.value = false
    }
  }

  async function save() {
    if (!background.value?.id) { error.value = t('strategyPlanner.missingBackground'); return }
    document.value = repairShipMarkerReferences(document.value, ships.value)
    if (invalidShipMarkers(document.value).length) {
      error.value = t('strategyPlanner.invalidShipReference')
      return
    }
    if (invalidBuildMarkers(document.value, builds.value).length) {
      error.value = t('strategyPlanner.invalidBuildReference')
      return
    }
    const title = String(strategy.value?.title || '').trim()
    if (!title) return
    saving.value = true
    error.value = ''
    status.value = ''
    try {
      const payload = {
        title,
        description: strategy.value?.description || null,
        background_file_id: Number(background.value.id),
        overlay_json: serializeStrategyDocument(document.value),
      }
      const saved = isEditing.value ? await updateStrategy(strategyId.value, payload) : await createStrategy(payload)
      applyStrategy(saved)
      status.value = t('strategyPlanner.saved')
      if (!isEditing.value) await router.replace(`/strategies/${saved.id}/edit`)
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.saveError')
    } finally {
      saving.value = false
    }
  }

  async function togglePublication() {
    if (!strategy.value?.id) { await save(); if (!strategy.value?.id) return }
    try {
      applyStrategy(strategy.value.is_published ? await unpublishStrategy(strategy.value.id) : await publishStrategy(strategy.value.id))
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.shareError')
    }
  }

  async function copyShareLink() {
    if (!shareUrl.value) return
    await navigator.clipboard.writeText(shareUrl.value)
    status.value = t('strategyPlanner.copied')
  }

  async function downloadSvg() {
    const source = canvas.value?.element
    if (!source) return
    error.value = ''
    try {
      await downloadStrategySvg(source, backgroundUrl.value, strategy.value?.title)
    } catch (exception) {
      error.value = exception.message || t('strategyPlanner.exportError')
    }
  }

  function printStrategy() { window.print() }

  onMounted(load)
  return {
    t, router, strategy, background, document, ships, builds, guides, selectedId, selectedObject,
    markerBuilds, selectedBuilds,
    mode, color, marker, formation, textValue, loading, saving, error, status, canvas,
    isEditing, backgroundUrl, canUndo, canRedo, shareUrl, STRATEGY_COLORS,
    setDocument, recordHistory, undo, redo, addShip, updateMarkerShipReference, updateSelectedShipReference,
    addLine, addFormation, addText,
    deleteSelected, useBackground, save, togglePublication, copyShareLink, downloadSvg, printStrategy,
  }
}
