<script setup>
import StrategyDocument from '../components/StrategyDocument.vue'
import { useStrategyViewPage } from '../composables/useStrategyView.js'
import '../styles/strategyPlanner.css'
import '../styles/strategyView.css'

const {
  t, strategy, document, ships, builds, guides, canvas, loading, error,
  isShared, canEdit, backgroundUrl, shareUrl, copyShareLink, downloadSvg, printStrategy,
} = useStrategyViewPage()
</script>

<template>
  <section class="strategy-view-page" aria-labelledby="strategy-view-title">
    <p v-if="loading" class="strategy-status muted">{{ t('strategyPlanner.loading') }}</p>
    <p v-else-if="error" class="strategy-status error-text" role="alert">{{ error }}</p>
    <template v-else-if="strategy">
      <header class="strategy-view-header">
        <RouterLink class="strategy-view-back" :to="isShared ? '/' : '/strategies'">← {{ t('common.back') }}</RouterLink>
        <div class="strategy-view-heading">
          <div>
            <p class="eyebrow">{{ t('strategyPlanner.eyebrow') }}</p>
            <h1 id="strategy-view-title">{{ strategy.title }}</h1>
            <p v-if="strategy.description">{{ strategy.description }}</p>
          </div>
          <div class="strategy-view-actions">
            <button v-if="shareUrl" type="button" class="small-action" @click="copyShareLink">{{ t('strategyPlanner.copyLink') }}</button>
            <button type="button" class="small-action" @click="printStrategy">{{ t('strategyPlanner.print') }}</button>
            <button type="button" class="small-action" @click="downloadSvg">{{ t('strategyPlanner.downloadSvg') }}</button>
            <RouterLink v-if="canEdit" class="small-action primary-action" :to="`/strategies/${strategy.id}/edit`">{{ t('strategyPlanner.edit') }}</RouterLink>
          </div>
        </div>
      </header>

      <main class="strategy-view-content">
        <StrategyDocument
          ref="canvas" :title="strategy.title" :description="strategy.description" :document="document"
          :background-url="backgroundUrl" :ships="ships" :builds="builds" :guides="guides" read-only
        />
      </main>
    </template>
  </section>
</template>
