<script setup>
import { useLocale } from '@/locales'
import StrategyBackgroundControls from './StrategyBackgroundControls.vue'
import StrategyMarkerCreator from './StrategyMarkerCreator.vue'
import StrategyObjectEditor from './StrategyObjectEditor.vue'
import StrategyTransformControls from './StrategyTransformControls.vue'
import '../styles/strategyInspector.css'

const { t } = useLocale()

defineProps({
  strategy: { type: Object, required: true },
  background: { type: Object, default: null },
  ships: { type: Array, required: true },
  guides: { type: Array, required: true },
  marker: { type: Object, required: true },
  markerBuilds: { type: Array, required: true },
  selectedObject: { type: Object, default: null },
  selectedBuilds: { type: Array, required: true },
  shareUrl: { type: String, default: '' },
  colors: { type: Array, required: true },
  backgroundSettings: { type: Object, required: true },
})

defineEmits([
  'close', 'use-background', 'update-marker-ship', 'add-ship', 'update-selected-ship', 'update-background-settings',
  'record-history', 'delete-selected', 'toggle-publication', 'copy-share-link',
])

</script>

<template>
  <aside id="strategy-tool-rail" class="strategy-tool-rail strategy-inspector" :aria-label="t('strategyPlanner.tools')">
    <header class="strategy-tools-head">
      <div>
        <span class="strategy-tools-kicker">{{ t('strategyPlanner.inspector') }}</span>
        <strong>{{ t('strategyPlanner.tools') }}</strong>
      </div>
      <button type="button" class="strategy-inspector-close" :aria-label="t('strategyPlanner.hideTools')" @click="$emit('close')">
        <span aria-hidden="true">›</span>
      </button>
    </header>

    <p class="strategy-tools-intro">{{ t('strategyPlanner.inspectorHint') }}</p>

    <details class="strategy-tool-section" open>
      <summary>
        <span class="strategy-section-index">01</span>
        <span><strong>{{ t('strategyPlanner.briefing') }}</strong><small>{{ t('strategyPlanner.background') }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <div class="strategy-panel strategy-basics-panel">
          <label><span>{{ t('strategyPlanner.titleLabel') }}</span><input v-model="strategy.title" maxlength="180" required /></label>
          <label><span>{{ t('strategyPlanner.descriptionLabel') }}</span><textarea v-model="strategy.description" maxlength="1000" rows="3"></textarea></label>
        </div>
        <StrategyBackgroundControls :background="background" :settings="backgroundSettings" @use-background="$emit('use-background', $event)" @update:settings="$emit('update-background-settings', $event)" @record-history="$emit('record-history')" />
      </div>
    </details>

    <details class="strategy-tool-section" open>
      <summary>
        <span class="strategy-section-index">02</span>
        <span><strong>{{ t('strategyPlanner.marker') }}</strong><small>{{ t('strategyPlanner.addMarker') }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <StrategyMarkerCreator :marker="marker" :ships="ships" :guides="guides" :marker-builds="markerBuilds" @update-marker-ship="$emit('update-marker-ship')" @add-ship="$emit('add-ship')" />
      </div>
    </details>

    <details v-if="selectedObject" class="strategy-tool-section strategy-selection-section" open>
      <summary>
        <span class="strategy-section-index">03</span>
        <span><strong>{{ t('strategyPlanner.selectedObject') }}</strong><small>{{ selectedObject.type }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <StrategyObjectEditor :selected-object="selectedObject" :ships="ships" :guides="guides" :selected-builds="selectedBuilds" :colors="colors" @update-selected-ship="$emit('update-selected-ship')" @record-history="$emit('record-history')" @delete-selected="$emit('delete-selected')" />
      </div>
    </details>

    <details v-if="selectedObject" class="strategy-tool-section strategy-transform-section" open>
      <summary>
        <span class="strategy-section-index">04</span>
        <span><strong>{{ t('strategyPlanner.transform') }}</strong><small>{{ t('strategyPlanner.transformHint') }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <StrategyTransformControls :selected-object="selectedObject" @record-history="$emit('record-history')" />
      </div>
    </details>

    <details class="strategy-tool-section" open>
      <summary>
        <span class="strategy-section-index">{{ selectedObject ? '05' : '03' }}</span>
        <span><strong>{{ t('strategyPlanner.sharing') }}</strong><small>{{ t('strategyPlanner.sharingHint') }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <section class="strategy-panel strategy-publication-panel">
          <span class="strategy-publication-state" :class="{ 'is-published': strategy.is_published }">{{ t(strategy.is_published ? 'strategyPlanner.published' : 'strategyPlanner.private') }}</span>
          <button class="small-action" type="button" @click="$emit('toggle-publication')">{{ t(strategy.is_published ? 'strategyPlanner.unpublish' : 'strategyPlanner.publish') }}</button>
          <button v-if="strategy.is_published && shareUrl" class="small-action" type="button" @click="$emit('copy-share-link')">{{ t('strategyPlanner.copyLink') }}</button>
        </section>
      </div>
    </details>
  </aside>
</template>
