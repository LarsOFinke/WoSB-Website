<script setup>
import { useLocale } from '@/locales'
import StrategyTransformControls from './StrategyTransformControls.vue'

defineProps({ selectedObject: { type: Object, required: true }, sectionIndex: { type: String, default: '04' } })

const emit = defineEmits(['record-history'])
const { t } = useLocale()
</script>

<template>
  <details class="strategy-tool-section strategy-transform-section" open>
    <summary>
      <span class="strategy-section-index">{{ sectionIndex }}</span>
      <span><strong>{{ t('strategyPlanner.transform') }}</strong><small>{{ t('strategyPlanner.transformHint') }}</small></span>
    </summary>
    <div class="strategy-tool-section-body">
      <StrategyTransformControls :selected-object="selectedObject" @record-history="emit('record-history')" />
    </div>
  </details>
</template>
