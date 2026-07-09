<script setup>
import { useLocale } from '@/locales'

const props = defineProps({
  builds: {
    type: Array,
    default: () => [],
  },
})

const { t } = useLocale()

function shipLine(build) {
  return `${build.ship?.name || '—'} · ${t('common.rate')} ${build.ship?.rate || '—'} · ${t(`builds.types.${build.build_type || 'balanced'}`)}`
}
</script>

<template>
  <section v-if="builds.length" class="linked-builds-panel" :aria-label="t('buildEmbeds.linkedTitle')">
    <div class="linked-builds-heading">
      <span class="eyebrow">{{ t('buildEmbeds.linkedEyebrow') }}</span>
      <strong>{{ t('buildEmbeds.linkedTitle') }}</strong>
    </div>
    <div class="linked-builds-grid">
      <RouterLink v-for="build in builds" :key="build.id" class="linked-build-card" :to="`/builds/${build.id}`">
        <span>{{ t('buildEmbeds.linkedCardEyebrow') }}</span>
        <strong>{{ build.build_name }}</strong>
        <small>{{ shipLine(build) }}</small>
      </RouterLink>
    </div>
  </section>
</template>
