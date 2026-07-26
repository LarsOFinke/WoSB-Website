<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import { useLocale } from '@/locales'

defineProps({
  membership: { type: Object, required: true },
  management: { type: Object, required: true },
  roleOptions: { type: Array, default: () => [] },
  roleLabel: { type: Function, required: true },
  protectionLabel: { type: String, default: '' },
  mode: { type: String, default: 'members' },
})

const emit = defineEmits(['save'])
const { t } = useLocale()

function fieldValue(field, event) {
  emit('save', { [field]: event.target.value.trim() || null })
}
</script>

<template>
  <article class="fleet-refresh-member" :class="[`mode-${mode}`, { 'is-protected': management.protected }]">
    <div class="fleet-refresh-member-identity">
      <span class="fleet-refresh-member-avatar" aria-hidden="true">{{ membership.user.display_name.slice(0, 2).toUpperCase() }}</span>
      <span>
        <strong>{{ membership.user.display_name }}</strong>
        <small>@{{ membership.user.username }}</small>
      </span>
    </div>

    <div class="fleet-refresh-member-status">
      <span>{{ t(`fleets.status.${membership.status}`) }}</span>
      <small>{{ roleLabel(membership.role) }}</small>
    </div>

    <div class="fleet-refresh-member-assignment">
      <strong>{{ membership.assignment || roleLabel(membership.role) }}</strong>
      <small>{{ membership.availability || membership.timezone || '—' }}</small>
    </div>

    <div class="fleet-refresh-member-contact">
      <span>{{ membership.discord_handle || '—' }}</span>
      <small>{{ membership.preferred_ships || membership.timezone || '—' }}</small>
    </div>

    <div class="fleet-refresh-member-controls">
      <div v-if="management.protected" class="fleet-refresh-protection">
        <AppIcon name="shield" :size="15" />
        <small>{{ protectionLabel }}</small>
      </div>

      <template v-if="mode === 'requests'">
        <button v-if="management.can_change_status" class="small-action" type="button" @click="emit('save', { status: 'active' })">{{ t('fleets.manage.approve') }}</button>
        <button v-if="management.can_change_status" class="danger-action" type="button" @click="emit('save', { status: 'inactive' })">{{ t('fleets.manage.reject') }}</button>
      </template>

      <template v-else>
        <label v-if="management.can_change_role" class="fleet-refresh-role-select">
          <span>{{ t('fleets.manage.role') }}</span>
          <select :value="membership.role" @change="emit('save', { role: $event.target.value })">
            <option v-for="role in roleOptions" :key="role" :value="role">{{ roleLabel(role) }}</option>
          </select>
        </label>
        <details v-if="management.can_edit_directory" class="fleet-refresh-member-details">
          <summary>{{ t('fleets.manage.extendedDirectory') }}</summary>
          <label><span>{{ t('fleets.directory.assignment') }}</span><input :value="membership.assignment || ''" maxlength="120" @change="fieldValue('assignment', $event)" /></label>
          <label><span>{{ t('fleets.directory.adminNote') }}</span><input :value="membership.admin_note || ''" maxlength="1200" @change="fieldValue('admin_note', $event)" /></label>
        </details>
        <button v-if="management.can_change_status && membership.status !== 'inactive'" class="danger-action" type="button" @click="emit('save', { status: 'inactive' })">{{ t('fleets.manage.deactivate') }}</button>
        <button v-else-if="management.can_change_status" class="small-action" type="button" @click="emit('save', { status: 'active' })">{{ t('fleets.manage.activate') }}</button>
      </template>
    </div>

    <p v-if="membership.note" class="fleet-refresh-member-note">{{ membership.note }}</p>
  </article>
</template>
