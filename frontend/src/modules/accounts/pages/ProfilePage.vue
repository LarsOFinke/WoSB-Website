<script setup>
import { computed } from 'vue'

import AppIcon from '@/core/components/AppIcon.vue'
import WorkspaceStatRail from '@/core/components/WorkspaceStatRail.vue'
import PreferenceTransferList from '@/modules/accounts/components/PreferenceTransferList.vue'
import { useProfilePage } from '@/modules/accounts/composables/useProfilePage.js'
import '@/styles/workspaceRefresh.css'
import '@/modules/accounts/styles/profileWorkspace.css'

const {
  t, loading, saving, changingPassword,
  error, success, passwordError, passwordSuccess,
  activeFleetMemberships, leadershipMemberships, primaryFleetMembership, hasOfficialFleetLink,
  displayInitials, preferredFocusLabel, preferredShipOptions, preferredRoleOptions, fleetStatusLabel,
  profileCompletion, profileCompletionHint, focusOptions, form, passwordForm,
  saveProfile, submitPasswordChange,
} = useProfilePage()

const profileStats = computed(() => [
  { key: 'account', icon: 'user', label: t('profile.account'), value: t(`roles.${form.role}`), hint: `@${form.username}` },
  { key: 'fleet', icon: 'fleet', label: t('profile.fleetMemberships.title'), value: fleetStatusLabel.value, hint: form.fleet_name || t('fleets.title') },
  { key: 'focus', icon: 'compass', label: t('profile.preferredFocus'), value: preferredFocusLabel.value },
  { key: 'completion', icon: 'shield', label: t('profile.completion.label'), value: `${profileCompletion.value}%`, hint: profileCompletionHint.value },
])
</script>

<template>
  <section class="profile-refresh-page" aria-labelledby="profile-title">
    <div class="wire-frame page-frame profile-refresh-frame">
      <header class="workspace-command-header profile-refresh-header">
        <div class="profile-refresh-identity">
          <span class="profile-refresh-avatar" aria-hidden="true">{{ displayInitials }}</span>
          <div>
            <h1 id="profile-title">{{ form.display_name || form.username || t('profile.title') }}</h1>
            <p>{{ t('profile.subtitle') }}</p>
          </div>
        </div>
        <nav class="workspace-command-actions" :aria-label="t('common.personalArea')">
          <RouterLink class="button-box" to="/profile/builds">{{ t('myBuilds.title') }}</RouterLink>
          <RouterLink class="button-box" to="/profile/groups">{{ t('myGroups.title') }}</RouterLink>
          <RouterLink class="button-box primary-action" to="/profile/squads">{{ t('mySquads.title') }}</RouterLink>
        </nav>
      </header>

      <p v-if="loading" class="muted table-state">{{ t('profile.loading') }}</p>

      <template v-else>
        <WorkspaceStatRail :items="profileStats" :label="t('profile.title')" />

        <div class="profile-refresh-main">
          <form class="profile-refresh-editor" @submit.prevent="saveProfile">
            <section class="profile-refresh-section">
              <h2>{{ t('profile.displayName') }}</h2>
              <p>{{ t('profile.subtitle') }}</p>
              <div class="profile-refresh-fields">
                <label class="input-panel embedded-field">
                  <span>{{ t('profile.displayName') }}</span>
                  <input v-model="form.display_name" required maxlength="120" />
                </label>
                <label class="input-panel embedded-field">
                  <span>{{ t('profile.preferredFocus') }}</span>
                  <select v-model="form.preferred_focus">
                    <option value="">{{ t('profile.noPreferredFocus') }}</option>
                    <option v-for="focus in focusOptions" :key="focus" :value="focus">{{ t(`focus.${focus}`) }}</option>
                  </select>
                </label>
                <label v-if="!hasOfficialFleetLink" class="input-panel embedded-field profile-refresh-wide">
                  <span>{{ t('profile.externalFleetName') }}</span>
                  <input v-model="form.fleet_name" maxlength="120" :placeholder="t('profile.fleetPlaceholder')" />
                  <small>{{ t('profile.externalFleetHint') }}</small>
                </label>
                <label class="input-panel embedded-field">
                  <span>{{ t('fleets.directory.availability') }}</span>
                  <input v-model="form.availability" maxlength="240" :placeholder="t('fleets.directory.availabilityPlaceholder')" />
                </label>
                <label class="input-panel embedded-field">
                  <span>{{ t('fleets.directory.timezone') }}</span>
                  <input v-model="form.timezone" maxlength="80" :placeholder="t('fleets.directory.timezonePlaceholder')" />
                </label>
                <label class="input-panel embedded-field profile-refresh-wide">
                  <span>{{ t('fleets.directory.discord') }}</span>
                  <input v-model="form.discord_handle" maxlength="120" :placeholder="t('fleets.directory.discordPlaceholder')" />
                </label>
              </div>
            </section>

            <section class="profile-refresh-section">
              <h2>{{ t('profile.preferredFocus') }}</h2>
              <p>{{ profileCompletionHint }}</p>
              <div class="profile-refresh-preferences">
                <fieldset class="input-panel embedded-field">
                  <legend>{{ t('fleets.directory.preferredShips') }}</legend>
                  <PreferenceTransferList v-model="form.preferred_ship_ids" :options="preferredShipOptions" />
                </fieldset>
                <fieldset class="input-panel embedded-field">
                  <legend>{{ t('fleets.directory.preferredRoles') }}</legend>
                  <PreferenceTransferList v-model="form.preferred_role_ids" :options="preferredRoleOptions" />
                </fieldset>
                <label class="input-panel embedded-field">
                  <span>{{ t('profile.note') }}</span>
                  <textarea v-model="form.note" maxlength="1000" rows="6" :placeholder="t('profile.notePlaceholder')"></textarea>
                </label>
              </div>
            </section>

            <p v-if="error" class="error-text profile-message">{{ error }}</p>
            <p v-if="success" class="success-text profile-message">{{ success }}</p>
            <div class="profile-refresh-save">
              <span class="muted">@{{ form.username }}</span>
              <button class="form-button primary-action" type="submit" :disabled="saving">
                {{ saving ? t('profile.saving') : t('profile.save') }}
              </button>
            </div>
          </form>

          <aside class="profile-refresh-side">
            <section>
              <div class="profile-refresh-side-heading">
                <h2>{{ t('profile.fleetMemberships.title') }}</h2>
                <span v-if="hasOfficialFleetLink" class="summary-pill">{{ t(`fleets.status.${form.fleet_membership_status}`) }}</span>
              </div>
              <div v-if="hasOfficialFleetLink" class="profile-refresh-fleet">
                <div><strong>{{ form.fleet_name }}</strong><span>{{ t(`fleets.roles.${form.fleet_membership_role || 'member'}`) }}</span></div>
                <small>{{ primaryFleetMembership ? t(`fleets.focus.${primaryFleetMembership.fleet.focus}`) : t('profile.fleetMemberships.syncedHint') }}</small>
              </div>
              <p v-else class="muted">{{ t('profile.fleetMemberships.empty') }}</p>
              <div v-if="activeFleetMemberships.length > 1" class="profile-refresh-memberships">
                <article v-for="membership in activeFleetMemberships" :key="membership.id">
                  <strong>{{ membership.fleet.name }}</strong>
                  <span>{{ t(`fleets.roles.${membership.role}`) }}</span>
                </article>
              </div>
              <div class="form-actions compact-actions">
                <RouterLink class="button-box" to="/fleet">{{ t('profile.fleetMemberships.browse') }}</RouterLink>
                <RouterLink v-if="leadershipMemberships.length" class="button-box primary-action" to="/fleets">{{ t('profile.fleetMemberships.manage') }}</RouterLink>
              </div>
            </section>

            <section>
              <div class="profile-refresh-side-heading"><h2>{{ t('common.modules') }}</h2></div>
              <nav class="profile-refresh-tools" :aria-label="t('common.modules')">
                <RouterLink class="profile-refresh-tool" to="/profile/builds"><span><AppIcon name="builds" :size="18" /></span><span><strong>{{ t('myBuilds.profileCardTitle') }}</strong><small>{{ t('myBuilds.profileCardText') }}</small></span><AppIcon name="chevron-right" :size="17" /></RouterLink>
                <RouterLink class="profile-refresh-tool" to="/profile/groups"><span><AppIcon name="groups" :size="18" /></span><span><strong>{{ t('myGroups.profileCardTitle') }}</strong><small>{{ t('myGroups.profileCardText') }}</small></span><AppIcon name="chevron-right" :size="17" /></RouterLink>
                <RouterLink class="profile-refresh-tool" to="/profile/squads"><span><AppIcon name="users" :size="18" /></span><span><strong>{{ t('mySquads.profileCardTitle') }}</strong><small>{{ t('mySquads.profileCardText') }}</small></span><AppIcon name="chevron-right" :size="17" /></RouterLink>
              </nav>
            </section>

            <details class="profile-refresh-security">
              <summary><h3>{{ t('profile.password.title') }}</h3></summary>
              <form class="profile-refresh-password" @submit.prevent="submitPasswordChange">
                <p class="muted">{{ t('profile.password.subtitle') }}</p>
                <label class="input-panel embedded-field"><span>{{ t('profile.password.current') }}</span><input v-model="passwordForm.current_password" type="password" autocomplete="current-password" required /></label>
                <label class="input-panel embedded-field"><span>{{ t('profile.password.new') }}</span><input v-model="passwordForm.new_password" type="password" autocomplete="new-password" required minlength="12" /></label>
                <label class="input-panel embedded-field"><span>{{ t('profile.password.repeat') }}</span><input v-model="passwordForm.repeat_password" type="password" autocomplete="new-password" required minlength="12" /></label>
                <p v-if="passwordError" class="error-text profile-message">{{ passwordError }}</p>
                <p v-if="passwordSuccess" class="success-text profile-message">{{ passwordSuccess }}</p>
                <button class="form-button" type="submit" :disabled="changingPassword">{{ changingPassword ? t('profile.password.saving') : t('profile.password.save') }}</button>
              </form>
            </details>
          </aside>
        </div>
      </template>
    </div>
  </section>
</template>
