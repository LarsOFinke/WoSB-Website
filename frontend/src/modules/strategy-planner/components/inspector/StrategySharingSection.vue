<script setup>
import { useLocale } from '@/locales'

const props = defineProps({
  strategy: { type: Object, required: true },
  shareUrl: { type: String, default: '' },
  sectionIndex: { type: String, default: '05' },
})

const emit = defineEmits(['toggle-publication', 'copy-share-link'])
const { t } = useLocale()
</script>

<template>
  <details class="strategy-tool-section" open>
    <summary>
      <span class="strategy-section-index">{{ props.sectionIndex }}</span>
      <span><strong>{{ t('strategyPlanner.sharing') }}</strong><small>{{ t('strategyPlanner.sharingHint') }}</small></span>
    </summary>
    <div class="strategy-tool-section-body">
      <section class="strategy-panel strategy-publication-panel">
        <span class="strategy-publication-state" :class="{ 'is-published': strategy.is_published }">{{ t(strategy.is_published ? 'strategyPlanner.published' : 'strategyPlanner.private') }}</span>
        <button class="small-action" type="button" @click="emit('toggle-publication')">{{ t(strategy.is_published ? 'strategyPlanner.unpublish' : 'strategyPlanner.publish') }}</button>
        <button v-if="strategy.is_published && shareUrl" class="small-action" type="button" @click="emit('copy-share-link')">{{ t('strategyPlanner.copyLink') }}</button>
      </section>
    </div>
  </details>
</template>
