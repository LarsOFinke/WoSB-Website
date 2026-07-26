<script setup>
import AppIcon from '@/core/components/AppIcon.vue'

defineProps({
  groups: { type: Array, required: true },
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

function selectTopic(value) {
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="guide-topic-groups">
    <section v-for="group in groups" :key="group.key" class="guide-topic-group">
      <h3>{{ group.label }}</h3>
      <div class="guide-topic-options">
        <button
          v-for="item in group.items"
          :key="item.value"
          type="button"
          class="guide-topic-button"
          :class="{ 'is-selected': modelValue === item.value }"
          :aria-pressed="modelValue === item.value"
          @click="selectTopic(item.value)"
        >
          <AppIcon :name="item.icon" :size="20" />
          <span>{{ item.label }}</span>
        </button>
      </div>
    </section>
  </div>
</template>
