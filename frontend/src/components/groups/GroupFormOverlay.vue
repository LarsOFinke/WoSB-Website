<template>
  <DetailOverlay :open="open" title="Neue Gruppe anlegen" eyebrow="Gruppenverwaltung" @close="$emit('close')">
    <GroupForm @submit="$emit('submit', $event)" />
  </DetailOverlay>
</template>

<script setup>
import GroupForm from '@/components/groups/GroupForm.vue'
import DetailOverlay from '@/components/ui/DetailOverlay.vue'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['submit', 'close'])
</script>
