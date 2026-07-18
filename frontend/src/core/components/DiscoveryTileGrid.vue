<script setup>
import AppIcon from '@/core/components/AppIcon.vue'

const props = defineProps({
  items: { type: Array, required: true },
  modelValue: { type: [String, Array], default: '' },
  multiple: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

function isSelected(value) {
  return props.multiple
    ? Array.isArray(props.modelValue) && props.modelValue.includes(value)
    : props.modelValue === value
}

function toggle(value) {
  if (!props.multiple) {
    emit('update:modelValue', props.modelValue === value ? '' : value)
    return
  }
  const current = Array.isArray(props.modelValue) ? props.modelValue : []
  emit(
    'update:modelValue',
    current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
  )
}
</script>

<template>
  <div class="discovery-tile-grid" :class="{ 'is-compact': compact }">
    <button
      v-for="item in items"
      :key="item.value"
      type="button"
      class="discovery-tile"
      :class="[`tone-${item.tone || 'navy'}`, { 'is-selected': isSelected(item.value) }]"
      :aria-pressed="isSelected(item.value)"
      @click="toggle(item.value)"
    >
      <span class="discovery-tile-icon"><AppIcon :name="item.icon" :size="compact ? 24 : 30" /></span>
      <span class="discovery-tile-copy">
        <strong>{{ item.label }}</strong>
        <small v-if="item.description">{{ item.description }}</small>
      </span>
      <span class="discovery-tile-check" aria-hidden="true">{{ isSelected(item.value) ? '✓' : '+' }}</span>
    </button>
  </div>
</template>
