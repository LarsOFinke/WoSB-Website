<script setup>
import { ref } from 'vue'
import { useLocale } from '@/locales'
import StrategyCanvas from './StrategyCanvas.vue'
import StrategyLegend from './StrategyLegend.vue'
import '../styles/strategyPrint.css'

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  document: { type: Object, required: true },
  backgroundUrl: { type: String, default: '' },
  ships: { type: Array, default: () => [] },
  builds: { type: Array, default: () => [] },
  guides: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  mode: { type: String, default: 'select' },
  color: { type: String, default: '' },
  readOnly: { type: Boolean, default: false },
  backgroundSettings: { type: Object, default: () => ({}) },
})
defineEmits(['update:document', 'select', 'history'])

const { t } = useLocale()
const canvas = ref(null)

defineExpose({
  get element() { return canvas.value?.element || null },
})
</script>

<template>
  <section class="strategy-print-chart-page">
    <header class="strategy-print-summary">
      <p class="eyebrow">{{ t('strategyPlanner.eyebrow') }}</p>
      <h1>{{ title }}</h1>
      <p v-if="description">{{ description }}</p>
    </header>
    <StrategyCanvas
      ref="canvas" :document="document" :background-url="backgroundUrl" :ships="ships"
      :selected-id="selectedId" :mode="mode" :color="color" :read-only="readOnly"
      :background-settings="backgroundSettings"
      @update:document="$emit('update:document', $event)" @select="$emit('select', $event)"
      @history="$emit('history')"
    />
  </section>
  <slot name="after-canvas"></slot>
  <section class="strategy-print-legend-page">
    <header class="strategy-print-player-heading">
      <p class="eyebrow">{{ title }}</p>
      <h2>{{ t('strategyPlanner.playerList') }}</h2>
    </header>
    <StrategyLegend :document="document" :ships="ships" :builds="builds" :guides="guides" />
  </section>
</template>
