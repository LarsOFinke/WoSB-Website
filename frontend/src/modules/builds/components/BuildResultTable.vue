<script setup>
import AppIcon from '@/core/components/AppIcon.vue'

defineProps({
  rows: { type: Array, required: true },
  labels: { type: Object, required: true },
})
</script>

<template>
  <div class="build-library-table" role="table" :aria-label="labels.results">
    <div class="build-library-table-head" role="row">
      <span role="columnheader">{{ labels.build }}</span>
      <span role="columnheader">{{ labels.type }}</span>
      <span role="columnheader">{{ labels.crew }}</span>
      <span role="columnheader">{{ labels.upgrades }}</span>
      <span role="columnheader">{{ labels.weapons }}</span>
      <span role="columnheader">{{ labels.specialists }}</span>
      <span role="columnheader">{{ labels.inventory }}</span>
      <span aria-hidden="true"></span>
    </div>
    <RouterLink v-for="row in rows" :key="row.id" class="build-library-row" :to="`/builds/${row.id}`" role="row">
      <span class="build-library-identity" role="cell">
        <span class="build-library-row-icon"><AppIcon name="builds" :size="18" /></span>
        <span><strong>{{ row.name }}</strong><small>{{ row.ship }}</small></span>
      </span>
      <span role="cell"><small class="build-library-mobile-label">{{ labels.type }}</small>{{ row.type }}</span>
      <span role="cell"><small class="build-library-mobile-label">{{ labels.crew }}</small>{{ row.crew }}</span>
      <span role="cell"><small class="build-library-mobile-label">{{ labels.upgrades }}</small>{{ row.upgrades }}</span>
      <span role="cell"><small class="build-library-mobile-label">{{ labels.weapons }}</small>{{ row.weapons }}</span>
      <span role="cell"><small class="build-library-mobile-label">{{ labels.specialists }}</small>{{ row.specialists }}</span>
      <span role="cell"><small class="build-library-mobile-label">{{ labels.inventory }}</small>{{ row.inventory }}</span>
      <span class="build-library-open" aria-hidden="true"><AppIcon name="chevron-right" :size="18" /></span>
    </RouterLink>
  </div>
</template>
