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
  optionLabel, t, build, loading, error, shareStatus, printStatus, printPreviewUrl,
  printPreviewOpen, printBusy, weaponArcRows, crewTotal, canEdit, upgrades,
  commandDeckUpgradeSlots, regularSpecialCrewSlots, gingerSpecialCrewSlot,
  classificationLabels, ammunitionSlots, consumableSlots, holdSlots,
  crewDistributionRows, optionMeta, optionImage, slotItem, slotLabel, slotQuantity,
  inventoryImage, specialistLabel, shareLinkMeta, shareBuild, prepareBuildImage,
  downloadBuildImagePng, downloadBuildImageSvg, printBuildSheet, closePrintPreview,
  buildTypeLabel, statRows, activeEffectRows,
} = useBuildDetailPage(props)

function crewCapacity() {
  return Number(build.value?.ship_stats?.crew_capacity || build.value?.ship?.crew_capacity || 1)
}
</script>

<template>
  <section class="build-detail-page build-detail-command-page" aria-labelledby="build-detail-title">
    <div class="wire-frame page-frame detail-frame build-detail-command-frame">
      <p v-if="loading" class="muted build-detail-state">{{ t('builds.detail.loading') }}</p>
      <p v-else-if="error" class="error-text build-detail-state">{{ error }}</p>

      <template v-else-if="build">
        <header class="build-detail-command-header">
          <RouterLink class="build-detail-back-link" to="/builds">← {{ t('common.back') }}</RouterLink>
          <div class="build-detail-command-heading">
            <div>
              <span class="command-deck-eyebrow">{{ t('builds.print.eyebrow') }}</span>
              <h1 id="build-detail-title">{{ build.build_name }}</h1>
              <p class="build-detail-ship-line">
                {{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }} · {{ build.ship.ship_type }} · {{ buildTypeLabel(build.build_type) }}
              </p>
              <div v-if="classificationLabels.length" class="build-detail-tag-row">
                <span v-for="classification in classificationLabels" :key="classification.value" class="build-detail-tag">
                  {{ classification.label }}
                </span>
              </div>
            </div>
            <div class="detail-header-actions build-detail-command-actions">
              <button class="small-action" type="button" @click="shareBuild">{{ t('builds.share.action') }}</button>
              <button class="small-action" type="button" :disabled="printBusy" @click="prepareBuildImage">
                {{ printBusy ? t('builds.print.preparing') : t('builds.print.action') }}
              </button>
              <RouterLink v-if="canEdit" class="small-action primary-action" :to="`/builds/${build.id}/edit`">
                {{ t('builds.edit.action') }}
              </RouterLink>
            </div>
          </div>
        </header>

        <p v-if="shareStatus" class="share-status" role="status">{{ shareStatus }}</p>
        <p v-if="printStatus" class="share-status" role="status">{{ printStatus }}</p>

        <section v-if="printPreviewOpen" class="build-print-export-panel build-print-sheet-preview">
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
              <button class="small-action" type="button" @click="closePrintPreview">{{ t('common.cancel') }}</button>
            </div>
          </div>
          <div class="build-print-export-preview">
            <img :src="printPreviewUrl" :alt="t('builds.print.previewTitle')" />
          </div>
        </section>

        <div class="build-result-summary build-detail-result-summary">
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
        </div>

        <section v-if="build.ship_stats.stat_warnings?.length" class="stat-warning-panel build-detail-warning-panel">
          <strong>{{ t('builds.detail.statWarnings') }}</strong>
          <ul class="simple-list">
            <li v-for="warning in build.ship_stats.stat_warnings" :key="warning">{{ warning }}</li>
          </ul>
        </section>

        <div class="build-detail-command-layout">
          <div class="build-detail-command-column">
            <section class="build-readout-panel" aria-labelledby="build-configuration-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">01</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.commandDeck.configurationEyebrow') }}</span>
                  <h2 id="build-configuration-title">{{ t('builds.print.configurationTitle') }}</h2>
                </div>
              </header>
              <div class="build-configuration-strip">
                <div class="build-configuration-item">
                  <span class="slot-image-cell detail-icon-cell"><img :src="optionImage('sail', build.sails)" alt="" /></span>
                  <span><small>{{ t('builds.detail.sail') }}</small><strong>{{ optionLabel(build.sails) || '—' }}</strong></span>
                </div>
                <div class="build-configuration-item">
                  <span class="slot-image-cell detail-icon-cell"><img :src="optionImage('lantern', build.lantern)" alt="" /></span>
                  <span><small>{{ t('builds.detail.lantern') }}</small><strong>{{ optionLabel(build.lantern) || '—' }}</strong></span>
                </div>
                <div class="build-configuration-item">
                  <span class="build-configuration-marker" aria-hidden="true">R</span>
                  <span><small>{{ t('builds.detail.researchUpgradeSlot') }}</small><strong>{{ build.research_upgrade_slot_unlocked ? t('builds.detail.researchUpgradeSlotActive') : t('builds.detail.researchUpgradeSlotInactive') }}</strong></span>
                </div>
              </div>
            </section>

            <section class="build-readout-panel" aria-labelledby="build-upgrades-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">02</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.commandDeck.configurationEyebrow') }}</span>
                  <h2 id="build-upgrades-title">{{ t('builds.detail.upgrades') }}</h2>
                </div>
              </header>
              <ol v-if="upgrades.length" class="build-readout-list build-upgrade-readout-list">
                <li v-for="(upgrade, index) in upgrades" :key="`${upgrade}-${index}`">
                  <span class="build-readout-number">{{ String(index + 1).padStart(2, '0') }}</span>
                  <span class="slot-image-cell detail-icon-cell"><img :src="optionImage('upgrade', upgrade)" alt="" /></span>
                  <span class="build-readout-copy">
                    <strong>{{ optionLabel(upgrade) }}</strong>
                    <small>{{ shareLinkMeta(optionMeta('upgrade', upgrade)) || t('builds.commandDeck.availableUpgrade') }}</small>
                  </span>
                </li>
              </ol>
              <p v-else class="build-readout-empty">—</p>
            </section>

            <section class="build-readout-panel" aria-labelledby="build-weapons-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">03</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.detail.shipStats') }}</span>
                  <h2 id="build-weapons-title">{{ t('builds.print.weaponLoadoutTitle') }}</h2>
                </div>
                <strong class="build-readout-total">{{ build.ship_stats.weapon_total || 0 }}</strong>
              </header>
              <div class="build-weapon-readout">
                <div v-for="arc in weaponArcRows" :key="arc.key" class="build-weapon-arc-row" :class="{ 'is-empty': !arc.slots.length }">
                  <span class="build-weapon-arc-label">{{ arc.label }}</span>
                  <ul v-if="arc.slots.length">
                    <li v-for="(slot, index) in arc.slots" :key="`${arc.key}-${index}-${slotLabel(slot)}`">
                      <img :src="inventoryImage(arc.fieldName, slot)" alt="" />
                      <span>{{ optionLabel(slotItem(slot)) }}</span>
                      <small v-if="slotQuantity(slot)">×{{ slotQuantity(slot) }}</small>
                    </li>
                  </ul>
                  <span v-else class="build-readout-empty">—</span>
                </div>
              </div>
            </section>
          </div>

          <div class="build-detail-command-column">
            <section class="build-readout-panel" aria-labelledby="build-crew-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">04</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.crewConsole.eyebrow') }}</span>
                  <h2 id="build-crew-title">{{ t('builds.detail.crewDistribution') }}</h2>
                </div>
                <strong class="build-readout-total">{{ crewTotal }}/{{ crewCapacity() }}</strong>
              </header>
              <div class="build-crew-readout">
                <div v-for="row in crewDistributionRows" :key="row.key" class="build-crew-meter-row">
                  <img :src="row.image" alt="" />
                  <span>{{ row.label }}</span>
                  <progress :value="row.count" :max="crewCapacity()">{{ row.count }}</progress>
                  <strong>{{ row.count }}</strong>
                </div>
              </div>
              <p class="build-readout-footnote">{{ t('builds.create.crew.sailorMinimum', { value: build.ship_stats?.sailor_minimum || build.ship.sailor_minimum }) }}</p>
            </section>

            <section class="build-readout-panel" aria-labelledby="build-specialists-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">05</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.detail.specialCrew') }}</span>
                  <h2 id="build-specialists-title">{{ t('builds.detail.specialCrew') }}</h2>
                </div>
                <strong class="build-readout-total">{{ regularSpecialCrewSlots.length }}/4</strong>
              </header>
              <ul v-if="regularSpecialCrewSlots.length" class="build-readout-list build-specialist-readout-list">
                <li v-for="(slot, index) in regularSpecialCrewSlots" :key="`special-${index}-${specialistLabel(slot)}`">
                  <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage('special_crew_slots', slot)" alt="" /></span>
                  <span class="build-readout-copy">
                    <strong>{{ specialistLabel(slot) }}</strong>
                    <small>{{ shareLinkMeta(slot) || t('builds.commandDeck.specialistMetric', { value: 1 }) }}</small>
                  </span>
                </li>
              </ul>
              <p v-else class="build-readout-empty">—</p>
              <div v-if="gingerSpecialCrewSlot" class="build-ginger-readout">
                <span class="slot-image-cell detail-icon-cell"><img :src="inventoryImage('special_crew_slots', gingerSpecialCrewSlot)" alt="" /></span>
                <span class="build-readout-copy">
                  <small>+1</small>
                  <strong>{{ specialistLabel(gingerSpecialCrewSlot) }}</strong>
                  <span>{{ shareLinkMeta(gingerSpecialCrewSlot) || t('builds.commandDeck.specialistMetric', { value: 1 }) }}</span>
                </span>
              </div>
            </section>

            <section class="build-readout-panel" aria-labelledby="build-inventory-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">06</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.detail.inventory') }}</span>
                  <h2 id="build-inventory-title">{{ t('builds.print.inventoryTitle') }}</h2>
                </div>
                <strong class="build-readout-total">{{ build.ship_stats.inventory_slots_used || 0 }}</strong>
              </header>
              <div class="build-inventory-readout">
                <section v-for="group in [
                  { key: 'ammunition_slots', label: t('builds.detail.ammunition'), slots: ammunitionSlots },
                  { key: 'consumable_slots', label: t('builds.detail.consumables'), slots: consumableSlots },
                  { key: 'hold_slots', label: t('builds.detail.hold'), slots: holdSlots },
                ]" :key="group.key">
                  <h3>{{ group.label }} <span>{{ group.slots.length }}</span></h3>
                  <ul v-if="group.slots.length">
                    <li v-for="(slot, index) in group.slots" :key="`${group.key}-${index}-${slotLabel(slot)}`">
                      <img :src="inventoryImage(group.key, slot)" alt="" />
                      <span>{{ optionLabel(slotItem(slot)) }}</span>
                      <small v-if="slotQuantity(slot)">×{{ slotQuantity(slot) }}</small>
                    </li>
                  </ul>
                  <p v-else class="build-readout-empty">—</p>
                </section>
              </div>
            </section>

            <section class="build-readout-panel build-notes-readout" aria-labelledby="build-notes-title">
              <header class="build-readout-panel-header">
                <span class="build-readout-index">07</span>
                <div>
                  <span class="command-deck-eyebrow">{{ t('builds.detail.details') }}</span>
                  <h2 id="build-notes-title">{{ t('builds.print.notesTitle') }}</h2>
                </div>
              </header>
              <p class="preserve-lines">{{ build.details || t('builds.detail.noDetails') }}</p>
            </section>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
