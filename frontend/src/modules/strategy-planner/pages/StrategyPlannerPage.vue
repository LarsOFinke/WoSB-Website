<script setup>
import { ref } from 'vue'
import StrategyDocument from '../components/canvas/StrategyDocument.vue'
import StrategyCanvasTools from '../components/canvas-tools/StrategyCanvasTools.vue'
import StrategyMarkerTools from '../components/canvas-tools/StrategyMarkerTools.vue'
import StrategySetupDeck from '../components/command-deck/StrategySetupDeck.vue'
import StrategyToolbar from '../components/command-deck/StrategyToolbar.vue'
import StrategyManagement from '../components/management/StrategyManagement.vue'
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

const canvasToolsOpen = ref(true)
const markerToolsOpen = ref(true)
const managementOpen = ref(true)

function addMarkerAndOpenObjectTools() {
  addShip()
  markerToolsOpen.value = false
  canvasToolsOpen.value = true
}
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
        <StrategyMarkerTools
          v-show="markerToolsOpen"
          :marker="marker"
          :ships="ships"
          :guides="guides"
          :marker-builds="markerBuilds"
          @update-marker-ship="updateMarkerShipReference"
          @add-ship="addMarkerAndOpenObjectTools"
          @close="markerToolsOpen = false"
        />
        <button
          v-if="!markerToolsOpen"
          type="button"
          class="strategy-marker-tools-toggle"
          aria-controls="strategy-marker-tools"
          :aria-expanded="markerToolsOpen"
          @click="markerToolsOpen = true"
        ><span aria-hidden="true">＋</span><strong>{{ t('strategyPlanner.showMarkerTools') }}</strong></button>
        <StrategyCanvasTools
          v-if="selectedObject"
          v-show="canvasToolsOpen"
          :ships="ships"
          :guides="guides"
          :selected-object="selectedObject"
          :selected-builds="selectedBuilds"
          :colors="STRATEGY_COLORS"
          @update-selected-ship="updateSelectedShipReference"
          @record-history="recordHistory"
          @delete-selected="deleteSelected"
          @close="canvasToolsOpen = false"
        />
        <button
          v-if="selectedObject && !canvasToolsOpen"
          type="button"
          class="strategy-canvas-tools-toggle"
          aria-controls="strategy-canvas-tools"
          :aria-expanded="canvasToolsOpen"
          @click="canvasToolsOpen = true"
        ><span aria-hidden="true">＋</span><strong>{{ t('strategyPlanner.showObjectTools') }}</strong></button>
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
        <StrategyManagement
          :open="managementOpen"
          :strategy="strategy"
          :share-url="shareUrl"
          @toggle="managementOpen = !managementOpen"
          @toggle-publication="togglePublication"
          @copy-share-link="copyShareLink"
        />
      </section>
    </div>
  </section>
</template>
