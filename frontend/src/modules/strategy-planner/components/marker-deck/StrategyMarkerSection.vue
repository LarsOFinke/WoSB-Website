<script setup>
import { useLocale } from '@/locales'
import StrategyMarkerCreator from './StrategyMarkerCreator.vue'

defineProps({
  marker: { type: Object, required: true },
  ships: { type: Array, required: true },
  guides: { type: Array, required: true },
  markerBuilds: { type: Array, required: true },
  sectionIndex: { type: String, default: '01' },
})

const emit = defineEmits(['update-marker-ship', 'add-ship'])
const { t } = useLocale()
</script>

<template>
  <details class="strategy-tool-section" open>
    <summary>
      <span class="strategy-section-index">{{ sectionIndex }}</span>
      <span><strong>{{ t('strategyPlanner.marker') }}</strong><small>{{ t('strategyPlanner.addMarker') }}</small></span>
    </summary>
    <div class="strategy-tool-section-body">
      <StrategyMarkerCreator
        :marker="marker"
        :ships="ships"
        :guides="guides"
        :marker-builds="markerBuilds"
        @update-marker-ship="emit('update-marker-ship')"
        @add-ship="emit('add-ship')"
      />
    </div>
  </details>
</template>
