<script setup>
import AppIcon from '@/core/components/AppIcon.vue'
import PageHeader from '@/core/components/PageHeader.vue'
import { useSquadListPage } from '@/modules/squads/composables/useSquadListPage'

const {
  t,
  canManageFleet,
  squads,
  loading,
  error,
  includeInactive,
  activeSquads,
  mySquads,
  managedSquads,
  loadSquads,
} = useSquadListPage()
</script>

<template>
  <section class="squad-page" aria-labelledby="squad-list-title">
    <div class="wire-frame page-frame squad-frame">
      <PageHeader
        :eyebrow="t('squads.list.eyebrow')"
        :title="t('squads.list.title')"
        :description="t('squads.list.subtitle')"
        title-id="squad-list-title"
      >
        <template #meta>
          <span class="summary-pill">{{ t('squads.list.activeCount', { count: activeSquads.length }) }}</span>
          <span v-if="mySquads.length" class="summary-pill">{{ t('squads.list.myCount', { count: mySquads.length }) }}</span>
          <span v-if="managedSquads.length" class="summary-pill">{{ t('squads.list.managedCount', { count: managedSquads.length }) }}</span>
        </template>
        <template #actions>
          <RouterLink class="button-box" to="/profile/squads">{{ t('common.mySquads') }}</RouterLink>
          <RouterLink class="button-box" to="/calendar">{{ t('squads.list.openCalendar') }}</RouterLink>
          <RouterLink v-if="canManageFleet" class="button-box primary-action" to="/squads/new">
            {{ t('squads.list.newSquad') }}
          </RouterLink>
        </template>
      </PageHeader>

      <section class="wire-section squad-intro-panel">
        <div>
          <p class="eyebrow">{{ t('squads.list.structureEyebrow') }}</p>
          <h2>{{ t('squads.list.structureTitle') }}</h2>
          <p>{{ t('squads.list.structureText') }}</p>
        </div>
        <label v-if="canManageFleet" class="toggle-card squad-archive-toggle">
          <span>
            <strong>{{ t('squads.list.showArchived') }}</strong>
            <small>{{ t('squads.list.showArchivedHint') }}</small>
          </span>
          <input v-model="includeInactive" type="checkbox" />
        </label>
      </section>

      <p v-if="loading" class="wire-section muted table-state">{{ t('squads.list.loading') }}</p>
      <p v-else-if="error" class="wire-section error-text table-state">{{ error }}</p>
      <div v-else-if="squads.length === 0" class="wire-section empty-state">
        <h2>{{ t('squads.list.emptyTitle') }}</h2>
        <p>{{ t('squads.list.emptyText') }}</p>
      </div>

      <section v-else class="squad-card-grid" :aria-label="t('squads.list.title')">
        <article
          v-for="squad in squads"
          :key="squad.id"
          class="wire-section squad-card"
          :class="{ 'is-archived': !squad.is_active, 'is-member': squad.is_member }"
        >
          <div class="squad-card-heading">
            <span class="squad-mark"><AppIcon name="users" :size="22" /></span>
            <div>
              <p class="eyebrow">{{ squad.is_active ? t('squads.status.active') : t('squads.status.archived') }}</p>
              <h2>{{ squad.name }}</h2>
            </div>
          </div>

          <p class="squad-card-description">{{ squad.description || t('squads.list.noDescription') }}</p>

          <dl class="squad-card-metrics">
            <div>
              <dt>{{ t('squads.fields.leader') }}</dt>
              <dd>{{ squad.leader?.display_name || t('squads.list.noLeader') }}</dd>
            </div>
            <div>
              <dt>{{ t('squads.fields.focus') }}</dt>
              <dd>{{ squad.focus || t('squads.list.noFocus') }}</dd>
            </div>
            <div>
              <dt>{{ t('squads.fields.members') }}</dt>
              <dd>{{ squad.max_members ? `${squad.member_count}/${squad.max_members}` : squad.member_count }}</dd>
            </div>
          </dl>

          <div class="squad-card-flags">
            <span v-if="squad.is_member" class="type-pill">
              {{ squad.current_user_role ? t(`squads.roles.${squad.current_user_role}`) : t('squads.list.memberBadge') }}
            </span>
            <span v-if="squad.can_manage" class="type-pill event-training">{{ t('squads.list.commandBadge') }}</span>
          </div>

          <div class="squad-card-actions">
            <RouterLink class="small-action" :to="`/squads/${squad.id}`">
              {{ squad.can_manage ? t('squads.list.manage') : t('squads.list.open') }}
            </RouterLink>
            <RouterLink
              v-if="squad.is_member || squad.can_manage"
              class="small-action"
              :to="{ path: '/calendar', query: { squad: squad.id } }"
            >
              {{ t('squads.list.calendar') }}
            </RouterLink>
          </div>
        </article>
      </section>
    </div>
  </section>
</template>
