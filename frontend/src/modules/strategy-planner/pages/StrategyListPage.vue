<script setup>
import { useStrategyListPage } from '../composables/useStrategyList.js'
import '../styles/strategyPlanner.css'

const { t, canAuthorContent, strategies, loading, error, remove, copy } = useStrategyListPage()
</script>

<template>
  <section class="strategy-list-page" aria-labelledby="strategy-list-title">
    <div class="strategy-list-frame">
      <header class="strategy-list-hero">
        <div>
          <p class="eyebrow">{{ t('strategyPlanner.eyebrow') }}</p>
          <h1 id="strategy-list-title">{{ t('strategyPlanner.title') }}</h1>
          <p>{{ t('strategyPlanner.subtitle') }}</p>
        </div>
        <RouterLink v-if="canAuthorContent" class="button-box primary-action" to="/strategies/new">{{ t('strategyPlanner.create') }}</RouterLink>
      </header>
      <p v-if="loading" class="muted">{{ t('strategyPlanner.loading') }}</p>
      <p v-else-if="error" class="error-text">{{ error }}</p>
      <div v-else-if="!strategies.length" class="empty-state-block">
        <h2>{{ t('strategyPlanner.empty') }}</h2>
        <RouterLink v-if="canAuthorContent" class="button-box primary-action" to="/strategies/new">{{ t('strategyPlanner.create') }}</RouterLink>
      </div>
      <div v-else class="strategy-card-grid">
        <article v-for="item in strategies" :key="item.id" class="strategy-card">
          <img :src="item.background_file.public_url" alt="" />
          <div>
            <span class="strategy-publication-badge">{{ t(item.is_published ? 'strategyPlanner.published' : 'strategyPlanner.private') }}</span>
            <h2>{{ item.title }}</h2>
            <p v-if="item.description">{{ item.description }}</p>
          </div>
          <footer>
            <RouterLink class="small-action" :to="`/strategies/${item.id}`">{{ t('strategyPlanner.view') }}</RouterLink>
            <RouterLink v-if="canAuthorContent" class="small-action" :to="`/strategies/${item.id}/edit`">{{ t('strategyPlanner.edit') }}</RouterLink>
            <button v-if="item.is_published" class="small-action" type="button" @click="copy(item)">{{ t('strategyPlanner.copyLink') }}</button>
            <button v-if="canAuthorContent" class="danger-action" type="button" @click="remove(item)">{{ t('strategyPlanner.delete') }}</button>
          </footer>
        </article>
      </div>
    </div>
  </section>
</template>
