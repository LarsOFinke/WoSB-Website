<script setup>
import { computed } from 'vue'

import FileUploadPanel from '@/core/components/FileUploadPanel.vue'
import MetricCard from '@/core/components/MetricCard.vue'
import StatEffectEditor from '@/modules/admin/components/StatEffectEditor.vue'
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { useMasterDataWorkspace } from '@/modules/admin/composables/useMasterDataWorkspace'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'
import { useSession } from '@/modules/accounts/session'
import { IMAGE_MIME_TYPES } from '@/modules/files/fileTypes'

const {
  t, activeTab, loading, saving, error, success, overview, taxonomy, categories, options,
  upgradeOptions, ships, optionCategory, optionSearch, shipSearch, categoryEditingId,
  optionEditingId, shipEditingId, effectRows, categoryForm, optionForm, shipForm,
  selectedCategory, selectedOption, selectedShip, tabCounts, seedStatusClass, mountLabel, visibleMounts,
  seedStatusLabel, imagePreview, applyUploadedImage, resetCategory, resetOption, resetShip,
  saveCategory, saveOption, upgradeOptionById, upgradeChoicesForOverride, addUpgradeOverride,
  removeUpgradeOverride, statEffectRows, replaceOverrideEffects, saveShip, deactivateCategory, deactivateOption, deactivateShip,
  restoreCategory, restoreOption, restoreShip, restoreAllSeedDefaults,
} = useMasterDataWorkspace()
const { isAdmin, user } = useSession()
const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))

function setMortarModificationEnabled(enabled) {
  shipForm.mortar_modification = enabled
    ? (shipForm.mortar_modification || {
        mortar_capacity: 1,
        max_caliber_inches: 7,
        broadside_capacity_delta: 0,
        durability_delta: 0,
        speed_pct: 0,
        maneuverability_delta: 0,
        hold_capacity_pct: 0,
        crew_capacity_delta: 0,
        source: '',
      })
    : null
}
</script>
<template>
  <StaffWorkspaceShell
    :eyebrow="t('masterData.eyebrow')"
    :title="t('masterData.title')"
    :description="t('masterData.subtitle')"
    title-id="master-data-title"
    :groups="navigationGroups"
    active-key="master-data"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :is-admin="isAdmin"
  >
    <template #actions><RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink></template>
    <div class="master-data-frame staff-subworkspace">

      <section class="master-data-metrics" aria-label="Master data summary">
        <MetricCard :label="t('masterData.metrics.categories')" :value="overview.category_count" />
        <MetricCard :label="t('masterData.metrics.options')" :value="overview.option_count" />
        <MetricCard :label="t('masterData.metrics.ships')" :value="overview.ship_count" />
        <MetricCard :label="t('masterData.metrics.overrides')" :value="overview.overridden_count" tone="warning" />
        <MetricCard :label="t('masterData.metrics.inactive')" :value="overview.inactive_count" />
      </section>

      <section class="master-data-reset-panel" aria-labelledby="master-data-reset-title">
        <div>
          <span class="panel-kicker">{{ t('masterData.restoreAllKicker') }}</span>
          <h2 id="master-data-reset-title">{{ t('masterData.restoreAllTitle') }}</h2>
          <p>{{ t('masterData.restoreAllHint') }}</p>
        </div>
        <button
          class="form-button danger-action master-data-reset-button"
          type="button"
          :disabled="loading || saving"
          @click="restoreAllSeedDefaults"
        >
          {{ t('masterData.restoreAllButton') }}
        </button>
      </section>

      <nav class="master-data-tabs" aria-label="Master data catalogs">
        <button
          v-for="tab in ['ships', 'options', 'categories']"
          :key="tab"
          type="button"
          class="catalog-tab"
          :class="{ 'is-active': activeTab === tab }"
          :aria-pressed="activeTab === tab"
          @click="activeTab = tab"
        >
          <span>{{ t(`masterData.tabs.${tab}`) }}</span>
          <strong>{{ tabCounts[tab] }}</strong>
        </button>
      </nav>

      <div v-if="loading || error || success" class="master-data-notices" aria-live="polite">
        <p v-if="loading" class="notice-card muted">{{ t('masterData.loading') }}</p>
        <p v-if="error" class="notice-card error-text">{{ error }}</p>
        <p v-if="success" class="notice-card success-text">{{ success }}</p>
      </div>

      <section v-if="activeTab === 'categories'" class="master-data-workspace">
        <aside class="catalog-panel">
          <header class="catalog-panel-header">
            <div>
              <span class="panel-kicker">{{ categories.length }}</span>
              <h2>{{ t('masterData.categories.title') }}</h2>
            </div>
            <button class="small-action" type="button" @click="resetCategory()">{{ t('masterData.new') }}</button>
          </header>
          <div class="catalog-scroll">
            <article
              v-for="row in categories"
              :key="row.id"
              class="catalog-record"
              :class="[seedStatusClass(row), { 'is-selected': categoryEditingId === row.id, 'is-inactive': !row.is_active }]"
            >
              <button class="catalog-record-main" type="button" @click="resetCategory(row)">
                <span class="record-icon">#</span>
                <span class="record-copy"><strong>{{ row.label }}</strong><small>{{ row.key }}</small></span>
              </button>
              <div class="record-meta">
                <span class="status-chip">{{ seedStatusLabel(row) }}</span>
                <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreCategory(row)">{{ t('masterData.restore') }}</button>
                <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateCategory(row)">{{ t('masterData.deactivate') }}</button>
              </div>
            </article>
          </div>
        </aside>

        <form class="editor-panel" @submit.prevent="saveCategory">
          <header class="editor-header">
            <div><span class="panel-kicker">{{ categoryEditingId ? seedStatusLabel(selectedCategory) : t('masterData.customRecord') }}</span><h2>{{ categoryEditingId ? t('masterData.categories.edit') : t('masterData.categories.create') }}</h2></div>
            <button v-if="selectedCategory?.seed_status === 'overridden'" class="small-action" type="button" :disabled="saving" @click="restoreCategory(selectedCategory)">{{ t('masterData.restore') }}</button>
          </header>
          <div class="editor-section form-grid two-columns">
            <label><span>{{ t('masterData.fields.key') }}</span><input v-model="categoryForm.key" required maxlength="40" :disabled="Boolean(categoryEditingId)" /></label>
            <label><span>{{ t('masterData.fields.label') }}</span><input v-model="categoryForm.label" required maxlength="80" /></label>
            <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="categoryForm.sort_order" type="number" min="0" /></label>
            <label class="toggle-field"><input v-model="categoryForm.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label>
          </div>
          <footer class="editor-actions"><button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button></footer>
        </form>
      </section>

      <section v-if="activeTab === 'options'" class="master-data-workspace">
        <aside class="catalog-panel">
          <header class="catalog-panel-header">
            <div><span class="panel-kicker">{{ options.length }}</span><h2>{{ t('masterData.options.title') }}</h2></div>
            <button class="small-action" type="button" @click="resetOption()">{{ t('masterData.new') }}</button>
          </header>
          <div class="catalog-toolbar">
            <select v-model="optionCategory"><option value="">{{ t('masterData.allCategories') }}</option><option v-for="row in categories" :key="row.id" :value="row.key">{{ row.label }}</option></select>
            <input v-model="optionSearch" type="search" :placeholder="t('common.search')" />
          </div>
          <div class="catalog-scroll">
            <article
              v-for="row in options"
              :key="row.id"
              class="catalog-record"
              :class="[seedStatusClass(row), { 'is-selected': optionEditingId === row.id, 'is-inactive': !row.is_active }]"
            >
              <button class="catalog-record-main" type="button" @click="resetOption(row)">
                <span class="record-image"><img v-if="row.image_url" :src="imagePreview(row.image_url)" alt="" /><span v-else>✦</span></span>
                <span class="record-copy"><strong>{{ row.name }}</strong><small>{{ row.category_label }} · {{ row.option_kind || '—' }}</small></span>
              </button>
              <div class="record-meta">
                <span class="status-chip">{{ seedStatusLabel(row) }}</span>
                <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreOption(row)">{{ t('masterData.restore') }}</button>
                <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateOption(row)">{{ t('masterData.deactivate') }}</button>
              </div>
            </article>
          </div>
        </aside>

        <form class="editor-panel" @submit.prevent="saveOption">
          <header class="editor-header editor-header-with-preview">
            <div class="editor-preview"><img v-if="optionForm.image_url" :src="imagePreview(optionForm.image_url)" alt="" /><span v-else>✦</span></div>
            <div><span class="panel-kicker">{{ selectedOption ? seedStatusLabel(selectedOption) : t('masterData.customRecord') }}</span><h2>{{ optionEditingId ? t('masterData.options.edit') : t('masterData.options.create') }}</h2><p>{{ optionForm.name || '—' }}</p></div>
          </header>
          <div v-if="selectedOption" class="seed-note">
            <div><strong>{{ seedStatusLabel(selectedOption) }}</strong><span>{{ selectedOption.seed_status === 'custom' ? t('masterData.customRecord') : selectedOption.seed_revision }}</span></div>
            <button v-if="selectedOption.seed_status === 'overridden'" class="small-action" type="button" :disabled="saving" @click="restoreOption(selectedOption)">{{ t('masterData.restore') }}</button>
          </div>

          <fieldset class="editor-section"><legend>{{ t('masterData.options.title') }}</legend>
            <div class="form-grid two-columns">
              <label><span>{{ t('masterData.fields.category') }}</span><select v-model="optionForm.category_id" required><option v-for="row in categories" :key="row.id" :value="row.id">{{ row.label }}</option></select></label>
              <label><span>{{ t('masterData.fields.name') }}</span><input v-model="optionForm.name" required maxlength="160" /></label>
              <label><span>{{ t('masterData.fields.kind') }}</span><input v-model="optionForm.option_kind" maxlength="40" /></label>
              <label><span>{{ t('masterData.fields.sortOrder') }}</span><input v-model.number="optionForm.sort_order" type="number" min="0" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.weaponMounts') }}</legend>
            <div class="form-grid two-columns">
              <label><span>{{ t('masterData.fields.weaponClass') }}</span><select v-model="optionForm.weapon_class" :disabled="!['cannon', 'bow_stern'].includes(optionForm.option_kind)"><option value="">—</option><option v-for="row in taxonomy.weapon_classes" :key="row.code" :value="row.code">{{ row.label }}</option></select></label>
              <label><span>{{ t('masterData.fields.caliber') }}</span><input v-model="optionForm.weapon_caliber_inches" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.weaponDamage') }}</span><input v-model="optionForm.weapon_base_damage" type="number" min="0" step="0.1" :disabled="!['cannon', 'bow_stern'].includes(optionForm.option_kind)" /></label>
              <label><span>{{ t('masterData.fields.weaponReload') }}</span><input v-model="optionForm.weapon_reload_seconds" type="number" min="0.1" step="0.1" :disabled="!['cannon', 'bow_stern'].includes(optionForm.option_kind)" /></label>
            </div>
            <div class="choice-grid"><label v-for="row in taxonomy.weapon_slot_types" :key="row.code" class="choice-card"><input v-model="optionForm.allowed_slot_types" type="checkbox" :value="row.code" /><span>{{ row.label }}</span></label></div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.effects') }}</legend>
            <p class="section-description">{{ t('masterData.effectsHint') }}</p>
            <StatEffectEditor v-model="effectRows" :definitions="taxonomy.stat_effects" />
          </fieldset>

          <fieldset class="editor-section upgrade-override-section"><legend>{{ t('masterData.shipUpgradeOverrides.title') }}</legend>
            <p class="section-description">{{ t('masterData.shipUpgradeOverrides.hint') }}</p>
            <div v-if="shipForm.upgrade_effect_overrides.length" class="upgrade-override-list">
              <article v-for="(override, index) in shipForm.upgrade_effect_overrides" :key="`upgrade-override-${index}`" class="upgrade-override-card">
                <div class="override-card-header">
                  <label><span>{{ t('masterData.shipUpgradeOverrides.upgrade') }}</span><select v-model.number="override.option_id"><option v-for="row in upgradeChoicesForOverride(index)" :key="row.id" :value="row.id">{{ row.name }}</option></select></label>
                  <button class="danger-action" type="button" @click="removeUpgradeOverride(index)">{{ t('masterData.shipUpgradeOverrides.remove') }}</button>
                </div>
                <div class="override-effect-grid">
                  <div><span>{{ t('masterData.shipUpgradeOverrides.defaultEffects') }}</span><StatEffectEditor :model-value="statEffectRows(upgradeOptionById(override.option_id)?.stat_effects)" :definitions="taxonomy.stat_effects" readonly /></div>
                  <div><span>{{ t('masterData.shipUpgradeOverrides.overrideEffects') }}</span><StatEffectEditor :model-value="statEffectRows(override.stat_effects)" :definitions="taxonomy.stat_effects" @update:model-value="replaceOverrideEffects(override, $event)" /></div>
                </div>
              </article>
            </div>
            <p v-else class="empty-state-inline">{{ t('masterData.shipUpgradeOverrides.empty') }}</p>
            <button class="small-action add-override-button" type="button" :disabled="shipForm.upgrade_effect_overrides.length >= upgradeOptions.length" @click="addUpgradeOverride">{{ t('masterData.shipUpgradeOverrides.add') }}</button>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.source') }}</legend>
            <div class="form-grid">
              <label><span>{{ t('masterData.fields.source') }}</span><input v-model="optionForm.source" maxlength="240" /></label>
              <label><span>{{ t('masterData.fields.notes') }}</span><textarea v-model="optionForm.notes" rows="3" maxlength="500"></textarea></label>
              <label><span>{{ t('masterData.fields.imageUrl') }}</span><input v-model="optionForm.image_url" type="text" inputmode="url" maxlength="500" /></label>
            </div>
            <FileUploadPanel usage-context="master-data" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="applyUploadedImage(optionForm, $event)" />
          </fieldset>

          <footer class="editor-actions"><label class="toggle-field"><input v-model="optionForm.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label><button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button></footer>
        </form>
      </section>

      <section v-if="activeTab === 'ships'" class="master-data-workspace">
        <aside class="catalog-panel ship-catalog-panel">
          <header class="catalog-panel-header">
            <div><span class="panel-kicker">{{ ships.length }}</span><h2>{{ t('masterData.ships.title') }}</h2></div>
            <button class="small-action" type="button" @click="resetShip()">{{ t('masterData.new') }}</button>
          </header>
          <div class="catalog-toolbar single"><input v-model="shipSearch" type="search" :placeholder="t('common.search')" /></div>
          <div class="catalog-scroll">
            <article
              v-for="row in ships"
              :key="row.id"
              class="catalog-record ship-record"
              :class="[seedStatusClass(row), { 'is-selected': shipEditingId === row.id, 'is-inactive': !row.is_active }]"
            >
              <button class="catalog-record-main" type="button" @click="resetShip(row)">
                <span class="record-image ship-record-image"><img v-if="row.image_url" :src="imagePreview(row.image_url)" alt="" /><span v-else>⚓</span></span>
                <span class="record-copy"><strong>{{ row.name }}</strong><small>{{ t('common.rate') }} {{ row.rate }} · {{ row.ship_type }}</small><small class="weapon-layout">{{ row.weapon_layout }}</small></span>
              </button>
              <div class="record-meta">
                <span class="status-chip">{{ seedStatusLabel(row) }}</span>
                <button v-if="row.seed_status === 'overridden'" class="small-action" type="button" @click="restoreShip(row)">{{ t('masterData.restore') }}</button>
                <button v-if="row.is_active" class="danger-action" type="button" @click="deactivateShip(row)">{{ t('masterData.deactivate') }}</button>
              </div>
            </article>
          </div>
        </aside>

        <form class="editor-panel ship-editor" @submit.prevent="saveShip">
          <header class="editor-header editor-header-with-preview ship-editor-header">
            <div class="editor-preview ship-editor-preview"><img v-if="shipForm.image_url" :src="imagePreview(shipForm.image_url)" alt="" /><span v-else>⚓</span></div>
            <div><span class="panel-kicker">{{ selectedShip ? seedStatusLabel(selectedShip) : t('masterData.customRecord') }}</span><h2>{{ shipForm.name || (shipEditingId ? t('masterData.ships.edit') : t('masterData.ships.create')) }}</h2><p>{{ t('common.rate') }} {{ shipForm.rate }} · {{ shipForm.ship_type || '—' }}</p></div>
            <div class="ship-quick-stats"><span><small>{{ t('masterData.fields.durability') }}</small><strong>{{ shipForm.durability }}</strong></span><span><small>{{ t('masterData.fields.cruiseMaxSpeed') }}</small><strong>{{ shipForm.speed_knots }}</strong></span><span><small>{{ t('masterData.fields.crewCapacity') }}</small><strong>{{ shipForm.crew_capacity }}</strong></span></div>
          </header>
          <div v-if="selectedShip" class="seed-note">
            <div><strong>{{ seedStatusLabel(selectedShip) }}</strong><span>{{ selectedShip.seed_status === 'custom' ? t('masterData.customRecord') : selectedShip.seed_revision }}</span></div>
            <button v-if="selectedShip.seed_status === 'overridden'" class="small-action" type="button" :disabled="saving" @click="restoreShip(selectedShip)">{{ t('masterData.restore') }}</button>
          </div>

          <fieldset class="editor-section"><legend>{{ t('masterData.ships.title') }}</legend>
            <div class="form-grid two-columns">
              <label><span>{{ t('masterData.fields.name') }}</span><input v-model="shipForm.name" required maxlength="120" /></label>
              <label><span>{{ t('masterData.fields.type') }}</span><input v-model="shipForm.ship_type" required maxlength="80" /></label>
            </div>
            <div class="form-grid three-columns compact-fields">
              <label><span>{{ t('common.rate') }}</span><input v-model.number="shipForm.rate" type="number" min="1" max="7" /></label>
              <label><span>{{ t('masterData.fields.sailSlots') }}</span><input v-model.number="shipForm.sail_slots" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.upgradeSlots') }}</span><input v-model.number="shipForm.upgrade_slots" type="number" min="0" max="8" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.durability') }}</legend>
            <div class="form-grid three-columns">
              <label><span>{{ t('masterData.fields.durability') }}</span><input v-model.number="shipForm.durability" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.baseSpeed') }}</span><input v-model.number="shipForm.speed_min_knots" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.cruiseMaxSpeed') }}</span><input v-model.number="shipForm.speed_knots" type="number" :min="shipForm.speed_min_knots" step="0.01" /></label>
              <label><span>{{ t('masterData.fields.maneuverability') }}</span><input v-model.number="shipForm.maneuverability" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.armor') }}</span><input v-model.number="shipForm.armor" type="number" min="0" step="0.1" /></label>
              <label><span>{{ t('masterData.fields.holdCapacity') }}</span><input v-model.number="shipForm.hold_capacity" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.displacement') }}</span><input v-model.number="shipForm.displacement_tons" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.crewCapacity') }}</span><input v-model.number="shipForm.crew_capacity" type="number" min="0" /></label>
              <label><span>{{ t('masterData.fields.sailorMinimum') }}</span><input v-model.number="shipForm.sailor_minimum" type="number" min="0" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section mount-section"><legend>{{ t('masterData.fields.weaponMounts') }}</legend>
            <div v-if="visibleMounts(shipForm.weapon_mounts).length" class="mount-summary">
              <span v-for="mount in visibleMounts(shipForm.weapon_mounts)" :key="`summary-${mount.slot_type}`"><small>{{ mountLabel(mount.slot_type) }}</small><strong>{{ mount.capacity }}</strong></span>
            </div>
            <div class="mount-grid">
              <div v-for="mount in shipForm.weapon_mounts" :key="mount.slot_type" class="mount-card" :class="{ 'has-capacity': Number(mount.capacity || 0) > 0 }">
                <strong>{{ mountLabel(mount.slot_type) }}</strong>
                <label><span>{{ t('masterData.fields.capacity') }}</span><input v-model.number="mount.capacity" type="number" min="0" /></label>
                <label v-if="['weapon_front', 'weapon_rear', 'weapon_special'].includes(mount.slot_type)"><span>{{ t('masterData.fields.specialWeaponCapacity') }}</span><input v-model.number="mount.special_weapon_capacity" type="number" min="0" :max="mount.capacity" /></label>
                <label><span>{{ t('masterData.fields.weaponClass') }}</span><select v-model="mount.max_weapon_class"><option value="">—</option><option v-for="row in taxonomy.weapon_classes" :key="row.code" :value="row.code">{{ row.label }}</option></select></label>
                <label><span>{{ t('masterData.fields.caliber') }}</span><input v-model="mount.max_caliber_inches" type="number" min="0" step="0.1" /></label>
              </div>
            </div>
          </fieldset>

          <fieldset class="editor-section">
            <legend>{{ t('masterData.mortarModification.title') }}</legend>
            <label class="toggle-field">
              <input
                :checked="Boolean(shipForm.mortar_modification)"
                type="checkbox"
                @change="setMortarModificationEnabled($event.target.checked)"
              />
              <span>{{ t('masterData.mortarModification.available') }}</span>
            </label>
            <p class="section-description">{{ t('masterData.mortarModification.hint') }}</p>
            <div v-if="shipForm.mortar_modification" class="form-grid three-columns">
              <label><span>{{ t('masterData.mortarModification.mortarCapacity') }}</span><input v-model.number="shipForm.mortar_modification.mortar_capacity" type="number" min="1" max="8" /></label>
              <label><span>{{ t('masterData.fields.caliber') }}</span><input v-model.number="shipForm.mortar_modification.max_caliber_inches" type="number" min="0.1" max="20" step="0.1" /></label>
              <label><span>{{ t('masterData.mortarModification.broadsideDelta') }}</span><input v-model.number="shipForm.mortar_modification.broadside_capacity_delta" type="number" max="0" /></label>
              <label><span>{{ t('masterData.mortarModification.durabilityDelta') }}</span><input v-model.number="shipForm.mortar_modification.durability_delta" type="number" max="0" /></label>
              <label><span>{{ t('masterData.mortarModification.speedPercent') }}</span><input v-model.number="shipForm.mortar_modification.speed_pct" type="number" step="0.1" /></label>
              <label><span>{{ t('masterData.mortarModification.maneuverabilityDelta') }}</span><input v-model.number="shipForm.mortar_modification.maneuverability_delta" type="number" step="0.1" /></label>
              <label><span>{{ t('masterData.mortarModification.holdPercent') }}</span><input v-model.number="shipForm.mortar_modification.hold_capacity_pct" type="number" step="0.1" /></label>
              <label><span>{{ t('masterData.mortarModification.crewDelta') }}</span><input v-model.number="shipForm.mortar_modification.crew_capacity_delta" type="number" max="0" /></label>
              <label><span>{{ t('masterData.fields.source') }}</span><input v-model="shipForm.mortar_modification.source" required maxlength="500" /></label>
            </div>
          </fieldset>

          <fieldset class="editor-section"><legend>{{ t('masterData.fields.source') }}</legend>
            <div class="form-grid">
              <label><span>{{ t('masterData.fields.source') }}</span><input v-model="shipForm.source" maxlength="240" /></label>
              <label><span>{{ t('masterData.fields.imageUrl') }}</span><input v-model="shipForm.image_url" type="text" inputmode="url" maxlength="500" /></label>
            </div>
            <FileUploadPanel usage-context="master-data" :accepted-types="IMAGE_MIME_TYPES" :multiple="false" @uploaded="applyUploadedImage(shipForm, $event)" />
          </fieldset>

          <footer class="editor-actions">
            <div class="editor-toggles"><label class="toggle-field"><input v-model="shipForm.has_lantern" type="checkbox" /><span>{{ t('masterData.fields.lantern') }}</span></label><label class="toggle-field"><input v-model="shipForm.is_active" type="checkbox" /><span>{{ t('masterData.fields.active') }}</span></label></div>
            <button class="form-button primary-action" type="submit" :disabled="saving">{{ t('common.save') }}</button>
          </footer>
        </form>
      </section>
    </div>
  </StaffWorkspaceShell>
</template>

<style scoped src="../styles/masterDataWorkspace.css"></style>
