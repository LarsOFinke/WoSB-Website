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
    <header class="strategy-command-heading">
      <div><span>{{ t('strategyPlanner.commandDeck') }}</span><strong>{{ t('strategyPlanner.objects') }}</strong></div>
      <div class="strategy-history-commands" :aria-label="t('strategyPlanner.history')">
        <button type="button" :disabled="!canUndo" :aria-label="t('strategyPlanner.undo')" @click="$emit('undo')"><span aria-hidden="true">↶</span><strong>{{ t('strategyPlanner.undo') }}</strong></button>
        <button type="button" :disabled="!canRedo" :aria-label="t('strategyPlanner.redo')" @click="$emit('redo')"><span aria-hidden="true">↷</span><strong>{{ t('strategyPlanner.redo') }}</strong></button>
      </div>
    </header>

    <div class="strategy-command-sections">
      <details class="strategy-command-section strategy-drawing-command" open>
        <summary><span>01</span><strong>{{ t('strategyPlanner.drawingTools') }}</strong></summary>
        <div class="strategy-command-group strategy-mode-commands">
          <button type="button" :class="{ active: mode === 'select' }" :aria-pressed="mode === 'select'" @click="$emit('update:mode', 'select')"><span aria-hidden="true">↖</span>{{ t('strategyPlanner.select') }}</button>
          <button type="button" :class="{ active: mode === 'freehand' }" :aria-pressed="mode === 'freehand'" @click="$emit('update:mode', 'freehand')"><span aria-hidden="true">✎</span>{{ t('strategyPlanner.freehand') }}</button>
          <button type="button" @click="$emit('add-line', 'line')"><span aria-hidden="true">╱</span>{{ t('strategyPlanner.line') }}</button>
          <button type="button" @click="$emit('add-line', 'arrow')"><span aria-hidden="true">→</span>{{ t('strategyPlanner.arrow') }}</button>
        </div>
      </details>

      <details class="strategy-command-section strategy-formation-command" open>
        <summary><span>02</span><strong>{{ t('strategyPlanner.formationsLabel') }}</strong></summary>
        <div class="strategy-command-group">
          <label>
            <span>{{ t('strategyPlanner.formationType') }}</span>
            <select :value="formation" @change="$emit('update:formation', $event.target.value)">
              <option v-for="name in ['line', 'circle', 'wedge', 'column', 'box']" :key="name" :value="name">{{ t(`strategyPlanner.formations.${name}`) }}</option>
            </select>
          </label>
          <button type="button" class="strategy-command-create" :aria-label="t('strategyPlanner.formation')" @click="$emit('add-formation')">+ {{ t('strategyPlanner.formation') }}</button>
        </div>
      </details>

      <details class="strategy-command-section strategy-text-command" open>
        <summary><span>03</span><strong>{{ t('strategyPlanner.annotations') }}</strong></summary>
        <div class="strategy-command-group">
          <label>
            <span>{{ t('strategyPlanner.textValue') }}</span>
            <input :value="textValue" maxlength="500" :placeholder="t('strategyPlanner.textValue')" @input="$emit('update:textValue', $event.target.value)" />
          </label>
          <button type="button" class="strategy-command-create" :aria-label="t('strategyPlanner.addText')" @click="$emit('add-text')">+ {{ t('strategyPlanner.addText') }}</button>
        </div>
      </details>

      <details class="strategy-command-section strategy-color-command" open>
        <summary><span>04</span><strong>{{ t('strategyPlanner.color') }}</strong></summary>
        <fieldset class="strategy-command-colors">
          <legend class="sr-only">{{ t('strategyPlanner.color') }}</legend>
          <button
            v-for="value in colors" :key="value" type="button" :class="{ active: color === value }"
            :style="{ '--strategy-color': value }" :aria-label="`${t('strategyPlanner.color')} ${value}`"
            :aria-pressed="color === value" @click="$emit('update:color', value)"
          ><span v-if="color === value" aria-hidden="true">✓</span></button>
        </fieldset>
      </details>
    </div>
  </nav>
</template>
