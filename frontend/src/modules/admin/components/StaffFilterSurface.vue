<script setup>
defineProps({
  title: { type: String, required: true },
  hint: { type: String, required: true },
  resetLabel: { type: String, required: true },
})

defineEmits(['reset'])
</script>

<template>
  <div class="staff-filter-surface">
    <div class="staff-filter-surface-head">
      <div>
        <strong>{{ title }}</strong>
        <small>{{ hint }}</small>
      </div>
      <slot name="actions">
        <button class="small-action" type="button" @click="$emit('reset')">
          {{ resetLabel }}
        </button>
      </slot>
    </div>
    <div class="staff-filter-row staff-filter-row--wide">
      <slot />
    </div>
  </div>
</template>
