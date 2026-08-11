<script setup>
import { ref } from 'vue'
import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import { IMAGE_MIME_TYPES } from '@/modules/files/fileTypes'
import StrategyCanvas from '../components/StrategyCanvas.vue'
import StrategyLegend from '../components/StrategyLegend.vue'
import StrategyToolbar from '../components/StrategyToolbar.vue'
import { useStrategyPlannerPage } from '../composables/useStrategyPlanner.js'
import '../styles/strategyPlanner.css'
import '../styles/strategyToolbar.css'
import '../styles/strategyPrint.css'

const {
  t, strategy, background, document, ships, builds, guides, selectedId, selectedObject,
  markerBuilds, selectedBuilds,
  mode, color, marker, formation, textValue, loading, saving, error, status, canvas,
  backgroundUrl, canUndo, canRedo, shareUrl, STRATEGY_COLORS,
  setDocument, recordHistory, undo, redo, addShip, updateMarkerShipReference, updateSelectedShipReference,
  addLine, addFormation, addText,
  deleteSelected, useBackground, save, togglePublication, copyShareLink, downloadSvg, printStrategy,
} = useStrategyPlannerPage()

const toolsOpen = ref(true)
</script>

<template>
  <section class="strategy-planner-page" aria-labelledby="strategy-planner-title">
    <header class="strategy-planner-header">
      <div>
        <p class="eyebrow">{{ t('strategyPlanner.eyebrow') }}</p>
        <h1 id="strategy-planner-title">{{ strategy.title || t('strategyPlanner.title') }}</h1>
        <p>{{ t('strategyPlanner.subtitle') }}</p>
      </div>
      <div class="strategy-header-actions">
        <RouterLink class="small-action" to="/strategies">{{ t('common.back') }}</RouterLink>
        <button
          type="button" class="small-action strategy-tools-toggle"
          aria-controls="strategy-tool-rail" :aria-expanded="toolsOpen" @click="toolsOpen = !toolsOpen"
        >{{ t(toolsOpen ? 'strategyPlanner.hideTools' : 'strategyPlanner.showTools') }}</button>
        <button type="button" class="small-action" @click="printStrategy">{{ t('strategyPlanner.print') }}</button>
        <button type="button" class="small-action" @click="downloadSvg">{{ t('strategyPlanner.downloadSvg') }}</button>
        <button type="button" class="primary-action" :disabled="saving" @click="save">
          {{ saving ? t('strategyPlanner.saving') : t('strategyPlanner.save') }}
        </button>
      </div>
    </header>

    <p v-if="loading" class="strategy-status muted">{{ t('strategyPlanner.loading') }}</p>
    <p v-if="error" class="strategy-status error-text" role="alert">{{ error }}</p>
    <p v-if="status" class="strategy-status" role="status">{{ status }}</p>

    <StrategyToolbar
      v-if="!loading" :mode="mode" :color="color" :colors="STRATEGY_COLORS" :formation="formation"
      :text-value="textValue" :can-undo="canUndo" :can-redo="canRedo"
      @update:mode="mode = $event" @update:color="color = $event" @update:formation="formation = $event"
      @update:text-value="textValue = $event" @add-line="addLine" @add-formation="addFormation"
      @add-text="addText" @undo="undo" @redo="redo"
    />

    <div v-if="!loading" class="strategy-planner-workspace">
      <aside
        v-show="toolsOpen" id="strategy-tool-rail" class="strategy-tool-rail strategy-inspector"
        :aria-label="t('strategyPlanner.tools')"
      >
        <header class="strategy-tools-head">
          <strong>{{ t('strategyPlanner.tools') }}</strong>
          <button type="button" class="small-action" @click="toolsOpen = false">{{ t('strategyPlanner.hideTools') }}</button>
        </header>
        <section class="strategy-panel">
          <h2>{{ t('strategyPlanner.background') }}</h2>
          <p>{{ t('strategyPlanner.backgroundHint') }}</p>
          <FileUploadPanel usage-context="strategy" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="useBackground" />
          <small v-if="background">{{ background.original_name }}</small>
        </section>

        <section class="strategy-panel strategy-basics-panel">
          <label>
            <span>{{ t('strategyPlanner.titleLabel') }}</span>
            <input v-model="strategy.title" maxlength="180" required />
          </label>
          <label>
            <span>{{ t('strategyPlanner.descriptionLabel') }}</span>
            <textarea v-model="strategy.description" maxlength="1000" rows="3"></textarea>
          </label>
        </section>

        <section class="strategy-panel">
          <h2>{{ t('strategyPlanner.marker') }}</h2>
          <label>
            <span>{{ t('strategyPlanner.ship') }}</span>
            <select v-model="marker.shipId" required @change="updateMarkerShipReference">
              <option value="">—</option>
              <option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }} · {{ ship.ship_type }} · R{{ ship.rate }}</option>
            </select>
          </label>
          <label><span>{{ t('strategyPlanner.shipName') }}</span><input v-model="marker.shipName" maxlength="120" /></label>
          <label><span>{{ t('strategyPlanner.playerName') }}</span><input v-model="marker.playerName" maxlength="120" /></label>
          <label>
            <span>{{ t('strategyPlanner.build') }}</span>
            <select v-model="marker.buildId" :disabled="!marker.shipId"><option value="">{{ t('strategyPlanner.noBuild') }}</option><option v-for="build in markerBuilds" :key="build.id" :value="build.id">{{ build.build_name }}</option></select>
          </label>
          <label>
            <span>{{ t('strategyPlanner.guide') }}</span>
            <select v-model="marker.guideId"><option value="">{{ t('strategyPlanner.noGuide') }}</option><option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option></select>
          </label>
          <button class="small-action" type="button" @click="addShip">{{ t('strategyPlanner.addMarker') }}</button>
        </section>

        <section v-if="selectedObject" class="strategy-panel strategy-selection-panel">
          <h2>{{ selectedObject.type }}</h2>
          <label v-if="selectedObject.type === 'ship'">
            <span>{{ t('strategyPlanner.ship') }}</span>
            <select v-model.number="selectedObject.shipId" class="strategy-selected-ship" required @change="updateSelectedShipReference">
              <option value="">—</option>
              <option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }} · {{ ship.ship_type }} · R{{ ship.rate }}</option>
            </select>
          </label>
          <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.shipName') }}</span><input v-model="selectedObject.shipName" maxlength="120" @change="recordHistory" /></label>
          <label v-if="selectedObject.type === 'ship'"><span>{{ t('strategyPlanner.playerName') }}</span><input v-model="selectedObject.playerName" maxlength="120" @change="recordHistory" /></label>
          <label v-if="selectedObject.type === 'ship'">
            <span>{{ t('strategyPlanner.build') }}</span>
            <select v-model="selectedObject.buildId" @change="recordHistory"><option :value="null">{{ t('strategyPlanner.noBuild') }}</option><option v-for="build in selectedBuilds" :key="build.id" :value="build.id">{{ build.build_name }}</option></select>
          </label>
          <label v-if="selectedObject.type === 'ship'">
            <span>{{ t('strategyPlanner.guide') }}</span>
            <select v-model="selectedObject.guideId" @change="recordHistory"><option :value="null">{{ t('strategyPlanner.noGuide') }}</option><option v-for="guide in guides" :key="guide.id" :value="guide.id">{{ guide.title }}</option></select>
          </label>
          <label v-if="selectedObject.type === 'text'"><span>{{ t('strategyPlanner.textValue') }}</span><input v-model="selectedObject.text" maxlength="500" @change="recordHistory" /></label>
          <label><span>{{ t('strategyPlanner.scale') }}</span><input v-model.number="selectedObject.scale" type="range" min="0.25" max="4" step="0.05" @change="recordHistory" /></label>
          <label v-if="selectedObject.rotation != null"><span>{{ t('strategyPlanner.rotation') }}</span><input v-model.number="selectedObject.rotation" type="range" min="-180" max="180" @change="recordHistory" /></label>
          <button class="danger-action" type="button" @click="deleteSelected">{{ t('strategyPlanner.deleteObject') }}</button>
        </section>

        <section class="strategy-panel strategy-publication-panel">
          <strong>{{ t(strategy.is_published ? 'strategyPlanner.published' : 'strategyPlanner.private') }}</strong>
          <button class="small-action" type="button" @click="togglePublication">{{ t(strategy.is_published ? 'strategyPlanner.unpublish' : 'strategyPlanner.publish') }}</button>
          <button v-if="strategy.is_published && shareUrl" class="small-action" type="button" @click="copyShareLink">{{ t('strategyPlanner.copyLink') }}</button>
        </section>
      </aside>

      <main class="strategy-chart-column">
        <p v-if="!backgroundUrl" class="strategy-empty-canvas">{{ t('strategyPlanner.missingBackground') }}</p>
        <section v-else class="strategy-print-chart-page">
          <header class="strategy-print-summary">
            <p class="eyebrow">{{ t('strategyPlanner.eyebrow') }}</p>
            <h1>{{ strategy.title || t('strategyPlanner.title') }}</h1>
            <p v-if="strategy.description">{{ strategy.description }}</p>
          </header>
          <StrategyCanvas
            ref="canvas" :document="document" :background-url="backgroundUrl" :ships="ships"
            :selected-id="selectedId" :mode="mode" :color="color" :read-only="false"
            @update:document="setDocument" @select="selectedId = $event" @history="recordHistory"
          />
        </section>
        <p class="strategy-object-help">{{ t('strategyPlanner.objectHelp') }}</p>
        <section class="strategy-print-legend-page">
          <header class="strategy-print-player-heading">
            <p class="eyebrow">{{ strategy.title || t('strategyPlanner.title') }}</p>
            <h2>{{ t('strategyPlanner.playerList') }}</h2>
          </header>
          <StrategyLegend :document="document" :ships="ships" :builds="builds" :guides="guides" />
        </section>
      </main>
    </div>
  </section>
</template>
