<script setup>
import { useLocale } from '@/locales'
import StrategySelectionSection from './StrategySelectionSection.vue'
import StrategySharingSection from './StrategySharingSection.vue'
import StrategyTransformSection from './StrategyTransformSection.vue'
import '../../styles/strategyInspector.css'

const { t } = useLocale()

defineProps({
  open: { type: Boolean, default: true },
  strategy: { type: Object, required: true },
  ships: { type: Array, required: true },
  guides: { type: Array, required: true },
  selectedObject: { type: Object, default: null },
  selectedBuilds: { type: Array, required: true },
  shareUrl: { type: String, default: '' },
  colors: { type: Array, required: true },
})

defineEmits([
  'toggle', 'update-selected-ship',
  'record-history', 'delete-selected', 'toggle-publication', 'copy-share-link',
])

</script>

<template>
  <aside id="strategy-inspector-panel" class="strategy-inspector-panel strategy-inspector" :class="{ 'is-collapsed': !open }" :aria-label="t('strategyPlanner.tools')">
    <header class="strategy-tools-head">
      <div>
        <span class="strategy-tools-kicker">{{ t('strategyPlanner.inspector') }}</span>
        <strong>{{ t('strategyPlanner.tools') }}</strong>
      </div>
    </header>

    <p v-if="open" class="strategy-tools-intro">{{ t('strategyPlanner.inspectorHint') }}</p>

    <div id="strategy-inspector-sections" class="strategy-inspector-sections">
      <template v-if="open">
      <StrategySelectionSection
        v-if="selectedObject"
        :selected-object="selectedObject"
        :ships="ships"
        :guides="guides"
        :selected-builds="selectedBuilds"
        :colors="colors"
        section-index="03"
        @update-selected-ship="$emit('update-selected-ship')"
        @record-history="$emit('record-history')"
        @delete-selected="$emit('delete-selected')"
      />
      <StrategyTransformSection v-if="selectedObject" :selected-object="selectedObject" section-index="04" @record-history="$emit('record-history')" />
      <StrategySharingSection
        :strategy="strategy"
        :share-url="shareUrl"
        section-index="05"
        @toggle-publication="$emit('toggle-publication')"
        @copy-share-link="$emit('copy-share-link')"
      />
      </template>
      <div class="strategy-inspector-control-card">
        <span class="strategy-section-index">{{ open ? '06' : '01' }}</span>
        <button type="button" class="strategy-inspector-toggle" :aria-controls="'strategy-inspector-sections'" :aria-expanded="open" @click="$emit('toggle')">
          <span aria-hidden="true">{{ open ? '⌄' : '⌃' }}</span>
          <strong>{{ t(open ? 'strategyPlanner.hideInspector' : 'strategyPlanner.showInspector') }}</strong>
        </button>
      </div>
    </div>
  </aside>
</template>
