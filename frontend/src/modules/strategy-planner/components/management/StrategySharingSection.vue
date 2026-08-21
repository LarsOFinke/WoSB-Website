<script setup>
import { useLocale } from '@/locales'

defineProps({
  strategy: { type: Object, required: true },
  shareUrl: { type: String, default: '' },
})

const emit = defineEmits(['toggle-publication', 'copy-share-link'])
const { t } = useLocale()
</script>

<template>
  <section class="strategy-management-section" aria-labelledby="strategy-visibility-title">
    <header>
      <span class="strategy-section-index">01</span>
      <div>
        <strong id="strategy-visibility-title">{{ t('strategyPlanner.visibility') }}</strong>
        <small>{{ t('strategyPlanner.sharingHint') }}</small>
      </div>
    </header>
    <div class="strategy-management-section-body">
      <section class="strategy-panel strategy-publication-panel">
        <div class="strategy-publication-summary">
          <span class="strategy-publication-state" :class="{ 'is-published': strategy.is_published }" role="status">{{ t(strategy.is_published ? 'strategyPlanner.published' : 'strategyPlanner.private') }}</span>
          <p>{{ t(strategy.is_published ? 'strategyPlanner.publishedVisibilityHint' : 'strategyPlanner.privateVisibilityHint') }}</p>
        </div>
        <div class="strategy-publication-actions">
          <button class="primary-action" type="button" @click="emit('toggle-publication')">{{ t(strategy.is_published ? 'strategyPlanner.makePrivate' : 'strategyPlanner.makePublic') }}</button>
          <template v-if="strategy.is_published && shareUrl">
            <a class="small-action" :href="shareUrl" target="_blank" rel="noopener noreferrer">{{ t('strategyPlanner.viewPublicStrategy') }}</a>
            <button class="small-action" type="button" @click="emit('copy-share-link')">{{ t('strategyPlanner.copyLink') }}</button>
          </template>
        </div>
        <label v-if="strategy.is_published && shareUrl" class="strategy-public-link">
          <span>{{ t('strategyPlanner.publicLink') }}</span>
          <input :value="shareUrl" type="url" readonly />
        </label>
      </section>
    </div>
  </section>
</template>
