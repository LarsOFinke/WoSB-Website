<script setup>
import { useLocale } from '@/locales'
import StrategySharingSection from './StrategySharingSection.vue'
import '../../styles/strategyInspector.css'

defineProps({
  open: { type: Boolean, default: true },
  strategy: { type: Object, required: true },
  shareUrl: { type: String, default: '' },
})

defineEmits(['toggle', 'toggle-publication', 'copy-share-link'])

const { t } = useLocale()
</script>

<template>
  <aside id="strategy-management-panel" class="strategy-inspector-panel strategy-management-panel" :class="{ 'is-collapsed': !open }" :aria-label="t('strategyPlanner.strategyManagement')">
    <header class="strategy-tools-head">
      <div>
        <span class="strategy-tools-kicker">{{ t('strategyPlanner.strategyManagement') }}</span>
        <strong>{{ t('strategyPlanner.visibility') }}</strong>
      </div>
    </header>
    <p v-if="open" class="strategy-tools-intro">{{ t('strategyPlanner.managementHint') }}</p>
    <div id="strategy-management-sections" class="strategy-management-grid">
      <StrategySharingSection
        v-if="open"
        :strategy="strategy"
        :share-url="shareUrl"
        @toggle-publication="$emit('toggle-publication')"
        @copy-share-link="$emit('copy-share-link')"
      />
      <div class="strategy-inspector-control-card strategy-management-control-card">
        <span class="strategy-section-index">{{ open ? '02' : '01' }}</span>
        <button type="button" class="strategy-inspector-toggle strategy-management-toggle" aria-controls="strategy-management-sections" :aria-expanded="open" @click="$emit('toggle')">
          <span aria-hidden="true">{{ open ? '⌄' : '⌃' }}</span>
          <strong>{{ t(open ? 'strategyPlanner.hideManagement' : 'strategyPlanner.showManagement') }}</strong>
        </button>
      </div>
    </div>
  </aside>
</template>
