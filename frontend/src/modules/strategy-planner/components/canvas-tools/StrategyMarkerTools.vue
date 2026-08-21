<script setup>
import { useLocale } from '@/locales'
import StrategyMarkerSection from '../marker-deck/StrategyMarkerSection.vue'
import '../../styles/strategyInspector.css'

defineProps({
  marker: { type: Object, required: true },
  ships: { type: Array, required: true },
  guides: { type: Array, required: true },
  markerBuilds: { type: Array, required: true },
})

const emit = defineEmits(['update-marker-ship', 'add-ship', 'close'])
const { t } = useLocale()
</script>

<template>
  <aside id="strategy-marker-tools" class="strategy-tool-rail strategy-marker-tools" :aria-label="t('strategyPlanner.addMarker')">
    <header class="strategy-canvas-tools-head">
      <div>
        <span class="strategy-tools-kicker">{{ t('strategyPlanner.marker') }}</span>
        <strong>{{ t('strategyPlanner.addMarker') }}</strong>
      </div>
      <button type="button" class="strategy-canvas-tools-close" :aria-label="t('strategyPlanner.hideMarkerTools')" @click="emit('close')">
        <span aria-hidden="true">×</span>
      </button>
    </header>
    <StrategyMarkerSection
      :marker="marker"
      :ships="ships"
      :guides="guides"
      :marker-builds="markerBuilds"
      section-index="01"
      @update-marker-ship="emit('update-marker-ship')"
      @add-ship="emit('add-ship')"
    />
  </aside>
</template>
