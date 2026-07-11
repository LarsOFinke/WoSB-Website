<script setup>
import { computed, onMounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { getBuild } from '@/modules/builds/api/builds'
import BuildStatCommandDeck from '@/modules/builds/components/BuildStatCommandDeck.vue'
import { useSession } from '@/modules/accounts/session'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const { optionLabel, t } = useLocale()
const { user } = useSession()

const build = ref(null)
const loading = ref(false)
const error = ref('')

const weaponArcRows = computed(() => [
  { key: 'front', label: t('builds.detail.weapons.front'), slots: build.value?.front_weapon_slots || [] },
  { key: 'rear', label: t('builds.detail.weapons.rear'), slots: build.value?.rear_weapon_slots || [] },
  { key: 'port', label: t('builds.detail.weapons.port'), slots: build.value?.port_weapon_slots || [] },
  { key: 'starboard', label: t('builds.detail.weapons.starboard'), slots: build.value?.starboard_weapon_slots || [] },
  { key: 'mortar', label: t('builds.detail.weapons.mortar'), slots: build.value?.mortar_weapon_slots || [] },
  { key: 'special', label: t('builds.detail.weapons.special'), slots: build.value?.special_weapon_slots || [] },
])

const crewTotal = computed(() => build.value?.ship_stats?.crew_total || 0)

const canEdit = computed(() => Number(build.value?.owner_id) === Number(user.value?.id) && !build.value?.is_official_template)

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

const commandDeckUpgradeSlots = computed(() => Array.from({ length: 6 }, (_, offset) => {
  const index = offset + 1
  const name = build.value?.[`upgrade_${index}`] || ''
  return {
    index,
    name,
    label: name ? optionLabel(name) : '',
    effects: '',
    locked: index > Number(build.value?.ship_stats?.upgrade_slots_available || 0),
  }
}))

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

function formatModifier(row) {
  const value = Number(row.modifier || 0)
  if (!Number.isFinite(value) || value === 0) return '—'
  const sign = value > 0 ? '+' : ''
  const suffix = row.modifier_kind === 'percent' || row.unit === '%' || String(row.effect_key || '').endsWith('_pct') ? '%' : (row.unit ? ` ${row.unit}` : '')
  return `${sign}${roundByPrecision(value, row.precision || 0)}${suffix}`
}

const statRows = computed(() => (build.value?.ship_stats?.stat_rows || []).map((row) => {
  const path = `builds.statLabels.${row.key}`
  const translated = t(path)
  return {
    ...row,
    label: translated === path ? (row.label || String(row.key).replaceAll('_', ' ')) : translated,
  }
}))

const activeEffectRows = computed(() => statRows.value
  .filter((row) => Number(row.modifier || 0) !== 0)
  .map((row) => ({
    ...row,
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
            <div class="detail-header-actions">
              <RouterLink v-if="canEdit" class="small-action primary-action" :to="`/builds/${build.id}/edit`">
                {{ t('builds.edit.action') }}
              </RouterLink>
              <RouterLink class="small-action" to="/builds">{{ t('common.back') }}</RouterLink>
            </div>
          </div>

          <BuildStatCommandDeck
            :ship="build.ship"
            :stat-rows="statRows"
            :upgrade-slots="commandDeckUpgradeSlots"
            :effect-rows="activeEffectRows"
            :crew-total="crewTotal"
            :crew-capacity="build.ship_stats?.crew_capacity || build.ship.crew_capacity"
            :crew-remaining="build.ship_stats?.crew_remaining || 0"
            :weapon-total="build.ship_stats?.weapon_total || 0"
            :upgrade-slots-available="build.ship_stats?.upgrade_slots_available || 0"
            :special-crew-total="build.ship_stats?.special_crew_total || 0"
            detail-mode
          />

          <div class="detail-grid command-deck-meta-grid">
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
              <span>{{ t('builds.detail.researchUpgradeSlot') }}</span>
              <strong>{{ build.research_upgrade_slot_unlocked ? t('builds.detail.researchUpgradeSlotActive') : t('builds.detail.researchUpgradeSlotInactive') }}</strong>
            </article>
            <article class="detail-card">
              <span>{{ t('builds.detail.shipStats') }}</span>
              <strong>{{ t('builds.detail.weaponTotal', { count: build.ship_stats.weapon_total }) }}</strong>
              <small>{{ t('builds.detail.weaponCapacity', { count: build.ship_stats.weapon_capacity_total || 0 }) }}</small>
            </article>
          </div>

          <div v-if="build.ship_stats.stat_warnings?.length" class="wire-section stat-warning-panel">
            <strong>{{ t('builds.detail.statWarnings') }}</strong>
            <ul class="simple-list">
              <li v-for="warning in build.ship_stats.stat_warnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>

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
              <div v-if="activeEffectRows.length" class="effect-pill-row">
                <span v-for="effect in activeEffectRows" :key="effect.key" class="effect-pill" :class="{ 'is-debuff': effect.isDebuff }">
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
