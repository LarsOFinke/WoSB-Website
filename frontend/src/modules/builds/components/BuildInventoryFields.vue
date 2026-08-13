<script setup>
defineProps({
  t: { type: Function, required: true },
  form: { type: Object, required: true },
  slotCount: { type: Function, required: true },
  inventoryImage: { type: Function, required: true },
  optionsFor: { type: Function, required: true },
  optionLabel: { type: Function, required: true },
  isOptionUsed: { type: Function, required: true },
  onInventoryItemChange: { type: Function, required: true },
  onInventoryQuantityChange: { type: Function, required: true },
})

const inventoryGroups = [
  {
    fieldName: 'ammunition_slots', category: 'ammunition', label: 'ammunition',
    hint: 'ammunitionHint', alt: 'ammunitionAlt', itemKey: 'ammo', panelClass: 'ammunition-panel',
  },
  {
    fieldName: 'consumable_slots', category: 'consumable', label: 'consumables',
    hint: 'consumablesHint', alt: 'consumableAlt', itemKey: 'consumable', panelClass: 'consumable-panel',
    maxSlots: 3,
  },
  {
    fieldName: 'hold_slots', category: 'hold', label: 'hold',
    hint: 'holdHint', alt: 'holdAlt', itemKey: 'hold', panelClass: 'hold-panel',
  },
]
</script>

<template>
  <section class="wire-section form-section inventory-section compact-inventory-panel" :aria-label="t('builds.create.sections.inventory')">
    <div class="section-title">
      <span>06</span>
      <h2>{{ t('builds.create.sections.inventory') }}</h2>
    </div>
    <div class="inventory-grid three-columns">
      <div v-for="group in inventoryGroups" :key="group.fieldName" class="inventory-panel" :class="group.panelClass">
        <div class="inventory-heading">
          <strong>{{ t(`builds.create.inventory.${group.label}`) }}</strong>
          <span v-if="group.maxSlots">{{ t('builds.create.inventory.limitedSlotCount', { count: slotCount(group.fieldName), max: group.maxSlots }) }}</span>
          <span v-else>{{ t('builds.create.inventory.slotCount', { count: slotCount(group.fieldName) }) }}</span>
        </div>
        <p class="slot-hint">{{ t(`builds.create.inventory.${group.hint}`) }}</p>
        <label v-for="(slot, index) in form[group.fieldName]" :key="`${group.itemKey}-${index}`" class="inventory-slot-select with-quantity">
          <span class="slot-image-cell">
            <img :src="inventoryImage(group.fieldName, slot.item)" :alt="t(`builds.create.inventory.${group.alt}`, { index: index + 1 })" />
          </span>
          <select :value="slot.item" @change="onInventoryItemChange(group.fieldName, index, $event)">
            <option value="">{{ t('common.empty') }}</option>
            <option
              v-for="option in optionsFor(group.category)"
              :key="option"
              :value="option"
              :disabled="isOptionUsed(form[group.fieldName], option, index)"
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
            @change="onInventoryQuantityChange(group.fieldName, index, $event)"
          />
        </label>
      </div>
    </div>
  </section>
</template>
