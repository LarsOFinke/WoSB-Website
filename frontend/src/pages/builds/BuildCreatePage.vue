<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import { createBuild, getBuildOptions } from '@/services/builds'
import { listShips } from '@/services/ships'

const router = useRouter()
const { optionLabel, t } = useLocale()

const ships = ref([])
const optionCatalog = ref({ categories: [], options: {} })
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const slotPlaceholderSrc = '/icons/slot-placeholder.svg'
const equipmentUpgradeCount = 5

const buildTypeOptions = computed(() => [
  { value: 'balanced', label: t('builds.types.balanced') },
  { value: 'gunnery', label: t('builds.types.gunnery') },
  { value: 'boarding', label: t('builds.types.boarding') },
  { value: 'defensive', label: t('builds.types.defensive') },
])

const inventoryLimits = {
  ammunition_slots: 12,
  consumable_slots: 3,
  hold_slots: 24,
}

function optionsFor(categoryKey) {
  return (optionCatalog.value.options?.[categoryKey] || [])
    .map((option) => option.name)
    .sort((left, right) => optionLabel(left).localeCompare(optionLabel(right), undefined, { sensitivity: 'base' }))
}

function sortShipsForDropdown(shipRows) {
  return [...shipRows].sort((left, right) => {
    const rateDiff = Number(right.rate || 0) - Number(left.rate || 0)
    if (rateDiff !== 0) return rateDiff
    return String(left.name || '').localeCompare(String(right.name || ''), undefined, { sensitivity: 'base' })
  })
}

function emptySlot() {
  return { item: '', quantity: 1 }
}

const form = reactive({
  build_name: '',
  build_type: 'balanced',
  ship_id: '',
  sails: '',
  upgrade_1: '',
  upgrade_2: '',
  upgrade_3: '',
  upgrade_4: '',
  upgrade_5: '',
  lantern: '',
  sailors: 0,
  soldiers: 0,
  musketeers: 0,
  mercenaries: 0,
  ammunition_slots: [emptySlot()],
  consumable_slots: [emptySlot()],
  hold_slots: [emptySlot()],
  details: '',
})

const selectedShip = computed(() => ships.value.find((ship) => ship.id === Number(form.ship_id)))
const crewCapacity = computed(() => selectedShip.value?.crew_capacity || 0)
const sailorMinimum = computed(() => selectedShip.value?.sailor_minimum || 0)

const crewTotal = computed(
  () => Number(form.sailors) + Number(form.soldiers) + Number(form.musketeers) + Number(form.mercenaries),
)
const crewRemaining = computed(() => Math.max(0, crewCapacity.value - crewTotal.value))
const crewOverLimit = computed(() => crewCapacity.value > 0 && crewTotal.value > crewCapacity.value)
const sailorsBelowMinimum = computed(() => Number(form.sailors) < sailorMinimum.value)
const crewInvalid = computed(() => crewOverLimit.value || sailorsBelowMinimum.value)

const canSubmit = computed(
  () => form.build_name.trim() && form.ship_id && !crewInvalid.value && !saving.value,
)

function normalizeInventorySlots(slots) {
  return slots
    .map((slot) => ({
      item: String(slot?.item || '').trim(),
      quantity: Math.max(1, Number(slot?.quantity) || 1),
    }))
    .filter((slot) => slot.item)
}

function inventoryCount(fieldName) {
  return normalizeInventorySlots(form[fieldName]).length
}

function isOptionUsed(slots, option, currentIndex) {
  return slots.some((slot, index) => index !== currentIndex && slot.item === option)
}

function onInventorySlotChange(fieldName) {
  const maxSlots = inventoryLimits[fieldName]
  const filled = normalizeInventorySlots(form[fieldName]).slice(0, maxSlots)

  if (filled.length < maxSlots) {
    filled.push(emptySlot())
  }

  form[fieldName].splice(0, form[fieldName].length, ...filled)
}

function setCrewToShipMinimum() {
  form.sailors = sailorMinimum.value
  form.soldiers = 0
  form.musketeers = 0
  form.mercenaries = 0
}

function resetInventory() {
  form.ammunition_slots = [emptySlot()]
  form.consumable_slots = [emptySlot()]
  form.hold_slots = [emptySlot()]
}

function buildPayload() {
  return {
    ...form,
    ship_id: Number(form.ship_id),
    sailors: Number(form.sailors),
    soldiers: Number(form.soldiers),
    musketeers: Number(form.musketeers),
    mercenaries: Number(form.mercenaries),
    ammunition_slots: normalizeInventorySlots(form.ammunition_slots),
    consumable_slots: normalizeInventorySlots(form.consumable_slots),
    hold_slots: normalizeInventorySlots(form.hold_slots),
  }
}

async function saveBuild() {
  error.value = ''
  if (!canSubmit.value) return

  saving.value = true
  try {
    const created = await createBuild(buildPayload())
    await router.push(`/builds/${created.id}`)
  } catch (err) {
    error.value = err.message || t('builds.create.saveError')
  } finally {
    saving.value = false
  }
}

watch(
  () => form.ship_id,
  () => {
    setCrewToShipMinimum()
  },
)

watch(sailorMinimum, (minimum) => {
  if (Number(form.sailors) < minimum) {
    form.sailors = minimum
  }
})

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const [shipRows, options] = await Promise.all([listShips(), getBuildOptions()])
    ships.value = sortShipsForDropdown(shipRows)
    optionCatalog.value = options
    form.ship_id = ships.value[0]?.id || ''
    resetInventory()
    setCrewToShipMinimum()
  } catch (err) {
    error.value = err.message || t('builds.create.loadError')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="build-create-page" aria-labelledby="build-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean" @submit.prevent="saveBuild">
      <div class="create-topline">
        <div>
          <h1 id="build-create-title">{{ t('builds.create.title') }}</h1>
          <p>{{ t('builds.create.subtitle') }}</p>
        </div>
        <RouterLink class="small-action" to="/builds">{{ t('common.back') }}</RouterLink>
      </div>

      <section class="wire-section form-section identity-section" :aria-label="t('builds.create.sections.identity')">
        <div class="section-title">
          <span>01</span>
          <h2>{{ t('builds.create.sections.identity') }}</h2>
        </div>
        <div class="section-fields two-fields">
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
        </div>
      </section>

      <section class="wire-section form-section ship-section" :aria-label="t('builds.create.sections.ship')">
        <div class="section-title">
          <span>02</span>
          <h2>{{ t('builds.create.sections.ship') }}</h2>
        </div>
        <label class="input-panel embedded-field ship-select-field">
          <select v-model="form.ship_id" required :disabled="loading" :aria-label="t('builds.create.ship')">
            <option value="" disabled>{{ t('builds.create.selectShip') }}</option>
            <option v-for="ship in ships" :key="ship.id" :value="ship.id">
              {{ ship.name }}
            </option>
          </select>
        </label>
        <div v-if="selectedShip" class="ship-stat-row" :aria-label="t('builds.create.sections.ship')">
          <span>{{ t('builds.create.stats.rate', { value: selectedShip.rate }) }}</span>
          <span>{{ t('builds.create.stats.type', { value: selectedShip.ship_type }) }}</span>
          <span>{{ t('builds.create.stats.crew', { value: selectedShip.crew_capacity }) }}</span>
          <span>{{ t('builds.create.stats.sailorMinimum', { value: selectedShip.sailor_minimum }) }}</span>
          <span>{{ t('builds.create.stats.upgrades') }}</span>
        </div>
      </section>

      <section class="wire-section form-section equipment-section" :aria-label="t('builds.create.sections.equipment')">
        <div class="section-title">
          <span>03</span>
          <h2>{{ t('builds.create.sections.equipment') }}</h2>
        </div>
        <div class="equipment-unified-grid">
          <label class="square-slot equipment-slot equipment-slot-sail">
            <span class="slot-visual"><img :src="slotPlaceholderSrc" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.sail') }}</span>
            <span class="select-shell">
              <select v-model="form.sails" :aria-label="t('builds.create.equipment.sail')">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('sail')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>

          <label v-for="index in equipmentUpgradeCount" :key="index" class="square-slot equipment-slot equipment-slot-upgrade">
            <span class="slot-visual"><img :src="slotPlaceholderSrc" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.upgrade', { index }) }}</span>
            <span class="select-shell">
              <select v-model="form[`upgrade_${index}`]" :aria-label="t('builds.create.equipment.upgrade', { index })">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('upgrade')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>

          <label class="square-slot equipment-slot equipment-slot-lantern">
            <span class="slot-visual"><img :src="slotPlaceholderSrc" alt="" /></span>
            <span class="field-caption">{{ t('builds.create.equipment.lantern') }}</span>
            <span class="select-shell">
              <select v-model="form.lantern" :aria-label="t('builds.create.equipment.lantern')">
                <option value="">{{ t('common.empty') }}</option>
                <option v-for="option in optionsFor('lantern')" :key="option" :value="option">{{ optionLabel(option) }}</option>
              </select>
            </span>
          </label>
        </div>
      </section>

      <section class="wire-section form-section crew-section" :aria-label="t('builds.create.sections.crew')">
        <div class="section-title">
          <span>04</span>
          <h2>{{ t('builds.create.sections.crew') }}</h2>
        </div>
        <div class="crew-status" :class="{ 'is-invalid': crewInvalid }">
          <span>{{ t('builds.create.crew.total', { current: crewTotal, max: crewCapacity || '—' }) }}</span>
          <span>{{ t('builds.create.crew.free', { value: crewRemaining }) }}</span>
          <span>{{ t('builds.create.crew.sailorMinimum', { value: sailorMinimum }) }}</span>
          <span v-if="sailorsBelowMinimum">· {{ t('builds.create.crew.tooFewSailors') }}</span>
          <span v-else-if="crewOverLimit">· {{ t('builds.create.crew.tooManyCrew') }}</span>
        </div>

        <div class="crew-grid section-fields">
          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.sailors') }} <strong>{{ form.sailors }}</strong></span>
            <input v-model.number="form.sailors" type="range" :min="sailorMinimum" :max="crewCapacity" />
          </label>

          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.musketeers') }} <strong>{{ form.musketeers }}</strong></span>
            <input v-model.number="form.musketeers" type="range" min="0" :max="crewCapacity" />
          </label>

          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.soldiers') }} <strong>{{ form.soldiers }}</strong></span>
            <input v-model.number="form.soldiers" type="range" min="0" :max="crewCapacity" />
          </label>

          <label class="wire-section slider-panel">
            <span>{{ t('builds.create.crew.mercenaries') }} <strong>{{ form.mercenaries }}</strong></span>
            <input v-model.number="form.mercenaries" type="range" min="0" :max="crewCapacity" />
          </label>
        </div>
      </section>

      <section class="wire-section form-section inventory-section" :aria-label="t('builds.create.sections.inventory')">
        <div class="section-title">
          <span>05</span>
          <h2>{{ t('builds.create.sections.inventory') }}</h2>
        </div>
        <div class="inventory-grid three-columns">
          <div class="inventory-panel ammunition-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.ammunition') }}</strong>
              <span>{{ t('builds.create.inventory.slotCount', { count: inventoryCount('ammunition_slots') }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.ammunitionHint') }}</p>
            <label v-for="(slot, index) in form.ammunition_slots" :key="`ammo-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.inventory.ammunitionAlt', { index: index + 1 })" />
              </span>
              <select v-model="slot.item" @change="onInventorySlotChange('ammunition_slots')">
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
                v-model.number="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventorySlotChange('ammunition_slots')"
              />
            </label>
          </div>

          <div class="inventory-panel consumable-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.consumables') }}</strong>
              <span>{{ t('builds.create.inventory.limitedSlotCount', { count: inventoryCount('consumable_slots'), max: 3 }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.consumablesHint') }}</p>
            <label v-for="(slot, index) in form.consumable_slots" :key="`consumable-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.inventory.consumableAlt', { index: index + 1 })" />
              </span>
              <select v-model="slot.item" @change="onInventorySlotChange('consumable_slots')">
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
                v-model.number="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventorySlotChange('consumable_slots')"
              />
            </label>
          </div>

          <div class="inventory-panel hold-panel">
            <div class="inventory-heading">
              <strong>{{ t('builds.create.inventory.hold') }}</strong>
              <span>{{ t('builds.create.inventory.slotCount', { count: inventoryCount('hold_slots') }) }}</span>
            </div>
            <p class="slot-hint">{{ t('builds.create.inventory.holdHint') }}</p>
            <label v-for="(slot, index) in form.hold_slots" :key="`hold-${index}`" class="inventory-slot-select with-quantity">
              <span class="slot-image-cell">
                <img :src="slotPlaceholderSrc" :alt="t('builds.create.inventory.holdAlt', { index: index + 1 })" />
              </span>
              <select v-model="slot.item" @change="onInventorySlotChange('hold_slots')">
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
                v-model.number="slot.quantity"
                type="number"
                min="1"
                max="999999"
                :aria-label="t('common.quantity')"
                @change="onInventorySlotChange('hold_slots')"
              />
            </label>
          </div>
        </div>
      </section>

      <section class="wire-section form-section details-section" :aria-label="t('builds.create.sections.details')">
        <div class="section-title">
          <span>06</span>
          <h2>{{ t('builds.create.sections.details') }}</h2>
        </div>
        <label class="input-panel embedded-field details-field">
          <textarea v-model="form.details" rows="4" maxlength="3000" :placeholder="t('builds.create.detailsPlaceholder')"></textarea>
        </label>
      </section>

      <p v-if="error" class="error-text">{{ error }}</p>

      <div class="form-actions">
        <RouterLink class="wire-section form-button" to="/builds">{{ t('common.cancel') }}</RouterLink>
        <button class="wire-section form-button primary" type="submit" :disabled="!canSubmit">
          {{ saving ? t('builds.create.saving') : t('builds.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
