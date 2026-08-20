<script setup>
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import { IMAGE_MIME_TYPES } from '@/modules/files/fileTypes'
import { useLocale } from '@/locales'
import '../styles/strategyInspector.css'

const { t } = useLocale()

const props = defineProps({
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
})

const emit = defineEmits([
  'close', 'use-background', 'update-marker-ship', 'add-ship', 'update-selected-ship',
  'record-history', 'delete-selected', 'toggle-publication', 'copy-share-link',
])

function setSelectedColor(value) {
  if (!props.selectedObject) return
  props.selectedObject.color = value
  emit('record-history')
}
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
        <div class="strategy-panel strategy-background-panel">
          <h2>{{ t('strategyPlanner.background') }}</h2>
          <p>{{ t('strategyPlanner.backgroundHint') }}</p>
          <FileUploadPanel usage-context="strategy" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="$emit('use-background', $event)" />
          <small v-if="background" class="strategy-background-name">{{ background.original_name }}</small>
        </div>
      </div>
    </details>

    <details class="strategy-tool-section" open>
      <summary>
        <span class="strategy-section-index">02</span>
        <span><strong>{{ t('strategyPlanner.marker') }}</strong><small>{{ t('strategyPlanner.addMarker') }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <section class="strategy-panel strategy-marker-panel">
          <label>
            <span>{{ t('strategyPlanner.ship') }}</span>
            <select v-model="marker.shipId" required @change="$emit('update-marker-ship')">
              <option value="">—</option>
              <option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }} · {{ ship.ship_type }} · R{{ ship.rate }}</option>
            </select>
          </label>
          <div class="strategy-field-pair">
            <label><span>{{ t('strategyPlanner.shipName') }}</span><input v-model="marker.shipName" maxlength="120" /></label>
            <label><span>{{ t('strategyPlanner.playerName') }}</span><input v-model="marker.playerName" maxlength="120" /></label>
          </div>
          <label><span>{{ t('strategyPlanner.build') }}</span><select v-model="marker.buildId" :disabled="!marker.shipId"><option value="">{{ t('strategyPlanner.noBuild') }}</option><option v-for="build in markerBuilds" :key="build.id" :value="build.id">{{ build.build_name }}</option></select></label>
          <label><span>{{ t('strategyPlanner.guide') }}</span><select v-model="marker.guideId"><option value="">{{ t('strategyPlanner.noGuide') }}</option><option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option></select></label>
          <button class="primary-action strategy-add-marker" type="button" @click="$emit('add-ship')">{{ t('strategyPlanner.addMarker') }}</button>
        </section>
      </div>
    </details>

    <details v-if="selectedObject" class="strategy-tool-section strategy-selection-section" open>
      <summary>
        <span class="strategy-section-index">03</span>
        <span><strong>{{ t('strategyPlanner.selectedObject') }}</strong><small>{{ selectedObject.type }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <section class="strategy-panel strategy-selection-panel">
          <label v-if="selectedObject.type === 'ship'">
            <span>{{ t('strategyPlanner.ship') }}</span>
            <select v-model.number="selectedObject.shipId" class="strategy-selected-ship" required @change="$emit('update-selected-ship')">
              <option value="">—</option>
              <option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }} · {{ ship.ship_type }} · R{{ ship.rate }}</option>
            </select>
          </label>
          <div v-if="selectedObject.type === 'ship'" class="strategy-field-pair">
            <label><span>{{ t('strategyPlanner.shipName') }}</span><input v-model="selectedObject.shipName" maxlength="120" @change="$emit('record-history')" /></label>
            <label><span>{{ t('strategyPlanner.playerName') }}</span><input v-model="selectedObject.playerName" maxlength="120" @change="$emit('record-history')" /></label>
          </div>
          <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.build') }}</span><select v-model="selectedObject.buildId" @change="$emit('record-history')"><option :value="null">{{ t('strategyPlanner.noBuild') }}</option><option v-for="build in selectedBuilds" :key="build.id" :value="build.id">{{ build.build_name }}</option></select></label>
          <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.guide') }}</span><select v-model="selectedObject.guideId" @change="$emit('record-history')"><option :value="null">{{ t('strategyPlanner.noGuide') }}</option><option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option></select></label>
          <label v-if="selectedObject.type === 'text'"><span>{{ t('strategyPlanner.textValue') }}</span><input v-model="selectedObject.text" maxlength="500" @change="$emit('record-history')" /></label>
          <div v-if="selectedObject.type === 'text'" class="strategy-text-color-field">
            <label><span>{{ t('strategyPlanner.textColor') }}</span><input v-model="selectedObject.color" class="strategy-native-color" type="color" @change="$emit('record-history')" /></label>
            <div class="strategy-object-colors" :aria-label="t('strategyPlanner.textColor')">
              <button
                v-for="value in colors" :key="value" type="button"
                :class="{ active: selectedObject.color === value }" :style="{ '--strategy-color': value }"
                :aria-label="`${t('strategyPlanner.textColor')} ${value}`" :aria-pressed="selectedObject.color === value"
                @click="setSelectedColor(value)"
              ><span v-if="selectedObject.color === value" aria-hidden="true">✓</span></button>
            </div>
          </div>
          <button class="danger-action" type="button" @click="$emit('delete-selected')">{{ t('strategyPlanner.deleteObject') }}</button>
        </section>
      </div>
    </details>

    <details v-if="selectedObject" class="strategy-tool-section strategy-transform-section" open>
      <summary>
        <span class="strategy-section-index">04</span>
        <span><strong>{{ t('strategyPlanner.transform') }}</strong><small>{{ t('strategyPlanner.transformHint') }}</small></span>
      </summary>
      <div class="strategy-tool-section-body">
        <section class="strategy-panel strategy-transform-panel">
          <div class="strategy-transform-control">
            <label><span>{{ t('strategyPlanner.scale') }}</span><input v-model.number="selectedObject.scale" type="range" min="0.25" max="4" step="0.05" @change="$emit('record-history')" /></label>
            <span class="strategy-transform-value">{{ Number(selectedObject.scale || 1).toFixed(2) }}×</span>
          </div>
          <div v-if="selectedObject.rotation != null" class="strategy-transform-control">
            <label><span>{{ t('strategyPlanner.rotation') }}</span><input v-model.number="selectedObject.rotation" type="range" min="-180" max="180" @change="$emit('record-history')" /></label>
            <span class="strategy-transform-value">{{ Number(selectedObject.rotation || 0) }}°</span>
          </div>
        </section>
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
