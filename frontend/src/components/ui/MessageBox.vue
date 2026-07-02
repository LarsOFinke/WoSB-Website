<template>
  <p v-if="message" class="message">{{ message }}</p>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: '',
  },
})
</script>
