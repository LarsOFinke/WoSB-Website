<script setup>
import { useLocale } from '@/locales'
import StrategyTransformControls from './StrategyTransformControls.vue'

defineProps({ open: { type: Boolean, default: true }, selectedObject: { type: Object, required: true }, sectionIndex: { type: String, default: '04' } })

const emit = defineEmits(['record-history', 'toggle'])
const { t } = useLocale()
</script>

<template>
  <details class="strategy-tool-section strategy-transform-section" :open="open" @toggle="emit('toggle', $event.target.open)">
    <summary>
      <span class="strategy-section-index">{{ sectionIndex }}</span>
      <span><strong>{{ t('strategyPlanner.transform') }}</strong><small>{{ t('strategyPlanner.transformHint') }}</small></span>
    </summary>
    <div class="strategy-tool-section-body">
      <StrategyTransformControls :selected-object="selectedObject" @record-history="emit('record-history')" />
    </div>
  </details>
</template>
