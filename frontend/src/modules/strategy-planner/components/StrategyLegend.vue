<script setup>
import { computed } from 'vue'
import { useLocale } from '@/locales'
import '../styles/strategyLegend.css'

const props = defineProps({
  document: { type: Object, required: true },
  ships: { type: Array, default: () => [] },
  builds: { type: Array, default: () => [] },
  guides: { type: Array, default: () => [] },
})
const { t } = useLocale()
const shipMap = computed(() => new Map(props.ships.map((ship) => [Number(ship.id), ship])))
const buildMap = computed(() => new Map(props.builds.map((build) => [Number(build.id), build])))
const guideMap = computed(() => new Map(props.guides.map((guide) => [Number(guide.id), guide])))
const markers = computed(() => props.document.objects.filter((object) => object.type === 'ship'))

function markerName(marker) {
  return marker.shipName || shipMap.value.get(Number(marker.shipId))?.name || t('strategyPlanner.ship')
}

function markerClass(marker) {
  const ship = shipMap.value.get(Number(marker.shipId))
  return `${ship?.ship_type || marker.shipType || t('strategyPlanner.ship')} · ${t('common.rate')} ${ship?.rate || marker.shipRate || '—'}`
}

function buildName(marker) {
  return buildMap.value.get(Number(marker.buildId))?.build_name || `#${marker.buildId}`
}

function guideName(marker) {
  return guideMap.value.get(Number(marker.guideId))?.title || `#${marker.guideId}`
}
</script>

<template>
  <section v-if="markers.length" class="strategy-legend" aria-labelledby="strategy-legend-title">
    <header class="strategy-legend-head">
      <h2 id="strategy-legend-title">{{ t('strategyPlanner.legend') }}</h2>
      <span>{{ markers.length }}</span>
    </header>
    <div class="strategy-legend-grid">
      <article v-for="marker in markers" :key="`legend-${marker.id}`" class="strategy-legend-entry">
        <span class="strategy-legend-symbol" :style="{ '--strategy-color': marker.color }" aria-hidden="true"></span>
        <div class="strategy-legend-copy">
          <strong>{{ markerName(marker) }}</strong>
          <span>{{ markerClass(marker) }}</span>
          <span v-if="marker.playerName">{{ marker.playerName }}</span>
          <div v-if="marker.buildId || marker.guideId" class="strategy-legend-links">
            <RouterLink v-if="marker.buildId" :to="`/builds/${marker.buildId}`">{{ t('strategyPlanner.build') }}: {{ buildName(marker) }}</RouterLink>
            <RouterLink v-if="marker.guideId" :to="`/guides/${marker.guideId}`">{{ t('strategyPlanner.guide') }}: {{ guideName(marker) }}</RouterLink>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
