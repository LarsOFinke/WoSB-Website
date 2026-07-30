<script setup>
import BuildOptionPicker from '@/modules/builds/components/BuildOptionPicker.vue'
import CombatDpmResultCard from '@/modules/combat/components/CombatDpmResultCard.vue'
import { useCombatAnalysisPage } from '@/modules/combat/composables/useCombatAnalyzer'
import '@/modules/builds/styles/buildOptionPicker.css'
import '@/modules/combat/styles/combatAnalysis.css'

const {
  t, optionLabel, form, loading, error, selectedShip, shipPickerOptions, selectedShipImage,
  availableUpgradeSlots, upgradePickerOptions, specialistPickerOptions, lanternPickerOptions,
  standardWeaponOptionsForField, weaponCapacityForField, slotQuantityTotal, quantityMaxForField,
  onInventoryItemChange, onInventoryQuantityChange, results,
} = useCombatAnalysisPage()

const weaponSections = [
  { field: 'port_weapon_slots', titleKey: 'combatAnalysis.weapons.oneSide', hintKey: 'combatAnalysis.weapons.oneSideHint' },
  { field: 'front_weapon_slots', titleKey: 'combatAnalysis.weapons.bow', hintKey: 'combatAnalysis.weapons.bowHint' },
  { field: 'rear_weapon_slots', titleKey: 'combatAnalysis.weapons.stern', hintKey: 'combatAnalysis.weapons.sternHint' },
]
</script>

<template>
  <section class="combat-analysis-page page-frame" aria-labelledby="combat-analysis-title">
    <header class="combat-analysis-hero wire-frame">
      <div>
        <p class="eyebrow">{{ t('combatAnalysis.eyebrow') }}</p>
        <h1 id="combat-analysis-title">{{ t('combatAnalysis.title') }}</h1>
        <p>{{ t('combatAnalysis.subtitle') }}</p>
      </div>
      <div class="combat-formula-note">
        <strong>{{ t('combatAnalysis.formulaTitle') }}</strong>
        <span>{{ t('combatAnalysis.formula') }}</span>
      </div>
    </header>

    <p v-if="error" class="form-error" role="alert">{{ error }}</p>

    <div class="combat-analysis-layout">
      <div class="combat-analysis-config">
        <section class="wire-section combat-section">
          <div class="section-title"><span>01</span><h2>{{ t('combatAnalysis.ship.title') }}</h2></div>
          <div class="combat-ship-picker-row">
            <BuildOptionPicker
              v-model="form.ship_id"
              :options="shipPickerOptions"
              :placeholder="t('builds.create.selectShip')"
              :aria-label="t('combatAnalysis.ship.select')"
              :disabled="loading"
              :allow-empty="false"
              searchable
              required
              :search-placeholder="t('builds.create.shipSearch.searchPlaceholder')"
              :no-results-text="t('builds.create.shipSearch.noMatches')"
            />
            <article v-if="selectedShip" class="combat-ship-summary">
              <img :src="selectedShipImage" alt="" />
              <div><strong>{{ selectedShip.name }}</strong><span>{{ selectedShip.ship_type }} · {{ t('common.rate') }} {{ selectedShip.rate }}</span></div>
              <div class="combat-ship-capacities">
                <span>{{ t('combatAnalysis.weapons.broadsideShort') }} {{ selectedShip.broadside_weapon_capacity }}</span>
                <span>{{ t('combatAnalysis.weapons.bowShort') }} {{ selectedShip.front_weapon_capacity }}</span>
                <span>{{ t('combatAnalysis.weapons.sternShort') }} {{ selectedShip.rear_weapon_capacity }}</span>
              </div>
            </article>
          </div>
        </section>

        <section class="wire-section combat-section">
          <div class="section-title"><span>02</span><h2>{{ t('combatAnalysis.weapons.title') }}</h2></div>
          <p class="section-helper-text">{{ t('combatAnalysis.weapons.hint') }}</p>
          <div class="combat-weapon-grid">
            <article v-for="section in weaponSections" :key="section.field" class="combat-weapon-panel">
              <header>
                <div><strong>{{ t(section.titleKey) }}</strong><p>{{ t(section.hintKey) }}</p></div>
                <span>{{ slotQuantityTotal(section.field) }}/{{ weaponCapacityForField(section.field) }}</span>
              </header>
              <p v-if="weaponCapacityForField(section.field) === 0" class="combat-empty-state">{{ t('builds.create.weapons.unavailable') }}</p>
              <label v-for="(slot, index) in form[section.field]" :key="`${section.field}-${index}`" class="combat-weapon-row">
                <select :value="slot.item" @change="onInventoryItemChange(section.field, index, $event)">
                  <option value="">{{ t('common.empty') }}</option>
                  <option v-for="name in standardWeaponOptionsForField(section.field, index)" :key="name" :value="name">{{ optionLabel(name) }}</option>
                </select>
                <input
                  :value="slot.quantity"
                  type="number"
                  min="1"
                  :max="quantityMaxForField(section.field, index)"
                  :aria-label="t('common.quantity')"
                  @input="onInventoryQuantityChange(section.field, index, $event)"
                />
              </label>
            </article>
          </div>
        </section>

        <section class="wire-section combat-section">
          <div class="section-title"><span>03</span><h2>{{ t('combatAnalysis.modifiers.title') }}</h2></div>
          <p class="section-helper-text">{{ t('combatAnalysis.modifiers.hint') }}</p>
          <div class="combat-modifier-grid">
            <label class="combat-picker-field">
              <span>{{ t('combatAnalysis.modifiers.lantern') }}</span>
              <BuildOptionPicker v-model="form.lantern" :options="lanternPickerOptions" :placeholder="t('common.empty')" :aria-label="t('combatAnalysis.modifiers.lantern')" />
            </label>

            <label v-for="index in availableUpgradeSlots" :key="`combat-upgrade-${index}`" class="combat-picker-field">
              <span>{{ t('combatAnalysis.modifiers.upgrade', { index }) }}</span>
              <BuildOptionPicker v-model="form.upgrades[index - 1]" :options="upgradePickerOptions(index - 1)" :placeholder="t('common.empty')" :aria-label="t('combatAnalysis.modifiers.upgrade', { index })" />
            </label>

            <label v-for="(_, index) in form.specialists" :key="`combat-specialist-${index}`" class="combat-picker-field">
              <span>{{ t('combatAnalysis.modifiers.specialist', { index: index + 1 }) }}</span>
              <BuildOptionPicker
                v-model="form.specialists[index]"
                :options="specialistPickerOptions(index)"
                :placeholder="t('common.empty')"
                :aria-label="t('combatAnalysis.modifiers.specialist', { index: index + 1 })"
                searchable
                :search-placeholder="t('builds.create.specialists.searchPlaceholder')"
                :no-results-text="t('builds.create.specialists.noMatches')"
              />
            </label>
          </div>
          <div class="combat-condition-row">
            <label><span>{{ t('combatAnalysis.modifiers.sailors') }}</span><input v-model.number="form.sailors" type="number" min="0" :max="selectedShip?.crew_capacity || 999" /></label>
            <label class="toggle-field"><input v-model="form.low_durability" type="checkbox" /><span>{{ t('combatAnalysis.modifiers.lowDurability') }}</span></label>
          </div>
          <p class="combat-scope-note">{{ t('combatAnalysis.modifiers.scopeNote') }}</p>
        </section>
      </div>

      <section class="wire-section combat-results-section" aria-live="polite">
        <div class="section-title"><span>04</span><h2>{{ t('combatAnalysis.results.title') }}</h2></div>
        <p class="section-helper-text">{{ t('combatAnalysis.results.hint') }}</p>
        <div class="combat-results-grid">
          <CombatDpmResultCard
            :title="t('combatAnalysis.results.oneSide')"
            :description="t('combatAnalysis.results.oneSideHint')"
            :result="results.oneSide"
            :armor="form.armor.oneSide"
            @update:armor="form.armor.oneSide = $event"
          />
          <CombatDpmResultCard
            :title="t('combatAnalysis.results.bothSides')"
            :description="t('combatAnalysis.results.bothSidesHint')"
            :result="results.bothSides"
            :armor="form.armor.bothSides"
            @update:armor="form.armor.bothSides = $event"
          />
          <CombatDpmResultCard
            :title="t('combatAnalysis.results.bow')"
            :description="t('combatAnalysis.results.bowHint')"
            :result="results.bow"
            :armor="form.armor.bow"
            @update:armor="form.armor.bow = $event"
          />
          <CombatDpmResultCard
            :title="t('combatAnalysis.results.stern')"
            :description="t('combatAnalysis.results.sternHint')"
            :result="results.stern"
            :armor="form.armor.stern"
            @update:armor="form.armor.stern = $event"
          />
        </div>
        <p class="combat-source-note">{{ t('combatAnalysis.results.sourceNote') }}</p>
      </section>
    </div>
  </section>
</template>
