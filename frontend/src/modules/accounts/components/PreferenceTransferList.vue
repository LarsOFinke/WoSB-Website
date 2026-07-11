<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { addPreferenceId, removePreferenceId, splitPreferenceOptions } from '@/modules/accounts/preferenceTransfer'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])
const { t } = useLocale()

const transferState = computed(() => splitPreferenceOptions(props.options, props.modelValue))
const selectedIds = computed(() => transferState.value.selectedIds)
const availableOptions = computed(() => transferState.value.availableOptions)
const selectedOptions = computed(() => transferState.value.selectedOptions)

function moveToSelected(id) {
  emit('update:modelValue', addPreferenceId(props.modelValue, id))
}

function moveToAvailable(id) {
  emit('update:modelValue', removePreferenceId(props.modelValue, id))
}
</script>

<template>
  <div class="preference-transfer-list">
    <section class="preference-transfer-column">
      <header>
        <strong>{{ t('profile.preferenceTransfer.available') }}</strong>
        <span>{{ availableOptions.length }}</span>
      </header>
      <div class="preference-transfer-options">
        <button
          v-for="option in availableOptions"
          :key="option.id"
          class="preference-transfer-option"
          type="button"
          :aria-label="`${t('profile.preferenceTransfer.select')} ${option.label}`"
          @click="moveToSelected(option.id)"
        >
          <span>{{ option.label }}</span>
          <b aria-hidden="true">→</b>
        </button>
        <p v-if="!availableOptions.length" class="muted preference-transfer-empty">
          {{ t('profile.preferenceTransfer.noneAvailable') }}
        </p>
      </div>
    </section>

    <span class="preference-transfer-arrow" aria-hidden="true">⇄</span>

    <section class="preference-transfer-column is-selected">
      <header>
        <strong>{{ t('profile.preferenceTransfer.selected') }}</strong>
        <span>{{ selectedOptions.length }}</span>
      </header>
      <div class="preference-transfer-options">
        <button
          v-for="option in selectedOptions"
          :key="option.id"
          class="preference-transfer-option is-selected"
          type="button"
          :aria-label="`${t('profile.preferenceTransfer.remove')} ${option.label}`"
          @click="moveToAvailable(option.id)"
        >
          <b aria-hidden="true">←</b>
          <span>{{ option.label }}</span>
        </button>
        <p v-if="!selectedOptions.length" class="muted preference-transfer-empty">
          {{ t('profile.preferenceTransfer.noneSelected') }}
        </p>
      </div>
    </section>
  </div>
</template>
