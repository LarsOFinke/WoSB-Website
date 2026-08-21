<script setup>
import { ref, watch } from 'vue'
import { useLocale } from '@/locales'
import StrategySelectionSection from '../inspector/StrategySelectionSection.vue'
import StrategyTransformSection from '../inspector/StrategyTransformSection.vue'
import '../../styles/strategyInspector.css'

const props = defineProps({
  ships: { type: Array, required: true },
  guides: { type: Array, required: true },
  selectedObject: { type: Object, required: true },
  selectedBuilds: { type: Array, required: true },
  colors: { type: Array, required: true },
})

const emit = defineEmits([
  'update-selected-ship', 'record-history', 'delete-selected', 'close',
])
const { t } = useLocale()
const activeSection = ref('selection')

watch(() => props.selectedObject?.id, (selectedId) => {
  if (selectedId) activeSection.value = 'selection'
}, { immediate: true })

function setActiveSection(section, open) {
  if (open) activeSection.value = section
  else if (activeSection.value === section) activeSection.value = null
}
</script>

<template>
  <aside id="strategy-canvas-tools" class="strategy-tool-rail strategy-canvas-tools" :aria-label="t('strategyPlanner.objectTools')">
    <header class="strategy-canvas-tools-head">
      <div>
        <span class="strategy-tools-kicker">{{ t('strategyPlanner.objectTools') }}</span>
        <strong>{{ t('strategyPlanner.selectedObject') }}</strong>
      </div>
      <button type="button" class="strategy-canvas-tools-close" :aria-label="t('strategyPlanner.hideObjectTools')" @click="emit('close')">
        <span aria-hidden="true">×</span>
      </button>
    </header>
    <StrategySelectionSection
      :selected-object="selectedObject"
      :ships="ships"
      :guides="guides"
      :selected-builds="selectedBuilds"
      :colors="colors"
      :open="activeSection === 'selection'"
      section-index="01"
      @update-selected-ship="emit('update-selected-ship')"
      @record-history="emit('record-history')"
      @delete-selected="emit('delete-selected')"
      @toggle="setActiveSection('selection', $event)"
    />
    <StrategyTransformSection
      :selected-object="selectedObject"
      :open="activeSection === 'transform'"
      section-index="02"
      @record-history="emit('record-history')"
      @toggle="setActiveSection('transform', $event)"
    />
  </aside>
</template>
