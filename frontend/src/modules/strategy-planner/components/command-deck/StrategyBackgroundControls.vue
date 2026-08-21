<script setup>
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import { IMAGE_MIME_TYPES } from '@/modules/files/fileTypes'
import { useLocale } from '@/locales'

const props = defineProps({
  background: { type: Object, default: null },
  settings: { type: Object, required: true },
})
const emit = defineEmits(['use-background', 'update:settings', 'record-history'])
const { t } = useLocale()

function update(name, value) {
  emit('update:settings', { ...props.settings, [name]: value })
}
</script>

<template>
  <section class="strategy-setup-field strategy-background-panel">
    <div class="strategy-setup-field-heading">
      <span>03</span>
      <strong>{{ t('strategyPlanner.background') }}</strong>
      <small v-if="background" class="strategy-background-name">{{ background.original_name }}</small>
    </div>
    <FileUploadPanel usage-context="strategy" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="emit('use-background', $event)" />
    <details class="strategy-background-adjustments">
      <summary>{{ t('strategyPlanner.backgroundFit') }}</summary>
      <div class="strategy-background-controls">
        <fieldset class="strategy-background-fit">
          <legend>{{ t('strategyPlanner.backgroundFit') }}</legend>
          <button v-for="fit in ['stretch', 'contain', 'cover']" :key="fit" type="button" :class="{ active: settings.fit === fit }" :aria-pressed="settings.fit === fit" @click="update('fit', fit); emit('record-history')">{{ t(`strategyPlanner.backgroundFits.${fit}`) }}</button>
        </fieldset>
        <div class="strategy-transform-control"><label><span>{{ t('strategyPlanner.backgroundScale') }}</span><input :value="settings.scale" type="range" min="0.5" max="2" step="0.05" @input="update('scale', Number($event.target.value))" @change="emit('record-history')" /></label><span class="strategy-transform-value">{{ Number(settings.scale).toFixed(2) }}×</span></div>
        <div class="strategy-transform-control"><label><span>{{ t('strategyPlanner.backgroundOpacity') }}</span><input :value="settings.opacity" type="range" min="0.1" max="1" step="0.05" @input="update('opacity', Number($event.target.value))" @change="emit('record-history')" /></label><span class="strategy-transform-value">{{ Math.round(settings.opacity * 100) }}%</span></div>
        <div class="strategy-transform-control"><label><span>{{ t('strategyPlanner.backgroundBrightness') }}</span><input :value="settings.brightness" type="range" min="0.5" max="1.5" step="0.05" @input="update('brightness', Number($event.target.value))" @change="emit('record-history')" /></label><span class="strategy-transform-value">{{ Math.round(settings.brightness * 100) }}%</span></div>
        <div class="strategy-transform-control"><label><span>{{ t('strategyPlanner.backgroundContrast') }}</span><input :value="settings.contrast" type="range" min="0.5" max="2" step="0.05" @input="update('contrast', Number($event.target.value))" @change="emit('record-history')" /></label><span class="strategy-transform-value">{{ Math.round(settings.contrast * 100) }}%</span></div>
      </div>
    </details>
  </section>
</template>
