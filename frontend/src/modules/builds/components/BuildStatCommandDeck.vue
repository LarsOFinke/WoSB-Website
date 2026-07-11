<script setup>
import { computed } from 'vue'

import { useLocale } from '@/locales'
import { absoluteFileUrl } from '@/modules/files/api/files'

const props = defineProps({
  ship: { type: Object, required: true },
  statRows: { type: Array, default: () => [] },
  upgradeSlots: { type: Array, default: () => [] },
  effectRows: { type: Array, default: () => [] },
  crewTotal: { type: Number, default: 0 },
  crewCapacity: { type: Number, default: 0 },
  crewRemaining: { type: Number, default: 0 },
  weaponTotal: { type: Number, default: 0 },
  upgradeSlotsAvailable: { type: Number, default: 0 },
  specialCrewTotal: { type: Number, default: 0 },
  detailMode: { type: Boolean, default: false },
})

const { t } = useLocale()

const CORE_STAT_KEYS = new Set([
  'durability',
  'speed_knots',
  'maneuverability',
  'armor',
  'hold_capacity',
  'crew_capacity',
  'sailor_minimum',
  'displacement_tons',
])

function roundByPrecision(value, precision = 0) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null
  const factor = 10 ** Number(precision || 0)
  const rounded = Math.round(Number(value) * factor) / factor
  return Number(precision || 0) === 0 ? Math.round(rounded) : rounded
}

function formatStatValue(value, unit, precision = 0) {
  const number = roundByPrecision(value, precision)
  if (number === null) return '—'
  return `${number}${unit ? ` ${unit}` : ''}`
}

function formatModifier(row) {
  const value = Number(row.modifier || 0)
  if (!Number.isFinite(value) || value === 0) return '—'
  const sign = value > 0 ? '+' : ''
  const suffix = row.modifier_kind === 'percent'
    || row.unit === '%'
    || String(row.effect_key || '').endsWith('_pct')
    ? '%'
    : (row.unit ? ` ${row.unit}` : '')
  return `${sign}${roundByPrecision(value, row.precision || 0)}${suffix}`
}

function rowIsDebuff(row) {
  return Boolean(row.isDebuff ?? row.is_debuff)
}

const coreRows = computed(() => props.statRows.filter((row) => CORE_STAT_KEYS.has(row.key)))
const activeEffects = computed(() => props.effectRows.filter((row) => Number(row.modifier || 0) !== 0))
const buffRows = computed(() => activeEffects.value.filter((row) => !rowIsDebuff(row)))
const debuffRows = computed(() => activeEffects.value.filter((row) => rowIsDebuff(row)))
const filledUpgradeSlots = computed(() => props.upgradeSlots.filter((slot) => slot?.name).length)
const shipImageUrl = computed(() => absoluteFileUrl(props.ship?.image_url))
const shipInitials = computed(() => String(props.ship?.name || 'RBF')
  .split(/\s+/)
  .filter(Boolean)
  .slice(0, 3)
  .map((part) => part[0])
  .join('')
  .toUpperCase())
const crewUsagePercent = computed(() => {
  if (!props.crewCapacity) return 0
  return Math.min(100, Math.max(0, (props.crewTotal / props.crewCapacity) * 100))
})
</script>

<template>
  <section class="build-command-deck" :class="{ 'is-detail': detailMode }" :aria-label="t('builds.commandDeck.title')">
    <header class="command-deck-header">
      <div>
        <span class="command-deck-eyebrow">{{ t('builds.commandDeck.eyebrow') }}</span>
        <h3>{{ t('builds.commandDeck.title') }}</h3>
      </div>
      <span class="command-deck-live" aria-live="polite">
        <i aria-hidden="true"></i>
        {{ t('builds.commandDeck.live') }}
      </span>
    </header>

    <div class="command-deck-overview">
      <article class="command-deck-panel ship-identity-panel">
        <div class="ship-visual" aria-hidden="true">
          <img v-if="shipImageUrl" class="ship-catalog-image" :src="shipImageUrl" alt="" />
          <svg v-else viewBox="0 0 320 180" role="img">
            <path class="ship-line sail-back" d="M160 25 L112 95 L160 95 Z" />
            <path class="ship-line sail-front" d="M170 38 L211 95 L170 95 Z" />
            <path class="ship-line mast" d="M164 22 L164 118" />
            <path class="ship-line hull" d="M56 105 Q82 141 160 148 Q241 140 267 105 L229 113 L91 113 Z" />
            <path class="ship-line water" d="M42 153 Q77 143 111 153 T180 153 T249 153 T292 153" />
          </svg>
          <span>{{ shipInitials }}</span>
        </div>
        <div class="ship-identity-copy">
          <span>{{ t('builds.commandDeck.selectedShip') }}</span>
          <strong>{{ ship.name }}</strong>
          <small>{{ t('common.rate') }} {{ ship.rate }} · {{ ship.ship_type }}</small>
        </div>
        <div class="ship-operational-summary">
          <span>{{ t('builds.commandDeck.crewMetric', { current: crewTotal, max: crewCapacity }) }}</span>
          <span>{{ t('builds.commandDeck.weaponMetric', { value: weaponTotal }) }}</span>
          <span>{{ t('builds.commandDeck.upgradeMetric', { used: filledUpgradeSlots, max: upgradeSlotsAvailable }) }}</span>
          <span>{{ t('builds.commandDeck.specialistMetric', { value: specialCrewTotal }) }}</span>
        </div>
        <div class="crew-capacity-meter" :aria-label="t('builds.commandDeck.crewMetric', { current: crewTotal, max: crewCapacity })">
          <span :style="{ width: `${crewUsagePercent}%` }"></span>
        </div>
        <small class="crew-capacity-caption">{{ t('builds.commandDeck.crewRemaining', { value: crewRemaining }) }}</small>
      </article>

      <article class="command-deck-panel effective-stats-panel">
        <div class="command-panel-title">
          <div>
            <span>{{ t('builds.commandDeck.performanceEyebrow') }}</span>
            <strong>{{ t('builds.commandDeck.performanceTitle') }}</strong>
          </div>
          <small>{{ t('builds.commandDeck.performanceHint') }}</small>
        </div>
        <div class="effective-stat-grid">
          <div
            v-for="row in coreRows"
            :key="row.key"
            class="effective-stat-cell"
            :class="{ 'has-modifier': Number(row.modifier) !== 0, 'is-debuff': rowIsDebuff(row) }"
          >
            <span>{{ row.label }}</span>
            <strong>{{ formatStatValue(row.effective, row.unit, row.precision) }}</strong>
            <small>
              {{ formatStatValue(row.base, row.unit, row.precision) }}
              <template v-if="Number(row.modifier) !== 0"> · {{ formatModifier(row) }}</template>
            </small>
          </div>
        </div>
      </article>
    </div>

    <article class="command-deck-panel upgrade-rack-panel">
      <div class="command-panel-title">
        <div>
          <span>{{ t('builds.commandDeck.configurationEyebrow') }}</span>
          <strong>{{ t('builds.commandDeck.configurationTitle') }}</strong>
        </div>
        <small>{{ t('builds.commandDeck.configurationHint') }}</small>
      </div>
      <div class="upgrade-rack-grid">
        <div
          v-for="slot in upgradeSlots"
          :key="slot.index"
          class="upgrade-rack-slot"
          :class="{ 'is-empty': !slot.name, 'is-locked': slot.locked }"
        >
          <span class="upgrade-rack-index">{{ String(slot.index).padStart(2, '0') }}</span>
          <div>
            <strong>{{ slot.label || t('builds.commandDeck.emptyUpgrade') }}</strong>
            <small v-if="slot.effects">{{ slot.effects }}</small>
            <small v-else-if="slot.locked">{{ t('builds.commandDeck.lockedUpgrade') }}</small>
            <small v-else>{{ t('builds.commandDeck.availableUpgrade') }}</small>
          </div>
        </div>
      </div>
    </article>

    <article class="command-deck-panel modifier-intelligence-panel">
      <div class="command-panel-title">
        <div>
          <span>{{ t('builds.commandDeck.modifierEyebrow') }}</span>
          <strong>{{ t('builds.commandDeck.modifierTitle') }}</strong>
        </div>
        <small>{{ t('builds.commandDeck.modifierHint') }}</small>
      </div>
      <div v-if="activeEffects.length" class="modifier-intelligence-grid">
        <section class="modifier-column positive-modifiers">
          <header>
            <span>{{ t('builds.commandDeck.buffs') }}</span>
            <strong>{{ buffRows.length }}</strong>
          </header>
          <div class="modifier-chip-grid">
            <span v-for="row in buffRows" :key="row.key" class="modifier-chip">
              <small>{{ row.label }}</small>
              <strong>{{ formatModifier(row) }}</strong>
            </span>
            <span v-if="!buffRows.length" class="modifier-empty">{{ t('builds.commandDeck.noBuffs') }}</span>
          </div>
        </section>
        <section class="modifier-column negative-modifiers">
          <header>
            <span>{{ t('builds.commandDeck.debuffs') }}</span>
            <strong>{{ debuffRows.length }}</strong>
          </header>
          <div class="modifier-chip-grid">
            <span v-for="row in debuffRows" :key="row.key" class="modifier-chip is-debuff">
              <small>{{ row.label }}</small>
              <strong>{{ formatModifier(row) }}</strong>
            </span>
            <span v-if="!debuffRows.length" class="modifier-empty">{{ t('builds.commandDeck.noDebuffs') }}</span>
          </div>
        </section>
      </div>
      <div v-else class="modifier-intelligence-empty">
        <strong>{{ t('builds.commandDeck.noModifiersTitle') }}</strong>
        <span>{{ t('builds.commandDeck.noModifiersText') }}</span>
      </div>
    </article>
  </section>
</template>
