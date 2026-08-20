<script setup>
import { ref } from 'vue'
import StrategyDocument from '../components/StrategyDocument.vue'
import StrategyInspector from '../components/StrategyInspector.vue'
import StrategyToolbar from '../components/StrategyToolbar.vue'
import { useStrategyPlannerPage } from '../composables/useStrategyPlanner.js'
import '../styles/strategyPlanner.css'
import '../styles/strategyToolbar.css'

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
      <button
        type="button" class="strategy-tools-toggle" :class="{ 'is-open': toolsOpen }"
        aria-controls="strategy-tool-rail" :aria-expanded="toolsOpen" @click="toolsOpen = !toolsOpen"
      ><span aria-hidden="true">{{ toolsOpen ? '›' : '‹' }}</span><strong>{{ t(toolsOpen ? 'strategyPlanner.hideTools' : 'strategyPlanner.showTools') }}</strong></button>

      <StrategyInspector
        v-show="toolsOpen" :strategy="strategy" :background="background" :ships="ships" :guides="guides"
        :marker="marker" :marker-builds="markerBuilds" :selected-object="selectedObject"
        :selected-builds="selectedBuilds" :share-url="shareUrl" :colors="STRATEGY_COLORS"
        @close="toolsOpen = false" @use-background="useBackground"
        @update-marker-ship="updateMarkerShipReference" @add-ship="addShip"
        @update-selected-ship="updateSelectedShipReference" @record-history="recordHistory"
        @delete-selected="deleteSelected" @toggle-publication="togglePublication" @copy-share-link="copyShareLink"
      />

      <main class="strategy-chart-column">
        <p v-if="!backgroundUrl" class="strategy-empty-canvas">{{ t('strategyPlanner.missingBackground') }}</p>
        <StrategyDocument
          v-else ref="canvas" :title="strategy.title || t('strategyPlanner.title')"
          :description="strategy.description" :document="document" :background-url="backgroundUrl"
          :ships="ships" :builds="builds" :guides="guides" :selected-id="selectedId"
          :mode="mode" :color="color"
          @update:document="setDocument" @select="selectedId = $event" @history="recordHistory"
        >
          <template #after-canvas>
            <p class="strategy-object-help">{{ t('strategyPlanner.objectHelp') }}</p>
          </template>
        </StrategyDocument>
      </main>
    </div>
  </section>
</template>
