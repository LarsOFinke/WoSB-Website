<script setup>
defineProps({
  title: { type: String, required: true },
  draft: { type: Object, required: true },
  fleets: { type: Array, default: () => [] },
  members: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  t: { type: Function, required: true },
})

defineEmits(['cancel', 'fleet-change', 'save'])
</script>

<template>
  <div class="warehouse-editor-backdrop" @click.self="$emit('cancel')">
    <section class="warehouse-editor wire-section" role="dialog" aria-modal="true" aria-labelledby="warehouse-editor-title">
      <header class="warehouse-editor__header">
        <div>
          <p class="eyebrow">{{ t('warehouse.editor.eyebrow') }}</p>
          <h2 id="warehouse-editor-title">{{ title }}</h2>
        </div>
        <button class="small-action" type="button" :aria-label="t('common.close')" @click="$emit('cancel')">×</button>
      </header>

      <form class="warehouse-editor__form" @submit.prevent="$emit('save')">
        <label class="input-panel">
          <span>{{ t('warehouse.fields.fleet') }}</span>
          <select v-model="draft.fleet_id" :aria-label="t('warehouse.fields.fleet')" required @change="$emit('fleet-change')">
            <option value="" disabled>{{ t('warehouse.editor.selectFleet') }}</option>
            <option v-for="fleet in fleets" :key="fleet.id" :value="fleet.id">{{ fleet.name }}</option>
          </select>
        </label>

        <fieldset class="warehouse-holder-fieldset">
          <legend>{{ t('warehouse.fields.holder') }}</legend>
          <div class="warehouse-holder-modes">
            <label><input v-model="draft.holder_mode" type="radio" value="member" /> {{ t('warehouse.editor.member') }}</label>
            <label><input v-model="draft.holder_mode" type="radio" value="custom" /> {{ t('warehouse.editor.custom') }}</label>
          </div>
          <label v-if="draft.holder_mode === 'member'" class="input-panel">
            <span>{{ t('warehouse.editor.member') }}</span>
            <select v-model="draft.member_user_id" :aria-label="t('warehouse.editor.member')" required>
              <option value="" disabled>{{ t('warehouse.editor.selectMember') }}</option>
              <option v-for="member in members" :key="member.id" :value="member.id">{{ member.display_name }}</option>
            </select>
          </label>
          <label v-else class="input-panel">
            <span>{{ t('warehouse.fields.customHolder') }}</span>
            <input v-model.trim="draft.custom_holder_name" maxlength="120" required />
          </label>
        </fieldset>

        <div class="warehouse-editor__grid">
          <label class="input-panel"><span>{{ t('warehouse.fields.port') }}</span><input v-model.trim="draft.port" maxlength="120" required /></label>
          <label class="input-panel"><span>{{ t('warehouse.fields.resource') }}</span><input v-model.trim="draft.resource" maxlength="120" required /></label>
          <label class="input-panel"><span>{{ t('warehouse.fields.amount') }}</span><input v-model.number="draft.amount" type="number" min="0" max="999999999" step="1" required /></label>
          <label class="warehouse-reserved-toggle"><input v-model="draft.reserved" type="checkbox" /><span>{{ t('warehouse.fields.reserved') }}</span></label>
        </div>

        <footer class="warehouse-editor__actions">
          <button class="button-box" type="button" :disabled="saving" @click="$emit('cancel')">{{ t('common.cancel') }}</button>
          <button class="button-box primary-action" type="submit" :disabled="saving">{{ saving ? t('warehouse.actions.saving') : t('warehouse.actions.save') }}</button>
        </footer>
      </form>
    </section>
  </div>
</template>
