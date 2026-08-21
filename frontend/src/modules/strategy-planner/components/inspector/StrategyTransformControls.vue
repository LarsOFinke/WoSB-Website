<script setup>
import { useLocale } from '@/locales'
defineProps({ selectedObject: { type: Object, required: true } })
const emit = defineEmits(['record-history'])
const { t } = useLocale()
</script>
<template>
  <section class="strategy-panel strategy-transform-panel">
    <div class="strategy-transform-control"><label><span>{{ t('strategyPlanner.scale') }}</span><input v-model.number="selectedObject.scale" type="range" min="0.25" max="4" step="0.05" @change="emit('record-history')" /></label><span class="strategy-transform-value">{{ Number(selectedObject.scale || 1).toFixed(2) }}×</span></div>
    <div v-if="selectedObject.rotation != null" class="strategy-transform-control"><label><span>{{ t('strategyPlanner.rotation') }}</span><input v-model.number="selectedObject.rotation" type="range" min="-180" max="180" @change="emit('record-history')" /></label><span class="strategy-transform-value">{{ Number(selectedObject.rotation || 0) }}°</span></div>
  </section>
</template>
