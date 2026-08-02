<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { addEffectRow, availableEffectDefinitions } from '@/modules/admin/domain/statEffectRows'

const props = defineProps({
  modelValue: { type: Array, required: true },
  definitions: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])
const { t } = useLocale()

const definitionByKey = computed(() => new Map(props.definitions.map((row) => [row.key, row])))

function statLabel(definition) {
  if (!definition) return '—'
  const path = `builds.statLabels.${definition.translation_key}`
  const translated = t(path)
  return translated === path ? definition.label : translated
}

function categoryLabel(category) {
  const translated = t(`masterData.effectCategories.${category}`)
  return translated === `masterData.effectCategories.${category}` ? category : translated
}

function groupedDefinitions(index) {
  const groups = new Map()
  for (const definition of availableEffectDefinitions(props.definitions, props.modelValue, index)) {
    if (!groups.has(definition.category)) groups.set(definition.category, [])
    groups.get(definition.category).push(definition)
  }
  return [...groups.entries()].map(([category, definitions]) => ({ category, definitions }))
}

function replaceRow(index, patch) {
  emit('update:modelValue', props.modelValue.map((row, rowIndex) => rowIndex === index ? { ...row, ...patch } : row))
}

function selectEffect(index, key) {
  const definition = definitionByKey.value.get(key)
  replaceRow(index, { key, value: definition?.value_type === 'boolean' ? 1 : 0 })
}

function addRow() {
  emit('update:modelValue', addEffectRow(props.modelValue, props.definitions))
}

function removeRow(index) {
  emit('update:modelValue', props.modelValue.filter((_, rowIndex) => rowIndex !== index))
}
</script>

<template>
  <div class="stat-effect-editor">
    <div v-if="modelValue.length" class="stat-effect-editor__rows">
      <div v-for="(row, index) in modelValue" :key="`${row.key}-${index}`" class="stat-effect-editor__row">
        <label>
          <span>{{ t('masterData.effectEditor.stat') }}</span>
          <select :value="row.key" :disabled="readonly" @change="selectEffect(index, $event.target.value)">
            <optgroup v-for="group in groupedDefinitions(index)" :key="group.category" :label="categoryLabel(group.category)">
              <option v-for="definition in group.definitions" :key="definition.key" :value="definition.key">{{ statLabel(definition) }}</option>
            </optgroup>
          </select>
        </label>
        <label v-if="definitionByKey.get(row.key)?.value_type === 'boolean'" class="toggle-field stat-effect-editor__toggle">
          <input :checked="Boolean(row.value)" type="checkbox" :disabled="readonly" @change="replaceRow(index, { value: $event.target.checked ? 1 : 0 })" />
          <span>{{ t('masterData.effectEditor.enabled') }}</span>
        </label>
        <label v-else>
          <span>{{ t('masterData.effectEditor.value') }}<template v-if="definitionByKey.get(row.key)?.unit"> ({{ definitionByKey.get(row.key).unit }})</template></span>
          <input :value="row.value" type="number" :step="definitionByKey.get(row.key)?.precision ? 0.1 : 1" :disabled="readonly" @input="replaceRow(index, { value: $event.target.value })" />
        </label>
        <button v-if="!readonly" class="danger-action" type="button" @click="removeRow(index)">{{ t('masterData.effectEditor.remove') }}</button>
      </div>
    </div>
    <p v-else class="empty-state-inline">{{ t('masterData.effectEditor.empty') }}</p>
    <button v-if="!readonly" class="small-action" type="button" :disabled="modelValue.length >= definitions.length" @click="addRow">{{ t('masterData.effectEditor.add') }}</button>
  </div>
</template>

<style scoped>
.stat-effect-editor,
.stat-effect-editor__rows {
  display: grid;
  gap: .65rem;
}

.stat-effect-editor__row {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) minmax(130px, .7fr) auto;
  gap: .65rem;
  align-items: end;
  padding: .7rem;
  border: 1px solid var(--line-faint);
  border-radius: var(--radius-sm);
  background: var(--surface-sheen);
}

.stat-effect-editor__toggle {
  min-height: 2.65rem;
}

@media (max-width: 720px) {
  .stat-effect-editor__row {
    grid-template-columns: 1fr;
  }
}
</style>
