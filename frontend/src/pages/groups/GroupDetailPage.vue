<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { closeGroup, getGroup, joinGroup } from '@/services/groups'
import { useSession } from '@/services/session'
import { listShips } from '@/services/ships'

const props = defineProps({ id: { type: [String, Number], required: true } })

const { t } = useLocale()
const { isAuthenticated, isStaff, user } = useSession()

const group = ref(null)
const ships = ref([])
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
  note: '',
})

const selectedShip = computed(() => ships.value.find((ship) => ship.id === Number(joinForm.ship_id)) || null)
const minShipRate = computed(() => Number(group.value?.min_ship_rate || 0))
const maxShipRate = computed(() => Number(group.value?.max_ship_rate || 0))
const shipRequiredForJoin = computed(() => minShipRate.value > 0 || maxShipRate.value > 0)
const selectedShipMeetsRate = computed(() => {
  if (!shipRequiredForJoin.value) return true
  if (!selectedShip.value) return false
  if (minShipRate.value && selectedShip.value.rate > minShipRate.value) return false
  if (maxShipRate.value && selectedShip.value.rate < maxShipRate.value) return false
  return true
})
const rateRequirementText = computed(() => {
  if (minShipRate.value && maxShipRate.value) return t('groups.detail.rateRangeRequirement', { max: maxShipRate.value, min: minShipRate.value })
  if (minShipRate.value) return t('groups.detail.minRateRequirement', { rate: minShipRate.value })
  if (maxShipRate.value) return t('groups.detail.maxRateRequirement', { rate: maxShipRate.value })
  return t('groups.detail.anyRate')
})
const joinRateMessage = computed(() => {
  if (!shipRequiredForJoin.value) return ''
  if (!selectedShip.value) return t('groups.detail.rateRequired', { requirement: rateRequirementText.value })
  if (!selectedShipMeetsRate.value) return t('groups.detail.rateTooLow', { requirement: rateRequirementText.value })
  return t('groups.detail.rateOk', { rate: selectedShip.value.rate })
})
const joinSubmitDisabled = computed(() => joining.value || !joinForm.display_name.trim() || !selectedShipMeetsRate.value)
const canManage = computed(() => group.value && user.value && (group.value.owner_id === user.value.id || isStaff.value))
const canJoin = computed(() => Boolean(group.value?.is_joinable))
const activeMembers = computed(() => group.value?.members?.filter((member) => member.is_active) || [])

const eligibleShips = computed(() => {
  const minRate = minShipRate.value
  return ships.value.map((ship) => ({
    ...ship,
    isEligible: (!minRate || ship.rate <= minRate) && (!maxShipRate.value || ship.rate >= maxShipRate.value),
    label: `${ship.name} · ${t('common.rate')} ${ship.rate}`,
  }))
})

function memberShipLabel(member) {
  if (member.ship?.name) return `${member.ship.name} · ${t('common.rate')} ${member.ship.rate}`
  if (member.ship_name) return member.ship_rate ? `${member.ship_name} · ${t('common.rate')} ${member.ship_rate}` : member.ship_name
  return t('groups.detail.noShip')
}

async function loadGroup() {
  loading.value = true
  error.value = ''
  try {
    group.value = await getGroup(props.id)
    if (isAuthenticated.value && user.value) {
      joinForm.display_name = user.value.display_name || ''
      joinForm.fleet_name = user.value.fleet_name || ''
    }
  } catch (err) {
    error.value = err.message || t('groups.detail.loadError')
  } finally {
    loading.value = false
  }
}

async function loadShips() {
  try {
    ships.value = await listShips()
  } catch {
    ships.value = []
  }
}

async function submitJoin() {
  joinError.value = ''
  joinSuccess.value = ''

  if (shipRequiredForJoin.value && !selectedShip.value) {
    joinError.value = t('groups.detail.rateRequired', { requirement: rateRequirementText.value })
    return
  }

  if (!selectedShipMeetsRate.value) {
    joinError.value = t('groups.detail.rateTooLow', { requirement: rateRequirementText.value })
    return
  }

  joining.value = true
  try {
    group.value = await joinGroup(group.value.id, {
      display_name: joinForm.display_name,
      fleet_name: joinForm.fleet_name || null,
      ship_id: joinForm.ship_id ? Number(joinForm.ship_id) : null,
      ship_name: selectedShip.value?.name || null,
      ship_rate: selectedShip.value?.rate || null,
      note: joinForm.note || null,
    })
    joinSuccess.value = t('groups.detail.joined')
    joinForm.note = ''
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

onMounted(async () => {
  await Promise.all([loadGroup(), loadShips()])
})
</script>

<template>
  <section class="group-detail-page" aria-labelledby="group-detail-title">
    <div class="wire-frame page-frame detail-frame group-detail-frame">
      <header class="wire-section detail-header group-detail-header">
        <RouterLink class="small-action" to="/groups">{{ t('common.back') }}</RouterLink>
        <div v-if="group">
          <p class="eyebrow">{{ t(`focus.${group.focus}`) }}</p>
          <h1 id="group-detail-title">{{ group.title }}</h1>
          <p>{{ group.description || t('groups.detail.noDescription') }}</p>
        </div>
      </header>

      <p v-if="loading" class="wire-section muted">{{ t('groups.detail.loading') }}</p>
      <p v-else-if="error" class="wire-section error-text">{{ error }}</p>

      <template v-else-if="group">
        <section class="wire-section group-overview-grid">
          <div class="group-stat-card">
            <span>{{ t('groups.fields.status') }}</span>
            <strong>{{ t(`groups.status.${group.status}`) }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.members') }}</span>
            <strong>{{ group.active_members_count }} / {{ group.max_members }}</strong>
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
            <span>{{ t('groups.fields.guests') }}</span>
            <strong>{{ group.allow_guests ? t('groups.detail.guestsYes') : t('groups.detail.guestsNo') }}</strong>
          </div>
          <div class="group-stat-card">
            <span>{{ t('groups.fields.fleetRestriction') }}</span>
            <strong>{{ group.fleet_restriction || t('groups.list.noFleetRestriction') }}</strong>
          </div>
        </section>

        <section class="group-detail-grid">
          <section class="wire-section group-members-panel">
            <div class="section-heading-row">
              <div>
                <p class="eyebrow">{{ t('groups.detail.membersEyebrow') }}</p>
                <h2>{{ t('groups.detail.membersTitle') }}</h2>
              </div>
              <span class="summary-pill">{{ group.spots_left }} {{ t('groups.detail.spotsLeft') }}</span>
            </div>

            <p v-if="activeMembers.length === 0" class="muted table-state">{{ t('groups.detail.noMembers') }}</p>
            <div v-else class="member-list">
              <article v-for="member in activeMembers" :key="member.id" class="member-row">
                <div>
                  <strong>{{ member.display_name }}</strong>
                  <span>{{ member.fleet_name || t('groups.detail.noFleet') }} · {{ memberShipLabel(member) }}</span>
                </div>
                <span class="type-pill">{{ member.is_guest ? t('groups.detail.guest') : t('groups.detail.member') }}</span>
              </article>
            </div>
          </section>

          <aside class="wire-section group-join-panel">
            <template v-if="canJoin">
              <p class="eyebrow">{{ t('groups.detail.joinEyebrow') }}</p>
              <h2>{{ t('groups.detail.joinTitle') }}</h2>
              <p>{{ shipRequiredForJoin ? t('groups.detail.joinTextWithRate', { requirement: rateRequirementText }) : t('groups.detail.joinText') }}</p>

              <form class="group-join-form" @submit.prevent="submitJoin">
                <label class="field-stack">
                  <span class="field-label">{{ t('groups.fields.displayName') }}</span>
                  <span class="input-panel embedded-field">
                    <input v-model="joinForm.display_name" required maxlength="120" />
                  </span>
                </label>
                <label class="field-stack">
                  <span class="field-label">{{ t('groups.fields.fleetName') }}</span>
                  <span class="input-panel embedded-field">
                    <input v-model="joinForm.fleet_name" maxlength="120" />
                  </span>
                </label>
                <label class="field-stack">
                  <span class="field-label">{{ t('groups.fields.ship') }}</span>
                  <span class="select-shell full-select-shell">
                    <select v-model="joinForm.ship_id" :required="shipRequiredForJoin">
                      <option value="" :disabled="shipRequiredForJoin">
                        {{ shipRequiredForJoin ? t('groups.detail.selectRequiredShip', { requirement: rateRequirementText }) : t('groups.detail.noShipSelection') }}
                      </option>
                      <option v-for="ship in eligibleShips" :key="ship.id" :value="ship.id" :disabled="!ship.isEligible">
                        {{ ship.label }}{{ !ship.isEligible ? ` · ${t('groups.detail.rateLocked', { requirement: rateRequirementText })}` : '' }}
                      </option>
                    </select>
                  </span>
                </label>
                <p v-if="shipRequiredForJoin" class="rate-check-message" :class="{ 'is-ok': selectedShipMeetsRate && selectedShip }">
                  {{ joinRateMessage }}
                </p>
                <label class="field-stack details-field">
                  <span class="field-label">{{ t('groups.fields.note') }}</span>
                  <span class="input-panel embedded-field textarea-shell">
                    <textarea v-model="joinForm.note" rows="4" maxlength="1000"></textarea>
                  </span>
                </label>

                <p v-if="joinError" class="error-text profile-message">{{ joinError }}</p>
                <p v-if="joinSuccess" class="success-text profile-message">{{ joinSuccess }}</p>

                <button class="form-button primary" type="submit" :disabled="joinSubmitDisabled">
                  {{ joining ? t('groups.detail.joining') : t('groups.detail.join') }}
                </button>
              </form>
            </template>

            <template v-else>
              <p class="eyebrow">{{ t('groups.detail.joinClosedEyebrow') }}</p>
              <h2>{{ t('groups.detail.joinClosedTitle') }}</h2>
              <p>{{ t('groups.detail.joinClosedText') }}</p>
            </template>

            <div v-if="canManage" class="group-management-actions">
              <button class="danger-action" type="button" :disabled="closing || group.status === 'closed'" @click="submitClose">
                {{ closing ? t('groups.detail.closing') : t('groups.detail.close') }}
              </button>
            </div>
          </aside>
        </section>
      </template>
    </div>
  </section>
</template>
