<script setup>
import { computed, onMounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { closeGroup, getGroup } from '@/services/groups'
import { useSession } from '@/services/session'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})

const { t } = useLocale()
const { isStaff, user } = useSession()

const group = ref(null)
const loading = ref(false)
const closing = ref(false)
const error = ref('')

const canManage = computed(() => group.value && user.value && (group.value.owner_id === user.value.id || isStaff.value))

const rateRequirementText = computed(() => {
  if (!group.value) return t('groups.detail.anyRate')
  const minRate = group.value.min_ship_rate
  const maxRate = group.value.max_ship_rate
  if (minRate && maxRate) return t('groups.detail.rateRangeRequirement', { max: maxRate, min: minRate })
  if (minRate) return t('groups.detail.minRateRequirement', { rate: minRate })
  if (maxRate) return t('groups.detail.maxRateRequirement', { rate: maxRate })
  return t('groups.detail.anyRate')
})

async function loadGroup() {
  loading.value = true
  error.value = ''
  try {
    group.value = await getGroup(props.id)
  } catch (err) {
    error.value = err.message || t('groups.detail.loadError')
  } finally {
    loading.value = false
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

onMounted(loadGroup)
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
                <h2>{{ t('groups.fields.description') }}</h2>
              </div>
              <span class="summary-pill">{{ t('groups.list.announcementMode') }}</span>
            </div>
            <p>{{ group.description || t('groups.detail.noDescription') }}</p>
          </section>

          <aside class="wire-section group-join-panel announcement-mode-panel">
            <p class="eyebrow">{{ t('groups.detail.joinClosedEyebrow') }}</p>
            <h2>{{ t('groups.detail.joinClosedTitle') }}</h2>
            <p>{{ t('groups.detail.joinClosedText') }}</p>

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
