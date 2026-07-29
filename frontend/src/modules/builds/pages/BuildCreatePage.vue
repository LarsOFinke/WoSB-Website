<script setup>
import { computed } from 'vue'

import slotPlaceholderSrc from '@/assets/slot-placeholder.svg'
import DiscoveryTileGrid from '@/core/components/DiscoveryTileGrid.vue'
import BuildOptionPicker from '@/modules/builds/components/BuildOptionPicker.vue'
import BuildStatCommandDeck from '@/modules/builds/components/BuildStatCommandDeck.vue'
import { useBuildDesigner } from '@/modules/builds/composables/useBuildDesigner'
import '@/modules/builds/styles/buildOptionPicker.css'
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
  optionLabel, t, isEditing, ships, optionCatalog, loading, saving, deleting, error, buildCrewVisuals, buildTypeOptions,
  optionsFor, form, selectedShip, availableWeaponArcs, optionMeta, optionEffects, optionImage,
  selectedShipImage, inventoryCategory, inventoryImage, upgradeEffects, specialCrewEffects,
  formatEffects, equipmentUpgradeCount, upgradeAccess, selectedUpgradeNames, upgradeEffectTotals, specialCrewEffectSets,
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

function updateClassificationTags(tags) {
  if (tags.length <= 6) form.classification_tags = tags
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
          <label class="input-panel embedded-field ship-select-field">
            <select v-model="form.ship_id" required :disabled="loading" :aria-label="t('builds.create.ship')">
              <option value="" disabled>{{ t('builds.create.selectShip') }}</option>
              <option v-for="ship in ships" :key="ship.id" :value="ship.id">{{ ship.name }}</option>
            </select>
          </label>
        </div>
        <div class="build-classification-editor">
          <div class="classification-editor-heading">
            <div><strong>{{ t('discovery.builds.formTitle') }}</strong><p>{{ t('discovery.builds.formHint') }}</p></div>
            <span>{{ t('discovery.builds.selectionCount', { count: form.classification_tags.length, max: 6 }) }}</span>
          </div>
          <div v-for="group in discoveryGroups" :key="group.key" class="discovery-group">
            <h3>{{ group.label }}</h3>
            <DiscoveryTileGrid
              :model-value="form.classification_tags"
              :items="group.items"
              multiple
              compact
              @update:model-value="updateClassificationTags"
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

      <section class="wire-section form-section crew-section compact-crew-panel" :aria-label="t('builds.create.sections.crew')">
        <div class="section-title">
          <span>05</span>
          <h2>{{ t('builds.create.sections.crew') }}</h2>
        </div>
        <div class="crew-allocation-console" :class="{ 'is-invalid': crewInvalid }">
          <div class="crew-allocation-header">
            <div>
              <span>{{ t('builds.crewConsole.eyebrow') }}</span>
              <strong>{{ t('builds.crewConsole.title') }}</strong>
            </div>
            <div class="crew-allocation-total">
              <strong>{{ crewTotal }}/{{ crewCapacity || '—' }}</strong>
              <span>{{ t('builds.create.crew.free', { value: crewRemaining }) }}</span>
            </div>
          </div>
          <div class="crew-allocation-meter" :aria-label="t('builds.create.crew.total', { current: crewTotal, max: crewCapacity || '—' })">
            <span class="crew-meter-sailors" :style="{ width: `${crewCapacity ? (Number(form.sailors) / crewCapacity) * 100 : 0}%` }"></span>
            <span class="crew-meter-musketeers" :style="{ width: `${crewCapacity ? (Number(form.musketeers) / crewCapacity) * 100 : 0}%` }"></span>
            <span class="crew-meter-soldiers" :style="{ width: `${crewCapacity ? (Number(form.soldiers) / crewCapacity) * 100 : 0}%` }"></span>
            <span class="crew-meter-mercenaries" :style="{ width: `${crewCapacity ? (Number(form.mercenaries) / crewCapacity) * 100 : 0}%` }"></span>
          </div>
          <div class="crew-allocation-legend">
            <span>{{ t('builds.create.crew.sailorMinimum', { value: sailorMinimum }) }}</span>
            <span>{{ t('builds.crewConsole.dynamicLimit') }}</span>
            <span>{{ t('builds.create.crew.workingSpeed', { value: sailingEfficiency }) }}</span>
            <span v-if="sailorsBelowMinimum" class="crew-warning">{{ t('builds.create.crew.tooFewSailors', { current: form.sailors, minimum: sailorMinimum }) }}</span>
            <span v-if="crewOverLimit" class="crew-warning">{{ t('builds.create.crew.tooManyCrew') }}</span>
          </div>

          <div class="crew-grid section-fields">
            <label class="crew-slider-card crew-sailors">
              <img class="crew-role-image" :src="buildCrewVisuals.sailors" alt="" />
              <span><small>{{ t('builds.create.crew.sailors') }}</small><strong>{{ form.sailors }}</strong></span>
              <input :value="form.sailors" type="range" min="0" :max="crewMaxFor('sailors')" @input="onCrewSliderInput('sailors', $event)" />
              <small>0–{{ crewMaxFor('sailors') }}</small>
            </label>

            <label class="crew-slider-card crew-musketeers">
              <img class="crew-role-image" :src="buildCrewVisuals.musketeers" alt="" />
              <span><small>{{ t('builds.create.crew.musketeers') }}</small><strong>{{ form.musketeers }}</strong></span>
              <input :value="form.musketeers" type="range" min="0" :max="crewMaxFor('musketeers')" @input="onCrewSliderInput('musketeers', $event)" />
              <small>0–{{ crewMaxFor('musketeers') }}</small>
            </label>

            <label class="crew-slider-card crew-soldiers">
              <img class="crew-role-image" :src="buildCrewVisuals.soldiers" alt="" />
              <span><small>{{ t('builds.create.crew.soldiers') }}</small><strong>{{ form.soldiers }}</strong></span>
              <input :value="form.soldiers" type="range" min="0" :max="crewMaxFor('soldiers')" @input="onCrewSliderInput('soldiers', $event)" />
              <small>0–{{ crewMaxFor('soldiers') }}</small>
            </label>

            <label class="crew-slider-card crew-mercenaries">
              <img class="crew-role-image" :src="buildCrewVisuals.mercenaries" alt="" />
              <span><small>{{ t('builds.create.crew.mercenaries') }}</small><strong>{{ form.mercenaries }}</strong></span>
              <input :value="form.mercenaries" type="range" min="0" :max="crewMaxFor('mercenaries')" @input="onCrewSliderInput('mercenaries', $event)" />
              <small>0–{{ crewMaxFor('mercenaries') }}</small>
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section inventory-section compact-inventory-panel" :aria-label="t('builds.create.sections.inventory')">
        <div class="section-title">
          <span>06</span>
          <h2>{{ t('builds.create.sections.inventory') }}</h2>
        </div>
        <div class="inventory-grid three-columns">
          <div class="inventory-panel ammunition-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.ammunition') }}</strong>
              <span>{{ t('builds.create.inventory.slotCount', { count: slotCount('ammunition_slots') }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.ammunitionHint') }}</p>
            <label v-for="(slot, index) in form.ammunition_slots" :key="`ammo-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="inventoryImage('ammunition_slots', slot.item)" :alt="t('builds.create.inventory.ammunitionAlt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('ammunition_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('ammunition')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.ammunition_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('ammunition_slots', index, $event)"
              />
            </label>
          </div>

          <div class="inventory-panel consumable-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.consumables') }}</strong>
              <span>{{ t('builds.create.inventory.limitedSlotCount', { count: slotCount('consumable_slots'), max: 3 }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.consumablesHint') }}</p>
            <label v-for="(slot, index) in form.consumable_slots" :key="`consumable-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="inventoryImage('consumable_slots', slot.item)" :alt="t('builds.create.inventory.consumableAlt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('consumable_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('consumable')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.consumable_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('consumable_slots', index, $event)"
              />
            </label>
          </div>

          <div class="inventory-panel hold-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.hold') }}</strong>
              <span>{{ t('builds.create.inventory.slotCount', { count: slotCount('hold_slots') }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.holdHint') }}</p>
            <label v-for="(slot, index) in form.hold_slots" :key="`hold-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="inventoryImage('hold_slots', slot.item)" :alt="t('builds.create.inventory.holdAlt', { index: index + 1 })" />
              </span>
              <select :value="slot.item" @change="onInventoryItemChange('hold_slots', index, $event)">
                <option value="">{{ t('common.empty') }}</option>
                <option
                  v-for="option in optionsFor('hold')"
                  :key="option"
                  :value="option"
                  :disabled="isOptionUsed(form.hold_slots, option, index)"
                >
                  {{ optionLabel(option) }}
                </option>
              </select>
              <input
                :value="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventoryQuantityChange('hold_slots', index, $event)"
              />
            </label>
          </div>
        </div>
      </section>

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
