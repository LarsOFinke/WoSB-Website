<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useSquadDetailPage } from '@/modules/squads/composables/useSquadDetailPage.js'

const props = defineProps({
  id: { type: Number, required: true },
})

const {
  router, t, canManageFleet, squad, roster,
  loading, saving, memberSavingId, adding, archiving,
  error, success, editForm, addForm, memberDrafts,
  availableRoster, roleOptions, addRoleOptions, canArchive, syncDrafts,
  loadSquad, saveSquad, addMember, saveMember, canRemove,
  removeMember, archiveCurrentSquad,
} = useSquadDetailPage(props)
</script>

<template>
  <section class="squad-page" aria-labelledby="squad-detail-title">
    <div class="wire-frame page-frame squad-frame squad-detail-frame">
      <PageHeader
        :eyebrow="t('squads.detail.eyebrow')"
        :title="squad?.name || t('squads.detail.title')"
        :description="squad?.description || t('squads.detail.subtitle')"
        title-id="squad-detail-title"
      >
        <template #meta>
          <span v-if="squad" class="summary-pill">{{ squad.is_active ? t('squads.status.active') : t('squads.status.archived') }}</span>
          <span v-if="squad?.is_member" class="summary-pill">{{ t('squads.list.memberBadge') }}</span>
          <span v-if="squad?.can_manage" class="summary-pill">{{ t('squads.list.commandBadge') }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/squads">{{ t('common.back') }}</RouterLink>
          <RouterLink
            v-if="squad?.is_member || squad?.can_manage"
            class="button-box"
            :to="{ path: '/calendar', query: { squad: squad.id } }"
          >
            {{ t('squads.detail.openCalendar') }}
          </RouterLink>
          <RouterLink
            v-if="canManageFleet && squad?.can_manage && squad?.is_active"
            class="button-box primary-action"
            :to="{ path: '/calendar/new', query: { squad: squad.id } }"
          >
            {{ t('squads.detail.newEvent') }}
          </RouterLink>
        </template>
      </PageHeader>

      <p v-if="loading" class="wire-section muted table-state">{{ t('squads.detail.loading') }}</p>
      <p v-else-if="error && !squad" class="wire-section error-text table-state">{{ error }}</p>

      <template v-else-if="squad">
        <section class="squad-overview-grid">
          <article class="wire-section squad-command-card">
            <span class="squad-mark"><AppIcon name="shield" :size="22" /></span>
            <div>
              <p class="eyebrow">{{ t('squads.fields.leader') }}</p>
              <h2>{{ squad.leader?.display_name || t('squads.list.noLeader') }}</h2>
              <p>{{ t('squads.detail.leaderText') }}</p>
            </div>
          </article>
          <article class="wire-section squad-overview-card">
            <span>{{ t('squads.fields.focus') }}</span>
            <strong>{{ squad.focus || t('squads.list.noFocus') }}</strong>
          </article>
          <article class="wire-section squad-overview-card">
            <span>{{ t('squads.fields.members') }}</span>
            <strong>{{ squad.max_members ? `${squad.member_count}/${squad.max_members}` : squad.member_count }}</strong>
          </article>
        </section>

        <p v-if="error" class="wire-section error-text table-state">{{ error }}</p>
        <p v-if="success" class="wire-section success-text table-state">{{ success }}</p>

        <section v-if="canManageFleet && squad.can_manage" class="wire-section squad-editor-panel">
          <div class="section-heading-row">
            <div>
              <p class="eyebrow">{{ t('squads.detail.managementEyebrow') }}</p>
              <h2>{{ t('squads.detail.managementTitle') }}</h2>
              <p>{{ t('squads.detail.managementText') }}</p>
            </div>
          </div>
          <form class="squad-edit-form" @submit.prevent="saveSquad">
            <div class="squad-form-grid">
              <label class="field-stack">
                <span class="field-label">{{ t('squads.fields.name') }}</span>
                <span class="input-panel embedded-field"><input v-model="editForm.name" required minlength="2" maxlength="120" /></span>
              </label>
              <label class="field-stack">
                <span class="field-label">{{ t('squads.fields.focus') }}</span>
                <span class="input-panel embedded-field"><input v-model="editForm.focus" maxlength="160" /></span>
              </label>
              <label class="field-stack">
                <span class="field-label">{{ t('squads.fields.maxMembers') }}</span>
                <span class="input-panel embedded-field"><input v-model.number="editForm.maxMembers" type="number" min="2" max="200" /></span>
              </label>
            </div>
            <label class="field-stack">
              <span class="field-label">{{ t('squads.fields.description') }}</span>
              <span class="input-panel embedded-field textarea-shell"><textarea v-model="editForm.description" rows="4" maxlength="3000"></textarea></span>
            </label>
            <div class="compact-actions">
              <button class="form-button primary-action" type="submit" :disabled="saving">
                {{ saving ? t('common.saving') : t('squads.detail.save') }}
              </button>
              <button v-if="canArchive" class="danger-action" type="button" :disabled="archiving" @click="archiveCurrentSquad">
                {{ archiving ? t('squads.detail.archiving') : t('squads.detail.archive') }}
              </button>
            </div>
          </form>
        </section>

        <section class="wire-section squad-roster-panel">
          <div class="section-heading-row">
            <div>
              <p class="eyebrow">{{ t('squads.detail.rosterEyebrow') }}</p>
              <h2>{{ t('squads.detail.rosterTitle') }}</h2>
              <p>{{ t('squads.detail.rosterText') }}</p>
            </div>
            <span class="summary-pill">{{ t('squads.detail.rosterCount', { count: squad.members.length }) }}</span>
          </div>

          <form v-if="canManageFleet && squad.can_manage && availableRoster.length" class="squad-add-member-form" @submit.prevent="addMember">
            <label class="field-stack squad-member-select">
              <span class="field-label">{{ t('squads.detail.addMember') }}</span>
              <span class="select-shell full-select-shell">
                <select v-model="addForm.fleetMembershipId" required>
                  <option value="">{{ t('squads.detail.selectMember') }}</option>
                  <option v-for="member in availableRoster" :key="member.fleet_membership_id" :value="member.fleet_membership_id">
                    {{ member.display_name }} · {{ t(`fleets.roles.${member.fleet_role}`) }}
                  </option>
                </select>
              </span>
            </label>
            <label class="field-stack">
              <span class="field-label">{{ t('squads.fields.role') }}</span>
              <span class="select-shell full-select-shell">
                <select v-model="addForm.role">
                  <option v-for="option in addRoleOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </span>
            </label>
            <label class="field-stack squad-note-field">
              <span class="field-label">{{ t('squads.fields.note') }}</span>
              <span class="input-panel embedded-field"><input v-model="addForm.note" maxlength="1000" /></span>
            </label>
            <button class="form-button primary-action" type="submit" :disabled="adding || !addForm.fleetMembershipId">
              {{ adding ? t('squads.detail.adding') : t('squads.detail.add') }}
            </button>
          </form>

          <div class="squad-member-list">
            <article v-for="member in squad.members" :key="member.id" class="squad-member-row">
              <div class="squad-member-identity">
                <span class="squad-member-avatar">{{ member.display_name.slice(0, 2).toUpperCase() }}</span>
                <div>
                  <strong>{{ member.display_name }}</strong>
                  <span>{{ t(`fleets.roles.${member.fleet_role}`) }}</span>
                </div>
              </div>

              <template v-if="canManageFleet && squad.can_manage && memberDrafts[member.id]">
                <label class="field-stack squad-member-role-field">
                  <span class="field-label">{{ t('squads.fields.role') }}</span>
                  <span class="select-shell full-select-shell">
                    <select v-model="memberDrafts[member.id].role" :disabled="!squad.can_administer">
                      <option v-for="option in roleOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                  </span>
                </label>
                <label class="field-stack squad-member-note-field">
                  <span class="field-label">{{ t('squads.fields.note') }}</span>
                  <span class="input-panel embedded-field"><input v-model="memberDrafts[member.id].note" maxlength="1000" /></span>
                </label>
                <div class="compact-actions squad-member-actions">
                  <button class="small-action" type="button" :disabled="memberSavingId === member.id" @click="saveMember(member)">
                    {{ t('common.save') }}
                  </button>
                  <button v-if="canRemove(member)" class="danger-action" type="button" :disabled="memberSavingId === member.id" @click="removeMember(member)">
                    {{ t('common.remove') }}
                  </button>
                </div>
              </template>
              <template v-else>
                <span class="type-pill" :class="{ 'event-training': member.squad_role === 'leader' }">{{ t(`squads.roles.${member.squad_role}`) }}</span>
              </template>
            </article>
          </div>
        </section>
      </template>
    </div>
  </section>
</template>
