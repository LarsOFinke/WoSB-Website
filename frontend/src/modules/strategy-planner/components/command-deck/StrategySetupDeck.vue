<script setup>
import { useLocale } from '@/locales'
import StrategyBackgroundControls from './StrategyBackgroundControls.vue'
import '../../styles/strategySetup.css'

defineProps({
  strategy: { type: Object, required: true },
  background: { type: Object, default: null },
  backgroundSettings: { type: Object, required: true },
})

defineEmits(['use-background', 'update-background-settings', 'record-history'])

const { t } = useLocale()
</script>

<template>
  <section class="strategy-setup-deck" :aria-label="t('strategyPlanner.briefing')">
    <label class="strategy-setup-field strategy-title-field">
      <span class="strategy-setup-field-heading"><span>01</span><strong>{{ t('strategyPlanner.titleLabel') }}</strong></span>
      <input v-model="strategy.title" maxlength="180" required />
    </label>

    <label class="strategy-setup-field strategy-description-field">
      <span class="strategy-setup-field-heading"><span>02</span><strong>{{ t('strategyPlanner.descriptionLabel') }}</strong></span>
      <textarea v-model="strategy.description" maxlength="1000" rows="2"></textarea>
    </label>

    <StrategyBackgroundControls
      :background="background"
      :settings="backgroundSettings"
      @use-background="$emit('use-background', $event)"
      @update:settings="$emit('update-background-settings', $event)"
      @record-history="$emit('record-history')"
    />
  </section>
</template>
