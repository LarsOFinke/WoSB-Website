<script setup>
import { useLocale } from '@/locales'
import StrategyObjectEditor from './StrategyObjectEditor.vue'

defineProps({
  selectedObject: { type: Object, required: true },
  ships: { type: Array, required: true },
  guides: { type: Array, required: true },
  selectedBuilds: { type: Array, required: true },
  colors: { type: Array, required: true },
  sectionIndex: { type: String, default: '03' },
})

const emit = defineEmits(['update-selected-ship', 'record-history', 'delete-selected'])
const { t } = useLocale()
</script>

<template>
  <details class="strategy-tool-section strategy-selection-section" open>
    <summary>
      <span class="strategy-section-index">{{ sectionIndex }}</span>
      <span><strong>{{ t('strategyPlanner.selectedObject') }}</strong><small>{{ selectedObject.type }}</small></span>
    </summary>
    <div class="strategy-tool-section-body">
      <StrategyObjectEditor
        :selected-object="selectedObject"
        :ships="ships"
        :guides="guides"
        :selected-builds="selectedBuilds"
        :colors="colors"
        @update-selected-ship="emit('update-selected-ship')"
        @record-history="emit('record-history')"
        @delete-selected="emit('delete-selected')"
      />
    </div>
  </details>
</template>
