<template>
  <DetailOverlay :open="open" title="Neuen Schiffs-Build anlegen" eyebrow="Build erstellen" @close="$emit('close')">
    <BuildForm :ships="ships" :build-options="buildOptions" @submit="$emit('submit', $event)" @cancel="$emit('close')" />
  </DetailOverlay>
</template>

<script setup>
import BuildForm from '@/components/builds/BuildForm.vue'
import DetailOverlay from '@/components/ui/DetailOverlay.vue'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  ships: {
    type: Array,
    default: () => [],
  },
  buildOptions: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['submit', 'close'])
</script>
