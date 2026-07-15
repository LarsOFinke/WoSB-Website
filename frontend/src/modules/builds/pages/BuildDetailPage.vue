<script setup>
import BuildStatCommandDeck from '@/modules/builds/components/BuildStatCommandDeck.vue'
import { useBuildDetailPage } from '@/modules/builds/composables/useBuildDetailPage.js'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const {
  optionLabel, t, user, build, optionCatalog,
  loading, error, shareStatus, printStatus, printPreviewUrl,
  printPreviewOpen, printBusy, categoryFallbackImages, crewFallbackImages, weaponArcRows,
  crewTotal, canEdit, upgrades, commandDeckUpgradeSlots, specialCrewSlots,
  ammunitionSlots, consumableSlots, holdSlots, crewDistributionRows, optionMeta,
  optionImage, inventoryCategory, slotItem, slotLabel, slotQuantity,
  inventoryImage, specialistLabel, shareLinkMeta, shareBuild, revokePrintPreview,
  ensurePrintPreview, prepareBuildImage, downloadBuildImagePng, downloadBuildImageSvg, printBuildSheet,
  closePrintPreview, buildTypeLabel, roundByPrecision, formatModifier, statRows,
  activeEffectRows, loadBuild,
} = useBuildDetailPage(props)
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
