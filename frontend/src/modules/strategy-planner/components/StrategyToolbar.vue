<script setup>
import { useLocale } from '@/locales'

const { t } = useLocale()

defineProps({
  mode: { type: String, required: true },
  color: { type: String, required: true },
  colors: { type: Array, required: true },
  formation: { type: String, required: true },
  textValue: { type: String, required: true },
  canUndo: { type: Boolean, default: false },
  canRedo: { type: Boolean, default: false },
})

defineEmits([
  'update:mode', 'update:color', 'update:formation', 'update:textValue',
  'add-line', 'add-formation', 'add-text', 'undo', 'redo',
])
</script>

<template>
  <nav class="strategy-command-bar" :aria-label="t('strategyPlanner.objects')">
    <div class="strategy-command-group strategy-mode-commands">
      <button type="button" :class="{ active: mode === 'select' }" :aria-pressed="mode === 'select'" @click="$emit('update:mode', 'select')">{{ t('strategyPlanner.select') }}</button>
      <button type="button" :class="{ active: mode === 'freehand' }" :aria-pressed="mode === 'freehand'" @click="$emit('update:mode', 'freehand')">{{ t('strategyPlanner.freehand') }}</button>
      <button type="button" @click="$emit('add-line', 'line')">{{ t('strategyPlanner.line') }}</button>
      <button type="button" @click="$emit('add-line', 'arrow')">{{ t('strategyPlanner.arrow') }}</button>
    </div>

    <div class="strategy-command-group strategy-formation-command">
      <label>
        <span class="sr-only">{{ t('strategyPlanner.formationType') }}</span>
        <select :value="formation" @change="$emit('update:formation', $event.target.value)">
          <option v-for="name in ['line', 'circle', 'wedge', 'column', 'box']" :key="name" :value="name">{{ t(`strategyPlanner.formations.${name}`) }}</option>
        </select>
      </label>
      <button type="button" @click="$emit('add-formation')">{{ t('strategyPlanner.formation') }}</button>
    </div>

    <div class="strategy-command-group strategy-text-command">
      <label>
        <span class="sr-only">{{ t('strategyPlanner.textValue') }}</span>
        <input :value="textValue" maxlength="500" :placeholder="t('strategyPlanner.textValue')" @input="$emit('update:textValue', $event.target.value)" />
      </label>
      <button type="button" @click="$emit('add-text')">{{ t('strategyPlanner.addText') }}</button>
    </div>

    <fieldset class="strategy-command-colors">
      <legend class="sr-only">{{ t('strategyPlanner.color') }}</legend>
      <button
        v-for="value in colors" :key="value" type="button" :class="{ active: color === value }"
        :style="{ '--strategy-color': value }" :aria-label="`${t('strategyPlanner.color')} ${value}`"
        :aria-pressed="color === value" @click="$emit('update:color', value)"
      ></button>
    </fieldset>

    <div class="strategy-command-group strategy-history-commands">
      <button type="button" :disabled="!canUndo" @click="$emit('undo')">{{ t('strategyPlanner.undo') }}</button>
      <button type="button" :disabled="!canRedo" @click="$emit('redo')">{{ t('strategyPlanner.redo') }}</button>
    </div>
  </nav>
</template>
