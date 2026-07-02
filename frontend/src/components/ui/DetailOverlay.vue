<template>
  <Teleport to="body">
    <div v-if="open" class="overlay-backdrop" @click.self="$emit('close')">
      <section class="overlay-panel" role="dialog" aria-modal="true" :aria-label="title">
        <div class="overlay-header">
          <div>
            <span v-if="eyebrow" class="badge">{{ eyebrow }}</span>
            <h2>{{ title }}</h2>
          </div>
          <button class="icon-button" type="button" aria-label="Overlay schließen" @click="$emit('close')">×</button>
        </div>
        <slot />
      </section>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    required: true,
  },
  eyebrow: {
    type: String,
    default: '',
  },
})

defineEmits(['close'])
</script>
