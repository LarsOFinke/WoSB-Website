<script setup>
import AppIcon from '@/core/components/AppIcon.vue'

defineProps({
  items: { type: Array, required: true },
  label: { type: String, default: '' },
})
</script>

<template>
  <dl class="workspace-stat-rail" :aria-label="label || undefined">
    <div v-for="item in items" :key="item.key || item.label" class="workspace-stat-item">
      <AppIcon v-if="item.icon" :name="item.icon" :size="19" />
      <span>
        <dt>{{ item.label }}</dt>
        <dd>{{ item.value }}</dd>
        <small v-if="item.hint">{{ item.hint }}</small>
      </span>
    </div>
  </dl>
</template>
