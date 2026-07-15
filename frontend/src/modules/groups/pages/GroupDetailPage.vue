<script setup>
import { useGroupDetailPage } from '@/modules/groups/composables/useGroupDetailPage.js'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const {
  t, isAuthenticated, isStaff, user, group,
  ships, builds, loading, joining, closing,
  error, joinError, joinSuccess, joinForm, canManage,
  canJoin, selectedBuild, selectedShip, allowedShips, allowedBuilds,
  rateRequirementText, scheduleText, formatDateTime, isShipAllowed, memberShipLabel,
  loadAuxiliaryData, loadGroup, submitJoin, submitClose,
} = useGroupDetailPage(props)
</script>

<template>
  <section class="group-detail-page" aria-labelledby="group-detail-title">
    <div class="wire-frame page-frame detail-frame group-detail-frame">
      <header class="wire-section detail-header group-detail-header">
        <RouterLink class="small-action" to="/groups">{{ t('common.back') }}</RouterLink>
        <div v-if="group">
          <p class="eyebrow">{{ t('groups.detail.announcementEyebrow') }} · {{ t(`focus.${group.focus}`) }}</p>
          <h1 id="group-detail-title">{{ group.title }}</h1>
          <p>{{ group.description || t('groups.detail.noDescription') }}</p>
        </div>
      </header>

      <p v-if="loading" class="wire-section muted">{{ t('groups.detail.loading') }}</p>
      <p v-else-if="error" class="wire-section error-text">{{ error }}</p>

      <template v-else-if="group">
        <section class="wire-section group-overview-grid announcement-overview-grid">
          <div class="group-stat-card">
            <span>{{ t('groups.fields.status') }}</span>
            <strong>{{ t(`groups.status.${group.status}`) }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.schedule') }}</span>
            <strong>{{ scheduleText }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.members') }}</span>
            <strong>{{ t('groups.list.members', { current: group.active_members_count, max: group.max_members }) }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.rateRange') }}</span>
            <strong>{{ rateRequirementText }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.leader') }}</span>
            <strong>{{ group.owner.display_name }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.fleetRestriction') }}</span>
            <strong>{{ group.fleet_restriction || t('groups.list.noFleetRestriction') }}</strong>
          </div>
        </section>

        <section class="group-detail-grid announcement-detail-grid">
          <section class="wire-section group-members-panel announcement-copy-panel">
            <div class="section-heading-row">
              <div>
                <p class="eyebrow">{{ t('groups.detail.overviewTitle') }}</p>
                <h2>{{ t('groups.detail.membersTitle') }}</h2>
              </div>
              <span class="summary-pill">{{ t('groups.list.spotsLeft', { count: group.spots_left }) }}</span>
            </div>

            <p v-if="group.members.length === 0" class="muted">{{ t('groups.detail.noMembers') }}</p>
            <div v-else class="group-member-list">
              <article v-for="member in group.members" :key="member.id" class="group-member-row">
                <div>
                  <strong>{{ member.display_name }}</strong>
                  <span>{{ member.is_guest ? t('groups.detail.guest') : t('groups.detail.member') }}</span>
                </div>
                <div>
                  <span>{{ memberShipLabel(member) }}</span>
                  <small v-if="member.note">{{ member.note }}</small>
                </div>
              </article>
            </div>
          </section>

          <aside class="wire-section group-join-panel announcement-mode-panel">
            <p class="eyebrow">{{ t('groups.detail.joinEyebrow') }}</p>
            <h2>{{ canJoin ? t('groups.detail.joinTitle') : t('groups.detail.joinClosedTitle') }}</h2>
            <p>{{ canJoin ? t('groups.detail.joinTextWithRate', { requirement: rateRequirementText }) : t('groups.detail.joinClosedText') }}</p>

            <form v-if="canJoin" class="group-join-form" @submit.prevent="submitJoin">
              <label class="input-panel embedded-field">
                <span>{{ t('groups.fields.displayName') }}</span>
                <input v-model="joinForm.display_name" required maxlength="120" :placeholder="t('groups.detail.displayNamePlaceholder')" />
              </label>

              <label v-if="isAuthenticated" class="input-panel embedded-field select-shell full-select-shell">
                <span>{{ t('groups.fields.linkedBuild') }}</span>
                <select v-model="joinForm.build_id">
                  <option value="">{{ t('groups.detail.noLinkedBuild') }}</option>
                  <option v-for="build in allowedBuilds" :key="build.id" :value="build.id">
                    {{ build.build_name }} · {{ build.ship.name }} · {{ t('common.rate') }} {{ build.ship.rate }}
                  </option>
                </select>
              </label>

              <label class="input-panel embedded-field select-shell full-select-shell">
                <span>{{ t('groups.fields.ship') }}</span>
                <select v-model="joinForm.ship_id" :disabled="Boolean(joinForm.build_id)">
                  <option value="">{{ t('groups.detail.noShipSelection') }}</option>
                  <option v-for="ship in allowedShips" :key="ship.id" :value="ship.id">
                    {{ ship.name }} · {{ t('common.rate') }} {{ ship.rate }}
                  </option>
                </select>
              </label>

              <label class="input-panel embedded-field textarea-shell">
                <span>{{ t('groups.fields.note') }}</span>
                <textarea v-model="joinForm.note" rows="3" maxlength="1000" :placeholder="t('groups.detail.joinNotePlaceholder')"></textarea>
              </label>

              <p v-if="selectedShip" class="success-text compact-message">
                {{ t('groups.detail.rateOk', { rate: selectedShip.rate }) }}
              </p>
              <p v-if="joinError" class="error-text compact-message">{{ joinError }}</p>
              <p v-if="joinSuccess" class="success-text compact-message">{{ joinSuccess }}</p>

              <button class="form-button primary-action" type="submit" :disabled="joining">
                {{ joining ? t('groups.detail.joining') : t('groups.detail.join') }}
              </button>
            </form>

            <div v-if="canManage" class="group-management-actions">
              <button class="danger-action" type="button" :disabled="closing || group.status === 'closed'" @click="submitClose">
                {{ closing ? t('groups.detail.closing') : t('groups.detail.close') }}
              </button>
            </div>
          </aside>
        </section>

        <section class="announcement-info-grid">
          <article class="wire-section detail-card announcement-info-card">
            <span>{{ t('groups.detail.expectationsTitle') }}</span>
            <p>{{ group.expectations || t('groups.detail.noExpectations') }}</p>
          </article>
          <article class="wire-section detail-card announcement-info-card">
            <span>{{ t('groups.detail.activityPlanTitle') }}</span>
            <p>{{ group.activity_plan || t('groups.detail.noActivityPlan') }}</p>
          </article>
          <article class="wire-section detail-card announcement-info-card">
            <span>{{ t('groups.detail.contactTitle') }}</span>
            <p>{{ group.contact_note || t('groups.detail.noContact') }}</p>
          </article>
        </section>
      </template>
    </div>
  </section>
</template>
