<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { strategyCanvasPoint } from '../domain/canvasCoordinates.js'
import { createFreehand, moveStrategyObject, snapshotStrategyObject, STRATEGY_COLORS } from '../domain/strategyDocument.js'
import { strategyFormationPath, strategyLineGeometry, strategyObjectScale } from '../domain/strategyGeometry.js'

const props = defineProps({
  document: { type: Object, required: true },
  backgroundUrl: { type: String, default: '' },
  ships: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  mode: { type: String, default: 'select' },
  color: { type: String, default: () => STRATEGY_COLORS[0] },
  readOnly: { type: Boolean, default: false },
})
const emit = defineEmits(['update:document', 'select', 'history'])
const svgElement = ref(null)
const canvasHeight = ref(625)
const drag = shallowRef(null)
const activePointerId = ref(null)
const freehandPoints = ref([])
const shipMap = computed(() => new Map(props.ships.map((ship) => [Number(ship.id), ship])))
const viewBox = computed(() => `0 0 1000 ${canvasHeight.value}`)

function loadBackgroundSize() {
  if (!props.backgroundUrl || typeof Image === 'undefined') return
  const image = new Image()
  image.onload = () => {
    if (image.naturalWidth && image.naturalHeight) canvasHeight.value = Math.max(300, Math.min(1400, 1000 * image.naturalHeight / image.naturalWidth))
  }
  image.src = props.backgroundUrl
}

function point(event) {
  return strategyCanvasPoint(svgElement.value, event, canvasHeight.value)
}

function replaceObject(id, replacement, history = false) {
  emit('update:document', { ...props.document, objects: props.document.objects.map((item) => item.id === id ? replacement : item) })
  if (history) emit('history')
}

function startObjectDrag(event, object) {
  if (props.readOnly || props.mode !== 'select') return
  event.preventDefault()
  event.stopPropagation()
  emit('select', object.id)
  const start = point(event)
  activePointerId.value = event.pointerId
  drag.value = { id: object.id, start, original: snapshotStrategyObject(object) }
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function startCanvas(event) {
  if (props.readOnly) return
  if (props.mode !== 'freehand') {
    emit('select', '')
    return
  }
  const start = point(event)
  activePointerId.value = event.pointerId
  freehandPoints.value = [start.x, start.y]
  event.currentTarget.setPointerCapture?.(event.pointerId)
}

function movePointer(event) {
  if (activePointerId.value == null || event.pointerId !== activePointerId.value) return
  event.preventDefault()
  const current = point(event)
  if (drag.value) {
    replaceObject(drag.value.id, moveStrategyObject(drag.value.original,
      current.x - drag.value.start.x, current.y - drag.value.start.y))
  } else if (freehandPoints.value.length) {
    const points = freehandPoints.value
    const previousX = points.at(-2)
    const previousY = points.at(-1)
    if (Math.hypot(current.x - previousX, current.y - previousY) > 0.004) freehandPoints.value = [...points, current.x, current.y]
  }
}

function endPointer(event) {
  if (event && activePointerId.value != null && event.pointerId !== activePointerId.value) return
  if (drag.value) {
    drag.value = null
    emit('history')
  }
  if (freehandPoints.value.length >= 4) {
    emit('update:document', { ...props.document, objects: [...props.document.objects, createFreehand(freehandPoints.value, props.color)] })
    emit('history')
  }
  freehandPoints.value = []
  activePointerId.value = null
}

function keyMove(event, object) {
  if (props.readOnly || props.selectedId !== object.id || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return
  event.preventDefault()
  const step = event.shiftKey ? 0.02 : 0.005
  const dx = event.key === 'ArrowLeft' ? -step : event.key === 'ArrowRight' ? step : 0
  const dy = event.key === 'ArrowUp' ? -step : event.key === 'ArrowDown' ? step : 0
  replaceObject(object.id, moveStrategyObject(object, dx, dy), true)
}

function shipLabel(object) {
  const ship = shipMap.value.get(Number(object.shipId))
  return object.shipName || ship?.name || 'Ship'
}

function formationPath(object) {
  return strategyFormationPath(object, canvasHeight.value)
}

function freehandPath(points) {
  if (!points?.length) return ''
  return points.reduce((path, value, index) => {
    if (index % 2) return path
    return `${path}${index ? ' L' : 'M'} ${value * 1000} ${points[index + 1] * canvasHeight.value}`
  }, '')
}

function objectScale(object) {
  return strategyObjectScale(object)
}

function anchoredTransform(object) {
  let centerX = Number(object.x || 0)
  let centerY = Number(object.y || 0)
  if (object.x2 != null && object.y2 != null) {
    centerX = (Number(object.x) + Number(object.x2)) / 2
    centerY = (Number(object.y) + Number(object.y2)) / 2
  } else if (Array.isArray(object.points) && object.points.length >= 4) {
    const xs = object.points.filter((_, index) => index % 2 === 0)
    const ys = object.points.filter((_, index) => index % 2 === 1)
    centerX = (Math.min(...xs) + Math.max(...xs)) / 2
    centerY = (Math.min(...ys) + Math.max(...ys)) / 2
  }
  const x = centerX * 1000
  const y = centerY * canvasHeight.value
  return `translate(${x} ${y}) rotate(${Number(object.rotation || 0)}) scale(${objectScale(object)}) translate(${-x} ${-y})`
}

function lineGeometry(object) {
  return strategyLineGeometry(object, canvasHeight.value)
}

function lineTransform(object) {
  const geometry = lineGeometry(object)
  return `rotate(${Number(object.rotation || 0)} ${geometry.centerX} ${geometry.centerY})`
}

function arrowHeadTransform(object) {
  const geometry = lineGeometry(object)
  return `translate(${geometry.x2} ${geometry.y2}) rotate(${geometry.angle})`
}

watch(() => props.backgroundUrl, loadBackgroundSize, { immediate: true })
onMounted(() => {
  window.addEventListener('pointermove', movePointer, { passive: false })
  window.addEventListener('pointerup', endPointer)
  window.addEventListener('pointercancel', endPointer)
})
onBeforeUnmount(() => {
  window.removeEventListener('pointermove', movePointer)
  window.removeEventListener('pointerup', endPointer)
  window.removeEventListener('pointercancel', endPointer)
})
defineExpose({ element: svgElement })
</script>

<template>
  <div class="strategy-canvas-shell">
    <svg
      ref="svgElement"
      class="strategy-canvas"
      :class="{ 'is-drawing': mode === 'freehand' }"
      :viewBox="viewBox"
      role="img"
      aria-label="Strategy drawing canvas"
      @pointerdown="startCanvas"
    >
      <rect class="strategy-canvas-background" width="1000" :height="canvasHeight" />
      <image v-if="backgroundUrl" :href="backgroundUrl" width="1000" :height="canvasHeight" preserveAspectRatio="none" />
      <g class="strategy-overlay-layer">
        <template v-for="object in document.objects" :key="object.id">
          <g
            v-if="object.type === 'ship'"
            class="strategy-object strategy-ship-marker"
            :class="{ 'is-selected': selectedId === object.id }"
            :transform="`translate(${object.x * 1000} ${object.y * canvasHeight}) rotate(${object.rotation || 0}) scale(${objectScale(object)})`"
            :tabindex="readOnly ? undefined : 0"
            @pointerdown="startObjectDrag($event, object)"
            @keydown="keyMove($event, object)"
          >
            <circle class="strategy-marker-disc" r="18" :stroke="object.color" stroke-width="3" />
            <path d="M-12 5 L0-11 L12 5 L8 12 H-8 Z" :fill="object.color" opacity=".9" />
            <path class="strategy-marker-detail" d="M0-11 V10 M-8 3 H8" stroke-width="2" />
            <text y="34" text-anchor="middle" class="strategy-marker-title">{{ shipLabel(object) }}</text>
            <text v-if="object.playerName" y="51" text-anchor="middle" class="strategy-marker-player">{{ object.playerName }}</text>
          </g>
          <g
            v-else-if="object.type === 'line' || object.type === 'arrow'"
            class="strategy-object strategy-line"
            :class="{ 'is-selected': selectedId === object.id }"
            :transform="lineTransform(object)"
            tabindex="0" @pointerdown="startObjectDrag($event, object)" @keydown="keyMove($event, object)"
          >
            <line
              :x1="lineGeometry(object).x1" :y1="lineGeometry(object).y1"
              :x2="lineGeometry(object).x2" :y2="lineGeometry(object).y2"
              :stroke="object.color" stroke-width="7" stroke-linecap="round"
            />
            <path
              v-if="object.type === 'arrow'" class="strategy-arrow-head"
              d="M 5 0 L -30 -17 L -22 0 L -30 17 Z" :fill="object.color"
              :transform="arrowHeadTransform(object)"
            />
          </g>
          <g
            v-else-if="object.type === 'formation'"
            class="strategy-object strategy-formation" :class="{ 'is-selected': selectedId === object.id }"
            :transform="`translate(${object.x * 1000} ${object.y * canvasHeight}) rotate(${object.rotation || 0})`"
            tabindex="0" @pointerdown="startObjectDrag($event, object)" @keydown="keyMove($event, object)"
          >
            <path :d="formationPath(object)" fill="none" :stroke="object.color" stroke-width="7" stroke-dasharray="18 11" />
            <circle r="10" :fill="object.color" />
          </g>
          <text
            v-else-if="object.type === 'text'"
            class="strategy-object strategy-text" :class="{ 'is-selected': selectedId === object.id }"
            x="0" y="0" :fill="object.color"
            :transform="`translate(${object.x * 1000} ${object.y * canvasHeight}) rotate(${object.rotation || 0}) scale(${objectScale(object)})`"
            text-anchor="middle" tabindex="0" @pointerdown="startObjectDrag($event, object)" @keydown="keyMove($event, object)"
          >{{ object.text }}</text>
          <path
            v-else-if="object.type === 'freehand'"
            class="strategy-object strategy-freehand" :class="{ 'is-selected': selectedId === object.id }"
            :d="freehandPath(object.points)" fill="none" :stroke="object.color" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"
            :transform="anchoredTransform(object)"
            tabindex="0" @pointerdown="startObjectDrag($event, object)" @keydown="keyMove($event, object)"
          />
        </template>
        <path v-if="freehandPoints.length" :d="freehandPath(freehandPoints)" fill="none" :stroke="color" stroke-width="6" stroke-linecap="round" />
      </g>
    </svg>
  </div>
</template>
