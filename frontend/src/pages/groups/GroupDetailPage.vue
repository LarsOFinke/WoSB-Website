<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { useLocale } from '@/locales'
import { listMyBuilds } from '@/services/builds'
import { closeGroup, getGroup, joinGroup } from '@/services/groups'
import { listShips } from '@/services/ships'
import { useSession } from '@/services/session'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const { t } = useLocale()
const { isAuthenticated, isStaff, user } = useSession()

const group = ref(null)
const ships = ref([])
const builds = ref([])
const loading = ref(false)
const joining = ref(false)
const closing = ref(false)
const error = ref('')
const joinError = ref('')
const joinSuccess = ref('')

const joinForm = reactive({
  display_name: '',
  fleet_name: '',
  ship_id: '',
  build_id: '',
  note: '',
})

const canManage = computed(() => group.value && user.value && (group.value.owner_id === user.value.id || isStaff.value))
const canJoin = computed(() => Boolean(group.value?.is_joinable))
const selectedBuild = computed(() => builds.value.find((build) => String(build.id) === String(joinForm.build_id)) || null)
const selectedShip = computed(() => {
  if (selectedBuild.value) return selectedBuild.value.ship
  return ships.value.find((ship) => String(ship.id) === String(joinForm.ship_id)) || null
})

const allowedShips = computed(() => ships.value.filter((ship) => isShipAllowed(ship.rate)))
const allowedBuilds = computed(() => builds.value.filter((build) => isShipAllowed(build.ship?.rate)))

const rateRequirementText = computed(() => {
  if (!group.value) return t('groups.detail.anyRate')
  const minRate = group.value.min_ship_rate
  const maxRate = group.value.max_ship_rate
  if (minRate && maxRate) return t('groups.detail.rateRangeRequirement', { max: maxRate, min: minRate })
  if (minRate) return t('groups.detail.minRateRequirement', { rate: minRate })
  if (maxRate) return t('groups.detail.maxRateRequirement', { rate: maxRate })
  return t('groups.detail.anyRate')
})

const scheduleText = computed(() => {
  if (!group.value?.scheduled_start_at) return t('groups.detail.noSchedule')
  const start = formatDateTime(group.value.scheduled_start_at)
  const end = group.value.scheduled_end_at ? formatDateTime(group.value.scheduled_end_at) : null
  return end ? `${start} – ${end}` : start
})

function formatDateTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function isShipAllowed(rate) {
  if (!group.value || !rate) return !group.value?.min_ship_rate && !group.value?.max_ship_rate
  if (group.value.min_ship_rate && rate > group.value.min_ship_rate) return false
  if (group.value.max_ship_rate && rate < group.value.max_ship_rate) return false
  return true
}

function memberShipLabel(member) {
  if (member.build) return `${member.build.build_name} · ${member.build.ship.name}`
  if (member.ship) return `${member.ship.name} · ${t('common.rate')} ${member.ship.rate}`
  return member.ship_name || t('groups.detail.noShip')
}

async function loadAuxiliaryData() {
  try {
    ships.value = await listShips()
  } catch {
    ships.value = []
  }
  if (!isAuthenticated.value) {
    builds.value = []
    return
  }
  try {
    builds.value = await listMyBuilds()
  } catch {
    builds.value = []
  }
}

async function loadGroup() {
  loading.value = true
  error.value = ''
  try {
    group.value = await getGroup(props.id)
    if (!joinForm.display_name && user.value) joinForm.display_name = user.value.display_name || user.value.username || ''
  } catch (err) {
    error.value = err.message || t('groups.detail.loadError')
  } finally {
    loading.value = false
  }
}

async function submitJoin() {
  joining.value = true
  joinError.value = ''
  joinSuccess.value = ''
  try {
    await joinGroup(group.value.id, {
      display_name: joinForm.display_name || user.value?.display_name || user.value?.username || '',
      fleet_name: joinForm.fleet_name || null,
      ship_id: joinForm.build_id ? null : (joinForm.ship_id ? Number(joinForm.ship_id) : null),
      build_id: joinForm.build_id ? Number(joinForm.build_id) : null,
      ship_name: selectedShip.value?.name || null,
      ship_rate: selectedShip.value?.rate || null,
      note: joinForm.note || null,
    })
    joinSuccess.value = t('groups.detail.joined')
    joinForm.note = ''
    await loadGroup()
  } catch (err) {
    joinError.value = err.message || t('groups.detail.joinError')
  } finally {
    joining.value = false
  }
}

async function submitClose() {
  closing.value = true
  error.value = ''
  try {
    await closeGroup(group.value.id)
    await loadGroup()
  } catch (err) {
    error.value = err.message || t('groups.detail.closeError')
  } finally {
    closing.value = false
  }
}

watch(() => joinForm.build_id, (value) => {
  if (value) joinForm.ship_id = ''
})

watch(() => joinForm.ship_id, (value) => {
  if (value) joinForm.build_id = ''
})

onMounted(async () => {
  await Promise.all([loadGroup(), loadAuxiliaryData()])
})
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
