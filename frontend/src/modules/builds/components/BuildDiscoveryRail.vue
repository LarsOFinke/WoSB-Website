<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import '@/shared/styles/discovery.css'

const props = defineProps({
  groups: { type: Array, required: true },
  modelValue: { type: String, default: '' },
  title: { type: String, required: true },
  hint: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

function select(value) {
  emit('update:modelValue', props.modelValue === value ? '' : value)
}
</script>

<template>
  <section class="build-library-discovery" :aria-labelledby="`${$attrs.id || 'build'}-title`">
    <div class="workspace-section-title">
      <div>
        <h2 :id="`${$attrs.id || 'build'}-title`">{{ title }}</h2>
        <p v-if="hint">{{ hint }}</p>
      </div>
    </div>
    <div class="build-library-discovery-groups">
      <section v-for="group in groups" :key="group.key" class="build-library-discovery-group">
        <h3>{{ group.label }}</h3>
        <div class="build-library-discovery-options">
          <button
            v-for="item in group.items"
            :key="item.value"
            type="button"
            :class="{ 'is-selected': modelValue === item.value }"
            :aria-pressed="modelValue === item.value"
            @click="select(item.value)"
          >
            <AppIcon :name="item.icon" :size="18" />
            <span>{{ item.label }}</span>
          </button>
        </div>
      </section>
    </div>
  </section>
</template>
