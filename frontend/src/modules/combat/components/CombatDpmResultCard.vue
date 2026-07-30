<script setup>
import { useLocale } from '@/locales'

const { t } = useLocale()

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  result: { type: Object, required: true },
  armor: { type: Number, required: true },
})

defineEmits(['update:armor'])
</script>

<template>
  <article class="combat-result-card">
    <header>
      <div>
        <p class="eyebrow">{{ title }}</p>
        <p>{{ description }}</p>
      </div>
      <label class="combat-armor-field">
        <span class="combat-field-label">{{ t('combatAnalysis.results.armor') }}</span>
        <input
          :value="armor"
          type="number"
          min="0"
          max="100"
          step="0.1"
          inputmode="decimal"
          @input="$emit('update:armor', Math.max(0, Number($event.target.value) || 0))"
        />
      </label>
    </header>

    <div class="combat-result-value">
      <strong v-if="result.rows.length">{{ Number(result.armorDpm || 0).toLocaleString(undefined, { maximumFractionDigits: 1 }) }}</strong>
      <strong v-else>—</strong>
      <span>{{ t('combatAnalysis.results.dpm') }}</span>
    </div>

    <div class="combat-result-modifiers">
      <span>{{ t('combatAnalysis.results.damageModifier') }} {{ result.damagePercent >= 0 ? '+' : '' }}{{ result.damagePercent }}%</span>
      <span>{{ t('combatAnalysis.results.reloadModifier') }} {{ result.reloadPercent >= 0 ? '+' : '' }}{{ result.reloadPercent }}%</span>
      <span v-if="result.rows.length">{{ t('combatAnalysis.results.rawDpm') }} {{ result.rawDpm }}</span>
    </div>

    <p v-if="result.missingProfiles.length" class="combat-data-warning">
      {{ t('combatAnalysis.results.missingData', { weapons: result.missingProfiles.join(', ') }) }}
    </p>
    <p v-else-if="result.empty" class="combat-empty-state">{{ t('combatAnalysis.results.selectWeapon') }}</p>

    <div v-if="result.rows.length" class="combat-breakdown-table" role="table">
      <div class="combat-breakdown-row is-heading" role="row">
        <span role="columnheader">{{ t('combatAnalysis.results.weapon') }}</span>
        <span role="columnheader">{{ t('combatAnalysis.results.quantity') }}</span>
        <span role="columnheader">{{ t('combatAnalysis.results.damage') }}</span>
        <span role="columnheader">{{ t('combatAnalysis.results.reload') }}</span>
        <span role="columnheader">{{ t('combatAnalysis.results.dpm') }}</span>
      </div>
      <div v-for="row in result.rows" :key="row.name" class="combat-breakdown-row" role="row">
        <strong role="cell">{{ row.name }}</strong>
        <span role="cell">{{ row.quantity }}</span>
        <span role="cell">{{ row.effectiveDamage }}</span>
        <span role="cell">{{ row.effectiveReload }}s</span>
        <span role="cell">{{ row.armorDpm }}</span>
      </div>
    </div>
  </article>
</template>
