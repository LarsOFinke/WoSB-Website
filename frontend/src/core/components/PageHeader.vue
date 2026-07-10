<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  titleId: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <header class="wire-section workspace-page-header" :class="{ 'is-compact': compact }">
    <div class="workspace-page-header-copy">
      <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
      <h1 :id="titleId || undefined">{{ title }}</h1>
      <p v-if="description" class="workspace-page-description">{{ description }}</p>
      <div v-if="$slots.meta" class="workspace-page-meta"><slot name="meta" /></div>
    </div>
    <div v-if="$slots.actions" class="workspace-page-actions"><slot name="actions" /></div>
  </header>
</template>
