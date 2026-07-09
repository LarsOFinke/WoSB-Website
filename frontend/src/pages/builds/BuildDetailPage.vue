<script setup>
import { computed, onMounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { getBuild } from '@/services/builds'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const { optionLabel, t } = useLocale()

const build = ref(null)
const loading = ref(false)
const error = ref('')

const weaponArcRows = computed(() => [
  { key: 'front', label: t('builds.detail.weapons.front'), slots: build.value?.front_weapon_slots || [] },
  { key: 'rear', label: t('builds.detail.weapons.rear'), slots: build.value?.rear_weapon_slots || [] },
  { key: 'port', label: t('builds.detail.weapons.port'), slots: build.value?.port_weapon_slots || [] },
  { key: 'starboard', label: t('builds.detail.weapons.starboard'), slots: build.value?.starboard_weapon_slots || [] },
  { key: 'mortar', label: t('builds.detail.weapons.mortar'), slots: build.value?.mortar_weapon_slots || [] },
])

const crewTotal = computed(() => build.value?.ship_stats?.crew_total || 0)

const upgrades = computed(() => {
  if (!build.value) return []
  return [
    build.value.upgrade_1,
    build.value.upgrade_2,
    build.value.upgrade_3,
    build.value.upgrade_4,
    build.value.upgrade_5,
    build.value.upgrade_6,
  ].filter(Boolean)
})

const specialCrewSlots = computed(() => build.value?.special_crew_slots || [])
const ammunitionSlots = computed(() => build.value?.ammunition_slots || [])
const consumableSlots = computed(() => build.value?.consumable_slots || [])
const holdSlots = computed(() => build.value?.hold_slots || [])

function slotLabel(slot) {
  if (typeof slot === 'string') return optionLabel(slot)
  if (!slot?.item) return ''
  return `${optionLabel(slot.item)} ×${slot.quantity || 1}`
}

function buildTypeLabel(value) {
  return t(`builds.types.${value || 'balanced'}`)
}

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
  const suffix = row.modifier_kind === 'percent' || row.unit === '%' || String(row.effect_key || '').endsWith('_pct') ? '%' : (row.unit ? ` ${row.unit}` : '')
  return `${sign}${roundByPrecision(value, row.precision || 0)}${suffix}`
}

const statRows = computed(() => (build.value?.ship_stats?.stat_rows || []).map((row) => ({
  ...row,
  label: t(`builds.statLabels.${row.key}`),
})))

const upgradeEffectRows = computed(() => statRows.value
  .filter((row) => Number(row.modifier || 0) !== 0)
  .map((row) => ({
    key: row.key,
    label: row.label,
    value: formatModifier(row),
    isDebuff: row.is_debuff,
  })))

async function loadBuild() {
  loading.value = true
  error.value = ''
  try {
    build.value = await getBuild(props.id)
  } catch (err) {
    error.value = err.message || t('builds.detail.loadError')
  } finally {
    loading.value = false
  }
}

onMounted(loadBuild)
</script>

<template>
  <section class="build-detail-page" aria-labelledby="build-detail-title">
    <div class="wire-frame page-frame detail-frame">
      <section class="wire-section build-info-panel">
        <p v-if="loading" class="muted">{{ t('builds.detail.loading') }}</p>
        <p v-else-if="error" class="error-text">{{ error }}</p>

        <template v-else-if="build">
          <div class="detail-header">
            <div>
              <h1 id="build-detail-title">{{ build.build_name }}</h1>
              <p class="muted">
                {{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ build.ship.ship_type }} · {{ buildTypeLabel(build.build_type) }}
              </p>
            </div>
            <RouterLink class="small-action" to="/builds">{{ t('common.back') }}</RouterLink>
          </div>

          <div class="detail-grid">
            <article class="detail-card">
              <span>{{ t('builds.detail.ship') }}</span>
              <strong>{{ build.ship.name }}</strong>
              <small>
                {{ t('builds.list.crew', { current: crewTotal, max: (build.ship_stats?.crew_capacity || build.ship.crew_capacity) }) }} ·
                {{ t('builds.list.sailorMin', { value: (build.ship_stats?.sailor_minimum || build.ship.sailor_minimum) }) }}
              </small>
            </article>
            <article class="detail-card">
              <span>{{ t('builds.detail.buildType') }}</span>
              <strong>{{ buildTypeLabel(build.build_type) }}</strong>
            </article>
            <article class="detail-card">
              <span>{{ t('builds.detail.sail') }}</span>
              <strong>{{ optionLabel(build.sails) || '—' }}</strong>
            </article>
            <article class="detail-card">
              <span>{{ t('builds.detail.lantern') }}</span>
              <strong>{{ optionLabel(build.lantern) || '—' }}</strong>
            </article>
            <article class="detail-card">
              <span>{{ t('builds.detail.shipStats') }}</span>
              <strong>{{ t('builds.detail.weaponTotal', { count: build.ship_stats.weapon_total }) }}</strong>
              <small>{{ t('builds.detail.weaponCapacity', { count: build.ship_stats.weapon_capacity_total || 0 }) }}</small>
              <small>{{ t('builds.detail.statsSummary', { upgrades: build.ship_stats.upgrade_slots_used, max: build.ship_stats.upgrade_slots_available, free: build.ship_stats.crew_remaining }) }}</small>
            </article>
          </div>

          <div v-if="build.ship_stats.stat_warnings?.length" class="wire-section stat-warning-panel">
            <strong>{{ t('builds.detail.statWarnings') }}</strong>
            <ul class="simple-list">
              <li v-for="warning in build.ship_stats.stat_warnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>

          <section class="wire-section build-stat-breakdown detail">
            <div class="stat-breakdown-heading">
              <strong>{{ t('builds.stats.breakdownTitle') }}</strong>
              <span>{{ t('builds.stats.breakdownDetailHint') }}</span>
            </div>
            <div class="stat-comparison-table" role="table" :aria-label="t('builds.stats.breakdownTitle')">
              <div class="stat-table-row stat-table-head" role="row">
                <span role="columnheader">{{ t('builds.stats.columns.stat') }}</span>
                <span role="columnheader">{{ t('builds.stats.columns.base') }}</span>
                <span role="columnheader">{{ t('builds.stats.columns.modifier') }}</span>
                <span role="columnheader">{{ t('builds.stats.columns.effective') }}</span>
              </div>
              <div v-for="row in statRows" :key="row.key" class="stat-table-row" :class="{ 'is-debuff': row.is_debuff, 'has-modifier': Number(row.modifier) !== 0 }" role="row">
                <span role="cell">{{ row.label }}</span>
                <span role="cell">{{ formatStatValue(row.base, row.unit, row.precision) }}</span>
                <span role="cell">{{ formatModifier(row) }}</span>
                <strong role="cell">{{ formatStatValue(row.effective, row.unit, row.precision) }}</strong>
              </div>
            </div>
          </section>

          <div class="detail-grid two-cols">
            <article class="detail-card">
              <span>{{ t('builds.detail.crewDistribution') }}</span>
              <div class="crew-bars readonly-bars">
                <p>{{ t('builds.create.crew.sailors') }}: <strong>{{ build.sailors }}</strong> <small>({{ t('builds.list.sailorMin', { value: (build.ship_stats?.sailor_minimum || build.ship.sailor_minimum) }) }})</small></p>
                <p>{{ t('builds.create.crew.musketeers') }}: <strong>{{ build.musketeers }}</strong></p>
                <p>{{ t('builds.create.crew.soldiers') }}: <strong>{{ build.soldiers }}</strong></p>
                <p>{{ t('builds.create.crew.mercenaries') }}: <strong>{{ build.mercenaries }}</strong></p>
              </div>
            </article>

            <article class="detail-card">
              <span>{{ t('builds.detail.upgrades') }}</span>
              <ul v-if="upgrades.length" class="simple-list">
                <li v-for="upgrade in upgrades" :key="upgrade">{{ optionLabel(upgrade) }}</li>
              </ul>
              <strong v-else>—</strong>
              <div v-if="upgradeEffectRows.length" class="effect-pill-row">
                <span v-for="effect in upgradeEffectRows" :key="effect.key" class="effect-pill" :class="{ 'is-debuff': effect.isDebuff }">
                  {{ effect.label }} {{ effect.value }}
                </span>
              </div>
            </article>
          </div>

          <div class="detail-grid weapon-detail-grid">
            <article v-for="arc in weaponArcRows" :key="arc.key" class="detail-card">
              <span>{{ arc.label }}</span>
              <ul v-if="arc.slots.length" class="simple-list">
                <li v-for="slot in arc.slots" :key="slotLabel(slot)">{{ slotLabel(slot) }}</li>
              </ul>
              <strong v-else>—</strong>
            </article>
          </div>

          <div class="detail-grid two-cols">
            <article class="detail-card">
              <span>{{ t('builds.detail.specialCrew') }}</span>
              <ul v-if="specialCrewSlots.length" class="simple-list">
                <li v-for="slot in specialCrewSlots" :key="slotLabel(slot)">{{ slotLabel(slot) }}</li>
              </ul>
              <strong v-else>—</strong>
            </article>

            <article class="detail-card">
              <span>{{ t('builds.detail.inventory') }}</span>
              <strong>{{ build.ship_stats.inventory_slots_used }} {{ t('common.slots') }}</strong>
              <small>{{ t('builds.detail.inventorySummary', { ammo: ammunitionSlots.length, consumables: consumableSlots.length, hold: holdSlots.length }) }}</small>
            </article>
          </div>

          <div class="detail-grid two-cols">
            <article class="detail-card">
              <span>{{ t('builds.detail.ammunition') }}</span>
              <ul v-if="ammunitionSlots.length" class="simple-list">
                <li v-for="slot in ammunitionSlots" :key="slotLabel(slot)">{{ slotLabel(slot) }}</li>
              </ul>
              <strong v-else>—</strong>
            </article>

            <article class="detail-card">
              <span>{{ t('builds.detail.consumables') }}</span>
              <ul v-if="consumableSlots.length" class="simple-list">
                <li v-for="slot in consumableSlots" :key="slotLabel(slot)">{{ slotLabel(slot) }}</li>
              </ul>
              <strong v-else>—</strong>
            </article>
          </div>

          <div class="detail-grid two-cols">
            <article class="detail-card">
              <span>{{ t('builds.detail.hold') }}</span>
              <ul v-if="holdSlots.length" class="simple-list">
                <li v-for="slot in holdSlots" :key="slotLabel(slot)">{{ slotLabel(slot) }}</li>
              </ul>
              <strong v-else>—</strong>
            </article>
          </div>

          <article class="detail-card notes-card">
            <span>{{ t('builds.detail.details') }}</span>
            <p>{{ build.details || t('builds.detail.noDetails') }}</p>
          </article>
        </template>
      </section>
    </div>
  </section>
</template>
