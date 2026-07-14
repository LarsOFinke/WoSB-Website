<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import slotPlaceholderSrc from '@/assets/slot-placeholder.svg'
import { buildCategoryVisuals, buildCrewVisuals, buildVisualUrl } from '@/modules/builds/buildVisuals'
import { absoluteFileUrl } from '@/modules/files/api/files'

import { useLocale } from '@/locales'
import { getBuild, getBuildOptions } from '@/modules/builds/api/builds'
import BuildStatCommandDeck from '@/modules/builds/components/BuildStatCommandDeck.vue'
import { downloadBuildPrintPng, downloadBuildPrintSvg, createBuildPrintPreviewUrl, openBuildPrintWindow } from '@/modules/builds/buildPrintExport'
import { copyBuildShareLink } from '@/modules/builds/shareBuild'
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
const optionCatalog = ref({ categories: [], options: {}, stat_definitions: [], research_upgrade_slot_effects: {}, limits: {} })
const loading = ref(false)
const error = ref('')
const shareStatus = ref('')
const printStatus = ref('')
const printPreviewUrl = ref('')
const printPreviewOpen = ref(false)
const printBusy = ref(false)

const categoryFallbackImages = buildCategoryVisuals
const crewFallbackImages = buildCrewVisuals

const weaponArcRows = computed(() => [
  { key: 'front', label: t('builds.detail.weapons.front'), fieldName: 'front_weapon_slots', slots: build.value?.front_weapon_slots || [] },
  { key: 'rear', label: t('builds.detail.weapons.rear'), fieldName: 'rear_weapon_slots', slots: build.value?.rear_weapon_slots || [] },
  { key: 'port', label: t('builds.detail.weapons.port'), fieldName: 'port_weapon_slots', slots: build.value?.port_weapon_slots || [] },
  { key: 'starboard', label: t('builds.detail.weapons.starboard'), fieldName: 'starboard_weapon_slots', slots: build.value?.starboard_weapon_slots || [] },
  { key: 'mortar', label: t('builds.detail.weapons.mortar'), fieldName: 'mortar_weapon_slots', slots: build.value?.mortar_weapon_slots || [] },
  { key: 'special', label: t('builds.detail.weapons.special'), fieldName: 'special_weapon_slots', slots: build.value?.special_weapon_slots || [] },
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
    build.value.upgrade_7,
    build.value.upgrade_8,
  ].filter(Boolean)
})

const commandDeckUpgradeSlots = computed(() => Array.from({ length: 8 }, (_, offset) => {
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

const crewDistributionRows = computed(() => [
  { key: 'sailors', label: t('builds.create.crew.sailors'), count: build.value?.sailors || 0, image: crewFallbackImages.sailors || slotPlaceholderSrc },
  { key: 'musketeers', label: t('builds.create.crew.musketeers'), count: build.value?.musketeers || 0, image: crewFallbackImages.musketeers || slotPlaceholderSrc },
  { key: 'soldiers', label: t('builds.create.crew.soldiers'), count: build.value?.soldiers || 0, image: crewFallbackImages.soldiers || slotPlaceholderSrc },
  { key: 'mercenaries', label: t('builds.create.crew.mercenaries'), count: build.value?.mercenaries || 0, image: crewFallbackImages.mercenaries || slotPlaceholderSrc },
])

function optionMeta(categoryKey, name) {
  return (optionCatalog.value.options?.[categoryKey] || []).find((option) => option.name === name)
}

function optionImage(categoryKey, name) {
  if (!name) return categoryFallbackImages[categoryKey] || slotPlaceholderSrc
  return absoluteFileUrl(optionMeta(categoryKey, name)?.image_url)
    || categoryFallbackImages[categoryKey]
    || slotPlaceholderSrc
}

function inventoryCategory(fieldName) {
  if (fieldName.includes('weapon')) return 'weapon'
  if (fieldName === 'special_crew_slots') return 'special_crew'
  if (fieldName === 'ammunition_slots') return 'ammunition'
  if (fieldName === 'consumable_slots') return 'consumable'
  if (fieldName === 'hold_slots') return 'hold'
  return ''
}

function slotItem(slot) {
  if (typeof slot === 'string') return slot
  return slot?.item || ''
}

function slotLabel(slot) {
  if (typeof slot === 'string') return optionLabel(slot)
  if (!slot?.item) return ''
  return `${optionLabel(slot.item)} ×${slot.quantity || 1}`
}

function slotQuantity(slot) {
  if (typeof slot === 'string') return null
  return Number(slot?.quantity || 0) > 1 ? Number(slot.quantity) : null
}

function inventoryImage(fieldName, slot) {
  return optionImage(inventoryCategory(fieldName), slotItem(slot))
}

function specialistLabel(slot) {
  return optionLabel(typeof slot === 'string' ? slot : slot?.item)
}

function shareLinkMeta(slot) {
  return typeof slot === 'string' ? '' : (slot?.notes || '')
}

async function shareBuild() {
  shareStatus.value = ''
  try {
    await copyBuildShareLink(build.value.id)
    shareStatus.value = t('builds.share.copied')
  } catch {
    shareStatus.value = t('builds.share.error')
  }
}

function revokePrintPreview() {
  if (printPreviewUrl.value) URL.revokeObjectURL(printPreviewUrl.value)
  printPreviewUrl.value = ''
}

function ensurePrintPreview() {
  revokePrintPreview()
  printPreviewUrl.value = createBuildPrintPreviewUrl(build.value, { t, optionLabel })
  printPreviewOpen.value = true
}

async function prepareBuildImage() {
  if (!build.value) return
  printStatus.value = ''
  printBusy.value = true
  try {
    ensurePrintPreview()
    printStatus.value = t('builds.print.previewReady')
  } catch {
    printStatus.value = t('builds.print.error')
  } finally {
    printBusy.value = false
  }
}

async function downloadBuildImagePng() {
  if (!build.value) return
  printStatus.value = ''
  printBusy.value = true
  try {
    if (!printPreviewUrl.value) ensurePrintPreview()
    await downloadBuildPrintPng(build.value, { t, optionLabel })
    printStatus.value = t('builds.print.downloadedPng')
  } catch {
    printStatus.value = t('builds.print.error')
  } finally {
    printBusy.value = false
  }
}

function downloadBuildImageSvg() {
  if (!build.value) return
  printStatus.value = ''
  try {
    if (!printPreviewUrl.value) ensurePrintPreview()
    downloadBuildPrintSvg(build.value, { t, optionLabel })
    printStatus.value = t('builds.print.downloadedSvg')
  } catch {
    printStatus.value = t('builds.print.error')
  }
}

function printBuildSheet() {
  if (!build.value) return
  printStatus.value = ''
  try {
    openBuildPrintWindow(build.value, { t, optionLabel })
    printStatus.value = t('builds.print.windowOpened')
  } catch {
    printStatus.value = t('builds.print.error')
  }
}

function closePrintPreview() {
  printPreviewOpen.value = false
  revokePrintPreview()
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
    optionCatalog.value = await getBuildOptions(build.value?.ship?.id || build.value?.ship_id || null)
  } catch (err) {
    error.value = err.message || t('builds.detail.loadError')
  } finally {
    loading.value = false
  }
}

onMounted(loadBuild)
onBeforeUnmount(revokePrintPreview)
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
              <button class="small-action" type="button" @click="shareBuild">{{ t('builds.share.action') }}</button>
              <button class="small-action" type="button" :disabled="printBusy" @click="prepareBuildImage">
                {{ printBusy ? t('builds.print.preparing') : t('builds.print.action') }}
              </button>
              <RouterLink v-if="canEdit" class="small-action primary-action" :to="`/builds/${build.id}/edit`">
                {{ t('builds.edit.action') }}
              </RouterLink>
              <RouterLink class="small-action" to="/builds">{{ t('common.back') }}</RouterLink>
            </div>
          </div>

          <p v-if="shareStatus" class="share-status" role="status">{{ shareStatus }}</p>
          <p v-if="printStatus" class="share-status" role="status">{{ printStatus }}</p>

          <section v-if="printPreviewOpen" class="wire-section build-print-export-panel">
            <div class="build-print-export-header">
              <div>
                <span class="command-deck-eyebrow">{{ t('builds.print.eyebrow') }}</span>
                <h2>{{ t('builds.print.previewTitle') }}</h2>
                <p class="muted">{{ t('builds.print.previewHint') }}</p>
              </div>
              <div class="build-print-export-actions">
                <button class="small-action" type="button" @click="downloadBuildImagePng">{{ t('builds.print.downloadPng') }}</button>
                <button class="small-action" type="button" @click="downloadBuildImageSvg">{{ t('builds.print.downloadSvg') }}</button>
                <button class="small-action primary-action" type="button" @click="printBuildSheet">{{ t('builds.print.printAction') }}</button>
                <button class="small-action" type="button" @click="closePrintPreview">{{ t('common.close') }}</button>
              </div>
            </div>
            <div class="build-print-export-preview">
              <img :src="printPreviewUrl" :alt="t('builds.print.previewTitle')" />
            </div>
          </section>

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

          <div class="detail-grid command-deck-meta-grid build-detail-visual-grid">
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.buildType') }}</span>
              <strong>{{ buildTypeLabel(build.build_type) }}</strong>
            </article>
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.sail') }}</span>
              <div class="detail-visual-inline">
                <span class="slot-image-cell detail-icon-cell"><img :src="optionImage('sail', build.sails)" alt="" /></span>
                <strong>{{ optionLabel(build.sails) || '—' }}</strong>
              </div>
            </article>
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.lantern') }}</span>
              <div class="detail-visual-inline">
                <span class="slot-image-cell detail-icon-cell"><img :src="optionImage('lantern', build.lantern)" alt="" /></span>
                <strong>{{ optionLabel(build.lantern) || '—' }}</strong>
              </div>
            </article>
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.researchUpgradeSlot') }}</span>
              <strong>{{ build.research_upgrade_slot_unlocked ? t('builds.detail.researchUpgradeSlotActive') : t('builds.detail.researchUpgradeSlotInactive') }}</strong>
            </article>
            <article class="detail-card detail-visual-card">
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

          <div class="detail-grid two-cols build-detail-section-grid">
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.crewDistribution') }}</span>
              <div class="detail-crew-grid">
                <div v-for="row in crewDistributionRows" :key="row.key" class="detail-crew-row">
                  <span class="slot-image-cell detail-icon-cell"><img :src="row.image" alt="" /></span>
                  <div>
                    <strong>{{ row.count }}</strong>
                    <small>{{ row.label }}</small>
                  </div>
                </div>
              </div>
              <small>{{ t('builds.list.sailorMin', { value: (build.ship_stats?.sailor_minimum || build.ship.sailor_minimum) }) }}</small>
            </article>

            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.upgrades') }}</span>
              <ul v-if="upgrades.length" class="build-visual-list">
                <li v-for="(upgrade, index) in upgrades" :key="`${upgrade}-${index}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="optionImage('upgrade', upgrade)" alt="" /></span>
                  <div>
                    <strong>{{ optionLabel(upgrade) }}</strong>
                    <small>{{ shareLinkMeta(optionMeta('upgrade', upgrade)) || t('builds.commandDeck.availableUpgrade') }}</small>
                  </div>
                </li>
              </ul>
              <strong v-else>—</strong>
              <div v-if="activeEffectRows.length" class="effect-pill-row">
                <span v-for="effect in activeEffectRows" :key="effect.key" class="effect-pill" :class="{ 'is-debuff': effect.isDebuff }">
                  {{ effect.label }} {{ effect.value }}
                </span>
              </div>
            </article>
          </div>

          <div class="detail-grid weapon-detail-grid build-detail-section-grid">
            <article v-for="arc in weaponArcRows" :key="arc.key" class="detail-card detail-visual-card">
              <span>{{ arc.label }}</span>
              <ul v-if="arc.slots.length" class="build-visual-list">
                <li v-for="(slot, index) in arc.slots" :key="`${arc.key}-${index}-${slotLabel(slot)}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage(arc.fieldName, slot)" alt="" /></span>
                  <div>
                    <strong>{{ slotLabel(slot) }}</strong>
                    <small v-if="slotQuantity(slot)">×{{ slotQuantity(slot) }}</small>
                    <small v-else>{{ t('builds.detail.shipStats') }}</small>
                  </div>
                </li>
              </ul>
              <strong v-else>—</strong>
            </article>
          </div>

          <div class="detail-grid two-cols build-detail-section-grid">
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.specialCrew') }}</span>
              <ul v-if="specialCrewSlots.length" class="build-visual-list">
                <li v-for="(slot, index) in specialCrewSlots" :key="`special-${index}-${specialistLabel(slot)}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage('special_crew_slots', slot)" alt="" /></span>
                  <div>
                    <strong>{{ specialistLabel(slot) }}</strong>
                    <small>{{ shareLinkMeta(slot) || t('builds.commandDeck.specialistMetric', { value: 1 }) }}</small>
                  </div>
                </li>
              </ul>
              <strong v-else>—</strong>
            </article>

            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.inventory') }}</span>
              <div class="detail-inventory-overview">
                <div>
                  <strong>{{ build.ship_stats.inventory_slots_used }}</strong>
                  <small>{{ t('common.slots') }}</small>
                </div>
                <div>
                  <strong>{{ ammunitionSlots.length }}</strong>
                  <small>{{ t('builds.detail.ammunition') }}</small>
                </div>
                <div>
                  <strong>{{ consumableSlots.length }}</strong>
                  <small>{{ t('builds.detail.consumables') }}</small>
                </div>
                <div>
                  <strong>{{ holdSlots.length }}</strong>
                  <small>{{ t('builds.detail.hold') }}</small>
                </div>
              </div>
              <small>{{ t('builds.detail.inventorySummary', { ammo: ammunitionSlots.length, consumables: consumableSlots.length, hold: holdSlots.length }) }}</small>
            </article>
          </div>

          <div class="detail-grid two-cols build-detail-section-grid">
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.ammunition') }}</span>
              <ul v-if="ammunitionSlots.length" class="build-visual-list">
                <li v-for="(slot, index) in ammunitionSlots" :key="`ammo-${index}-${slotLabel(slot)}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage('ammunition_slots', slot)" alt="" /></span>
                  <div>
                    <strong>{{ slotLabel(slot) }}</strong>
                    <small v-if="slotQuantity(slot)">×{{ slotQuantity(slot) }}</small>
                    <small v-else>—</small>
                  </div>
                </li>
              </ul>
              <strong v-else>—</strong>
            </article>

            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.consumables') }}</span>
              <ul v-if="consumableSlots.length" class="build-visual-list">
                <li v-for="(slot, index) in consumableSlots" :key="`consumable-${index}-${slotLabel(slot)}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage('consumable_slots', slot)" alt="" /></span>
                  <div>
                    <strong>{{ slotLabel(slot) }}</strong>
                    <small v-if="slotQuantity(slot)">×{{ slotQuantity(slot) }}</small>
                    <small v-else>—</small>
                  </div>
                </li>
              </ul>
              <strong v-else>—</strong>
            </article>
          </div>

          <div class="detail-grid two-cols build-detail-section-grid">
            <article class="detail-card detail-visual-card">
              <span>{{ t('builds.detail.hold') }}</span>
              <ul v-if="holdSlots.length" class="build-visual-list">
                <li v-for="(slot, index) in holdSlots" :key="`hold-${index}-${slotLabel(slot)}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage('hold_slots', slot)" alt="" /></span>
                  <div>
                    <strong>{{ slotLabel(slot) }}</strong>
                    <small v-if="slotQuantity(slot)">×{{ slotQuantity(slot) }}</small>
                    <small v-else>—</small>
                  </div>
                </li>
              </ul>
              <strong v-else>—</strong>
            </article>
          </div>

          <article class="detail-card notes-card">
            <span>{{ t('builds.detail.details') }}</span>
            <p class="preserve-lines">{{ build.details || t('builds.detail.noDetails') }}</p>
          </article>
        </template>
      </section>
    </div>
  </section>
</template>
