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

const crewTotal = computed(() => {
  if (!build.value) return 0
  return (
    build.value.sailors +
    build.value.soldiers +
    build.value.musketeers +
    build.value.mercenaries
  )
})

const upgrades = computed(() => {
  if (!build.value) return []
  return [
    build.value.upgrade_1,
    build.value.upgrade_2,
    build.value.upgrade_3,
    build.value.upgrade_4,
    build.value.upgrade_5,
  ].filter(Boolean)
})

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
                {{ t('builds.list.crew', { current: crewTotal, max: build.ship.crew_capacity }) }} ·
                {{ t('builds.list.sailorMin', { value: build.ship.sailor_minimum }) }}
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
              <span>{{ t('builds.detail.inventory') }}</span>
              <strong>{{ ammunitionSlots.length + consumableSlots.length + holdSlots.length }} {{ t('common.slots') }}</strong>
              <small>{{ t('builds.detail.inventorySummary', { ammo: ammunitionSlots.length, consumables: consumableSlots.length, hold: holdSlots.length }) }}</small>
            </article>
          </div>

          <div class="detail-grid two-cols">
            <article class="detail-card">
              <span>{{ t('builds.detail.crewDistribution') }}</span>
              <div class="crew-bars readonly-bars">
                <p>{{ t('builds.create.crew.sailors') }}: <strong>{{ build.sailors }}</strong> <small>({{ t('builds.list.sailorMin', { value: build.ship.sailor_minimum }) }})</small></p>
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
