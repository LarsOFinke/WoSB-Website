<script setup>
import { computed } from 'vue'

import slotPlaceholderSrc from '@/assets/slot-placeholder.svg'
import DiscoveryTileGrid from '@/core/components/DiscoveryTileGrid.vue'
import BuildCrewFields from '@/modules/builds/components/BuildCrewFields.vue'
import BuildInventoryFields from '@/modules/builds/components/BuildInventoryFields.vue'
import BuildOptionPicker from '@/modules/builds/components/BuildOptionPicker.vue'
import BuildStatCommandDeck from '@/modules/builds/components/BuildStatCommandDeck.vue'
import { useBuildDesigner } from '@/modules/builds/composables/useBuildDesigner'
import '@/modules/builds/styles/buildOptionPicker.css'
import '@/modules/builds/styles/buildWorkspace.css'
import '@/shared/styles/discovery.css'
import { localizedBuildDiscoveryGroups } from '@/modules/builds/domain/buildDiscovery'
import {
  composeSpecialistSelection,
  GINGER_SPECIALIST_NAME,
  REGULAR_SPECIALIST_LIMIT,
  splitSpecialistSelection,
} from '@/modules/builds/domain/specialistSelection'

const props = defineProps({
  id: { type: String, default: '' },
})

const {
  optionLabel, t, isEditing, optionCatalog, loading, saving, deleting, error, buildCrewVisuals, buildTypeOptions,
  optionsFor, form, selectedShip, availableWeaponArcs, optionMeta, optionEffects, optionImage,
  selectedShipImage, shipPickerOptions, inventoryCategory, inventoryImage, upgradeEffects, specialCrewEffects,
  formatEffectMap, formatEffects, equipmentUpgradeCount, upgradeAccess, selectedUpgradeNames, upgradeEffectTotals, specialCrewEffectSets,
  specialCrewEffectTotals, equipmentEffectTotals, researchUpgradeEffectTotals, buildEffectTotals,
  buildEffectSets, upgradeSlot5Unlocked, upgradeSlot6Available, upgradeSlot7Available,
  upgradeSlot8Available, availableUpgradeSlots, crewCapacity, sailorMinimum, sailingEfficiency,
  crewTotal, crewRemaining, crewOverLimit, sailorsBelowMinimum, crewInvalid, specialCrewLimit,
  specialCrewOverCapacity, upgradeSlotsUsed, shipStatsPreview, buildStatRows, selectedUpgradeCards,
  activeEffectRows, submitBlockers, canSubmit, slotCount, slotQuantityTotal, allWeaponQuantityTotal,
  isOptionUsed, upgradeOptionsForSlot, upgradeGroupsForSlot, weaponCapacityForField,
  slotLimitForField, weaponOptionsForField, isWeaponFieldUnavailable, weaponFieldOverCapacity,
  weaponSelectionInvalid, allWeaponsValid, isUpgradeSlotDisabled, upgradeSlotPlaceholder,
  quantityMaxForField, reconcileInventoryField, onInventoryItemChange, onInventoryQuantityChange,
  crewMaxFor, onCrewSliderInput, resetCrewAllocation, saveBuild, deleteBuild,
} = useBuildDesigner(props, { slotPlaceholderSrc })

const discoveryGroups = computed(() => localizedBuildDiscoveryGroups(t))
const mortarModification = computed(() => selectedShip.value?.mortar_modification ?? null)
const researchUpgradeEffectSummary = computed(() => formatEffectMap(optionCatalog.value.research_upgrade_slot_effects || {}))
const specialistSelection = computed(() => splitSpecialistSelection(form.special_crew_slots))
const regularSpecialistRows = computed(() => Array.from(
  { length: REGULAR_SPECIALIST_LIMIT },
  (_, index) => specialistSelection.value.regular[index] || { item: '', quantity: 1 },
))
const regularSpecialistOptions = computed(() => optionsFor('special_crew').filter((name) => name !== GINGER_SPECIALIST_NAME))
const sailPickerOptions = computed(() => pickerOptions('sail', optionsFor('sail')))
const lanternPickerOptions = computed(() => pickerOptions('lantern', optionsFor('lantern')))

function pickerOptions(categoryKey, names, disabledNames = new Set()) {
  return names.map((name) => ({
    value: name,
    label: optionLabel(name),
    image: optionImage(categoryKey, name),
    meta: formatEffects(name, categoryKey),
    disabled: disabledNames.has(name),
  }))
}

function upgradePickerGroups(index) {
  return upgradeGroupsForSlot(index).map((group) => ({
    key: group.key,
    label: group.label,
    options: pickerOptions('upgrade', group.options),
  }))
}

function specialistPickerOptions(index) {
  const selectedElsewhere = new Set(
    regularSpecialistRows.value
      .filter((row, rowIndex) => rowIndex !== index && row.item)
      .map((row) => row.item),
  )
  return pickerOptions('special_crew', regularSpecialistOptions.value, selectedElsewhere)
}

function updateRegularSpecialist(index, value) {
  const next = regularSpecialistRows.value.map((slot) => ({ ...slot }))
  next[index].item = value
  form.special_crew_slots = composeSpecialistSelection(next, specialistSelection.value.gingerSelected)
}

function toggleGinger() {
  form.special_crew_slots = composeSpecialistSelection(
    specialistSelection.value.regular,
    !specialistSelection.value.gingerSelected,
  )
}
</script>
<template>
  <section class="build-create-page" aria-labelledby="build-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean build-designer-compact" @submit.prevent="saveBuild">
      <div class="create-topline">
        <div>
          <h1 id="build-create-title">{{ t(isEditing ? 'builds.edit.title' : 'builds.create.title') }}</h1>
          <p>{{ t(isEditing ? 'builds.edit.subtitle' : 'builds.create.subtitle') }}</p>
        </div>
        <RouterLink class="small-action" :to="isEditing ? `/builds/${props.id}` : '/builds'">{{ t('common.back') }}</RouterLink>
      </div>

      <section v-if="selectedShip" class="wire-section build-result-summary" :aria-label="t('discovery.builds.liveResult')">
        <div class="compact-workspace-heading"><span>01</span><div><p class="eyebrow">{{ t('discovery.builds.resultEyebrow') }}</p><h2>{{ t('discovery.builds.liveResult') }}</h2></div></div>
        <BuildStatCommandDeck
          :ship="selectedShip"
          :stat-rows="buildStatRows"
          :upgrade-slots="selectedUpgradeCards"
          :effect-rows="activeEffectRows"
          :crew-total="crewTotal"
          :crew-capacity="crewCapacity"
          :crew-remaining="crewRemaining"
          :weapon-total="shipStatsPreview.weaponTotal"
          :upgrade-slots-available="availableUpgradeSlots"
          :special-crew-total="shipStatsPreview.specialCrew"
        />
      </section>

      <div class="build-config-heading"><span>02</span><div><p class="eyebrow">{{ t('discovery.builds.inputEyebrow') }}</p><h2>{{ t('discovery.builds.configureTitle') }}</h2><p>{{ t('discovery.builds.configureHint') }}</p></div></div>
      <div class="build-config-grid">
      <section class="wire-section form-section identity-section compact-basics-panel" :aria-label="t('builds.create.sections.identity')">
        <div class="section-title">
          <span>01</span>
          <h2>{{ t('builds.create.sections.identity') }}</h2>
        </div>
        <div class="section-fields three-fields">
          <label class="input-panel embedded-field">
            <input
              v-model="form.build_name"
              required
              maxlength="140"
              :placeholder="t('builds.create.buildNamePlaceholder')"
              :aria-label="t('builds.create.buildName')"
            />
          </label>
          <label class="input-panel embedded-field">
            <select v-model="form.build_type" required :aria-label="t('builds.create.buildType')">
              <option v-for="option in buildTypeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <div class="input-panel embedded-field ship-select-field">
            <BuildOptionPicker
              v-model="form.ship_id"
              :options="shipPickerOptions"
              :placeholder="t('builds.create.selectShip')"
              :aria-label="t('builds.create.ship')"
              :disabled="loading"
              :allow-empty="false"
              searchable
              required
              :search-placeholder="t('builds.create.shipSearch.searchPlaceholder')"
              :no-results-text="t('builds.create.shipSearch.noMatches')"
            />
          </div>
        </div>
        <div class="build-classification-editor">
          <div class="classification-editor-heading">
            <div><strong>{{ t('discovery.builds.formTitle') }}</strong><p>{{ t('discovery.builds.formHint') }}</p></div>
            <span>{{ t('discovery.builds.selectionCount', { count: form.classification_tags.length, max: 6 }) }}</span>
          </div>
          <div v-for="group in discoveryGroups" :key="group.key" class="discovery-group">
            <h3>{{ group.label }}</h3>
            <DiscoveryTileGrid
              v-model="form.classification_tags"
              :items="group.items"
              multiple
              compact
            />
          </div>
        </div>
      </section>

      <section class="wire-section form-section equipment-section compact-equipment-panel" :aria-label="t('builds.create.sections.equipment')">
        <div class="section-title">
          <span>02</span>
          <h2>{{ t('builds.create.sections.equipment') }}</h2>
        </div>
        <div class="equipment-unified-grid">
          <div class="square-slot equipment-slot equipment-slot-sail">
            <span class="slot-visual"><img :src="optionImage('sail', form.sails)" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.sail') }}</span>
            <div class="select-shell">
              <BuildOptionPicker
                v-model="form.sails"
                :options="sailPickerOptions"
                :placeholder="t('common.empty')"
                :aria-label="t('builds.create.equipment.sail')"
              />
            </div>
          </div>

          <div v-for="index in equipmentUpgradeCount" :key="index" class="square-slot equipment-slot equipment-slot-upgrade">
            <span class="slot-visual"><img :src="optionImage('upgrade', form[`upgrade_${index}`])" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.upgrade', { index }) }}</span>
            <div class="select-shell">
              <BuildOptionPicker
                v-model="form[`upgrade_${index}`]"
                :groups="upgradePickerGroups(index)"
                :placeholder="upgradeSlotPlaceholder(index)"
                :aria-label="t('builds.create.equipment.upgrade', { index })"
                :disabled="isUpgradeSlotDisabled(index)"
              />
            </div>
          </div>

          <div class="square-slot equipment-slot equipment-slot-lantern">
            <span class="slot-visual"><img :src="optionImage('lantern', form.lantern)" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.lantern') }}</span>
            <div class="select-shell">
              <BuildOptionPicker
                v-model="form.lantern"
                :options="lanternPickerOptions"
                :placeholder="t('common.empty')"
                :aria-label="t('builds.create.equipment.lantern')"
              />
            </div>
          </div>
        </div>
        <button
          type="button"
          class="research-slot-toggle"
          :class="{ 'is-active': form.research_upgrade_slot_unlocked }"
          :aria-pressed="form.research_upgrade_slot_unlocked"
          @click="form.research_upgrade_slot_unlocked = !form.research_upgrade_slot_unlocked"
        >
          <span>{{ form.research_upgrade_slot_unlocked ? '✓' : '+' }}</span>
          <strong>{{ t('builds.create.equipment.researchUpgradeSlot') }}</strong>
          <small>{{ t('builds.create.equipment.researchUpgradeSlotHint') }}</small>
          <small v-if="researchUpgradeEffectSummary" class="research-slot-effects">{{ researchUpgradeEffectSummary }}</small>
        </button>
        <button
          v-if="mortarModification"
          type="button"
          class="research-slot-toggle mortar-modification-toggle"
          :class="{ 'is-active': form.mortar_modification_installed }"
          :aria-pressed="form.mortar_modification_installed"
          @click="form.mortar_modification_installed = !form.mortar_modification_installed"
        >
          <span>{{ form.mortar_modification_installed ? '✓' : '+' }}</span>
          <strong>{{ t('builds.create.equipment.mortarModification') }}</strong>
          <small>
            {{ t('builds.create.equipment.mortarModificationHint', {
              mortars: mortarModification.mortar_capacity,
              broadside: Math.abs(mortarModification.broadside_capacity_delta),
            }) }}
          </small>
        </button>
      </section>

      <section class="wire-section form-section weapons-section compact-weapons-panel" :aria-label="t('builds.create.sections.weapons')">
        <div class="section-title">
          <span>03</span>
          <h2>{{ t('builds.create.sections.weapons') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('builds.create.weapons.hint') }}</p>
        <div class="inventory-grid weapon-arc-grid weapon-arc-grid--adaptive">
          <div v-for="arc in availableWeaponArcs" :key="arc.fieldName" class="inventory-panel weapon-arc-panel">
            <div class="inventory-heading">
              <strong>{{ t(arc.labelKey) }}</strong>
              <span>{{ t('builds.create.weapons.capacity', { count: slotQuantityTotal(arc.fieldName), max: weaponCapacityForField(arc.fieldName) }) }}</span>
            </div>
            <p v-if="isWeaponFieldUnavailable(arc.fieldName)" class="slot-hint">{{ t('builds.create.weapons.unavailable') }}</p>
            <label v-for="(slot, index) in form[arc.fieldName]" :key="`${arc.fieldName}-${index}`" class="inventory-slot-select with-quantity" :class="{ 'is-invalid': weaponSelectionInvalid(arc.fieldName, slot.item) || weaponFieldOverCapacity(arc.fieldName) }">
              <span class="slot-image-cell">
                <img :src="inventoryImage(arc.fieldName, slot.item)" :alt="t(arc.altKey, { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange(arc.fieldName, index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in weaponOptionsForField(arc.fieldName, index)"
                  :key="option"
                  :value="option"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                :max="quantityMaxForField(arc.fieldName, index)"
                :aria-label="t('common.quantity')"
                @input="onInventoryQuantityChange(arc.fieldName, index, $event)"
              />
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section special-crew-section compact-specialists-panel" :aria-label="t('builds.create.sections.specialCrew')">
        <div class="section-title">
          <span>04</span>
          <h2>{{ t('builds.create.sections.specialCrew') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('builds.create.specialCrew.hint') }}</p>
        <div class="inventory-grid special-crew-grid single-column">
          <div class="inventory-panel special-crew-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.specialCrew.title') }}</strong>
              <span>{{ t('discovery.specialists.regularCount', { count: specialistSelection.regular.length, max: specialCrewLimit }) }}</span>
            </div>
            <button type="button" class="ginger-specialist-card" :class="{ 'is-selected': specialistSelection.gingerSelected }" :aria-pressed="specialistSelection.gingerSelected" @click="toggleGinger">
              <span class="slot-image-cell"><img :src="inventoryImage('special_crew_slots', GINGER_SPECIALIST_NAME)" alt="" /></span>
              <span><strong>{{ GINGER_SPECIALIST_NAME }}</strong><small>{{ t('discovery.specialists.gingerHint') }}</small></span>
              <b>{{ specialistSelection.gingerSelected ? '✓' : '+' }}</b>
            </button>
            <div v-for="(slot, index) in regularSpecialistRows" :key="`special-crew-${index}`" class="inventory-slot-select specialist-slot-select">
              <span class="slot-image-cell">
                <img :src="inventoryImage('special_crew_slots', slot.item)" :alt="t('builds.create.specialCrew.alt', { index: index + 1 })" />
              </span>
              <BuildOptionPicker
                :model-value="slot.item"
                :options="specialistPickerOptions(index)"
                :placeholder="t('common.empty')"
                :aria-label="t('builds.create.specialCrew.alt', { index: index + 1 })"
                searchable
                :search-placeholder="t('builds.create.specialCrew.searchPlaceholder')"
                :no-results-text="t('builds.create.specialCrew.noMatches')"
                @update:model-value="updateRegularSpecialist(index, $event)"
              />
            </div>
          </div>
        </div>
      </section>

      <BuildCrewFields
        :t="t"
        :form="form"
        :build-crew-visuals="buildCrewVisuals"
        :crew-invalid="crewInvalid"
        :crew-total="crewTotal"
        :crew-capacity="crewCapacity"
        :crew-remaining="crewRemaining"
        :sailor-minimum="sailorMinimum"
        :sailing-efficiency="sailingEfficiency"
        :sailors-below-minimum="sailorsBelowMinimum"
        :crew-over-limit="crewOverLimit"
        :crew-max-for="crewMaxFor"
        :on-crew-slider-input="onCrewSliderInput"
      />

      <BuildInventoryFields
        :t="t"
        :form="form"
        :slot-count="slotCount"
        :inventory-image="inventoryImage"
        :options-for="optionsFor"
        :option-label="optionLabel"
        :is-option-used="isOptionUsed"
        :on-inventory-item-change="onInventoryItemChange"
        :on-inventory-quantity-change="onInventoryQuantityChange"
      />

      <section class="wire-section form-section details-section compact-details-panel" :aria-label="t('builds.create.sections.details')">
        <div class="section-title">
          <span>07</span>
          <h2>{{ t('builds.create.sections.details') }}</h2>
        </div>
        <label class="input-panel embedded-field details-field">
          <textarea v-model="form.details" rows="4" maxlength="3000" :placeholder="t('builds.create.detailsPlaceholder')"></textarea>
        </label>
      </section>
      </div>

      <section class="wire-section save-readiness" :class="{ 'is-ready': submitBlockers.length === 0 }" aria-live="polite">
        <div>
          <strong>{{ t(submitBlockers.length ? 'builds.create.saveReadiness.blockedTitle' : 'builds.create.saveReadiness.readyTitle') }}</strong>
          <p>{{ t(submitBlockers.length ? 'builds.create.saveReadiness.blockedHint' : 'builds.create.saveReadiness.readyHint') }}</p>
        </div>
        <ul v-if="submitBlockers.length">
          <li v-for="blocker in submitBlockers" :key="blocker">{{ blocker }}</li>
        </ul>
      </section>

      <p v-if="error" class="error-text">{{ error }}</p>

      <div class="form-actions build-editor-actions">
        <button
          v-if="isEditing"
          class="wire-section danger-action build-editor-delete-action"
          type="button"
          :disabled="saving || deleting"
          @click="deleteBuild"
        >
          {{ t('myBuilds.deleteNow') }}
        </button>
        <RouterLink class="wire-section form-button" :to="isEditing ? `/builds/${props.id}` : '/builds'">{{ t('common.cancel') }}</RouterLink>
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit || deleting">
          {{ saving ? t(isEditing ? 'builds.edit.saving' : 'builds.create.saving') : t(isEditing ? 'builds.edit.save' : 'builds.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
