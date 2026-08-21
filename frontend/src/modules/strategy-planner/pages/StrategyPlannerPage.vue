<script setup>
import { ref } from 'vue'
import StrategyDocument from '../components/canvas/StrategyDocument.vue'
import StrategyInspector from '../components/inspector/StrategyInspector.vue'
import StrategyMarkerOverlay from '../components/marker-deck/StrategyMarkerOverlay.vue'
import StrategySetupDeck from '../components/command-deck/StrategySetupDeck.vue'
import StrategyToolbar from '../components/command-deck/StrategyToolbar.vue'
import { useStrategyPlannerPage } from '../composables/useStrategyPlanner.js'
import '../styles/strategyPlanner.css'
import '../styles/strategyToolbar.css'

const {
  t, strategy, background, document, ships, builds, guides, selectedId, selectedObject,
  markerBuilds, selectedBuilds,
  mode, color, marker, formation, textValue, loading, saving, error, status, canvas,
  backgroundUrl, canUndo, canRedo, shareUrl, STRATEGY_COLORS,
  setDocument, recordHistory, undo, redo, addShip, updateMarkerShipReference, updateSelectedShipReference, updateBackgroundSettings,
  addLine, addFormation, addText,
  deleteSelected, useBackground, save, togglePublication, copyShareLink, downloadSvg, printStrategy,
} = useStrategyPlannerPage()

const markerToolsOpen = ref(true)
const inspectorOpen = ref(true)
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

    <StrategySetupDeck
      v-if="!loading"
      :strategy="strategy"
      :background="background"
      :background-settings="document.background"
      @use-background="useBackground"
      @update-background-settings="updateBackgroundSettings"
      @record-history="recordHistory"
    />

    <StrategyToolbar
      v-if="!loading"
      :mode="mode" :color="color" :colors="STRATEGY_COLORS" :formation="formation"
      :text-value="textValue" :can-undo="canUndo" :can-redo="canRedo"
      @update:mode="mode = $event" @update:color="color = $event" @update:formation="formation = $event"
      @update:text-value="textValue = $event" @add-line="addLine" @add-formation="addFormation"
      @add-text="addText" @undo="undo" @redo="redo"
    />

    <div v-if="!loading" class="strategy-planner-workspace">
      <main class="strategy-chart-column">
        <StrategyMarkerOverlay
          v-show="markerToolsOpen"
          :marker="marker"
          :ships="ships"
          :guides="guides"
          :marker-builds="markerBuilds"
          @update-marker-ship="updateMarkerShipReference"
          @add-ship="addShip"
          @close="markerToolsOpen = false"
        />
        <button
          v-if="!markerToolsOpen"
          type="button"
          class="strategy-marker-tools-toggle"
          aria-controls="strategy-tool-rail"
          :aria-expanded="markerToolsOpen"
          @click="markerToolsOpen = true"
        ><span aria-hidden="true">＋</span><strong>{{ t('strategyPlanner.showMarkerTools') }}</strong></button>
        <p v-if="!backgroundUrl" class="strategy-empty-canvas">{{ t('strategyPlanner.missingBackground') }}</p>
        <StrategyDocument
          v-else ref="canvas" :title="strategy.title || t('strategyPlanner.title')"
          :description="strategy.description" :document="document" :background-url="backgroundUrl"
          :ships="ships" :builds="builds" :guides="guides" :selected-id="selectedId"
          :mode="mode" :color="color" :background-settings="document.background"
          @update:document="setDocument" @select="selectedId = $event" @history="recordHistory"
        >
          <template #after-canvas>
            <p class="strategy-object-help">{{ t('strategyPlanner.objectHelp') }}</p>
          </template>
        </StrategyDocument>
      </main>
      <section class="strategy-workspace-tools" :aria-label="t('strategyPlanner.tools')">
        <StrategyInspector
          :open="inspectorOpen"
          :strategy="strategy"
          :ships="ships"
          :guides="guides"
          :selected-object="selectedObject"
          :selected-builds="selectedBuilds"
          :share-url="shareUrl"
          :colors="STRATEGY_COLORS"
          @toggle="inspectorOpen = !inspectorOpen"
          @update-selected-ship="updateSelectedShipReference"
          @record-history="recordHistory"
          @delete-selected="deleteSelected"
          @toggle-publication="togglePublication"
          @copy-share-link="copyShareLink"
        />
      </section>
    </div>
  </section>
</template>
