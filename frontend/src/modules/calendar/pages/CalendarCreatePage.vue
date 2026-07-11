<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useLocale } from '@/locales'
import LocalDateTimeFields from '@/shared/components/LocalDateTimeFields.vue'
import { dateInputValue, localDateFromInputs, timeInputValue } from '@/shared/datetime/localDateTime'
import { createFleetEvent, FLEET_EVENT_CATEGORIES } from '@/modules/calendar/api/calendar'
import { useSession } from '@/modules/accounts/session'
import { listSquads } from '@/modules/squads/api/squads'

const route = useRoute()
const router = useRouter()
const { t } = useLocale()
const { canManageFleet } = useSession()

const now = new Date()
now.setMinutes(0, 0, 0)
const later = new Date(now)
later.setHours(now.getHours() + 2)

const squads = ref([])
const loadingScopes = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive({
  title: '',
  category: 'training',
  scope: route.query.squad ? `squad:${route.query.squad}` : '',
  location: '',
  startDate: dateInputValue(now),
  startTime: timeInputValue(now),
  endDate: dateInputValue(later),
  endTime: timeInputValue(later),
  allDay: false,
  description: '',
})

const managedSquads = computed(() => squads.value.filter((squad) => squad.can_manage && squad.is_active))
const scopeOptions = computed(() => {
  const options = []
  if (canManageFleet.value) options.push({ value: 'fleet', label: t('calendar.scopes.fleetWide') })
  options.push(...managedSquads.value.map((squad) => ({ value: `squad:${squad.id}`, label: squad.name })))
  return options
})
const canCreate = computed(() => scopeOptions.value.length > 0)

const categoryOptions = computed(() =>
  FLEET_EVENT_CATEGORIES.map((value) => ({ value, label: t(`calendar.categories.${value}`) })),
)

const startAt = computed(() => localDateFromInputs(form.startDate, form.allDay ? '00:00' : form.startTime))
const endAt = computed(() => {
  const date = localDateFromInputs(form.endDate, form.allDay ? '00:00' : form.endTime)
  if (date && form.allDay) date.setDate(date.getDate() + 1)
  return date
})
const dateRangeInvalid = computed(() => !startAt.value || !endAt.value || endAt.value <= startAt.value)

async function loadScopes() {
  loadingScopes.value = true
  error.value = ''
  try {
    squads.value = await listSquads()
    const values = new Set(scopeOptions.value.map((option) => option.value))
    if (!values.has(form.scope)) form.scope = scopeOptions.value[0]?.value || ''
  } catch (err) {
    error.value = err.message || t('calendar.create.scopeLoadError')
  } finally {
    loadingScopes.value = false
  }
}

async function submitEvent() {
  error.value = ''
  if (dateRangeInvalid.value) {
    error.value = t('calendar.create.dateRangeInvalid')
    return
  }
  if (!form.scope) {
    error.value = t('calendar.create.noScopeError')
    return
  }

  saving.value = true
  try {
    const squadId = form.scope.startsWith('squad:') ? Number(form.scope.split(':')[1]) : null
    await createFleetEvent({
      title: form.title,
      category: form.category,
      location: form.location || null,
      description: form.description || null,
      start_at: startAt.value.toISOString(),
      end_at: endAt.value.toISOString(),
      all_day: form.allDay,
      squad_id: squadId,
    })
    router.push(squadId ? { path: '/calendar', query: { squad: squadId } } : '/calendar')
  } catch (err) {
    error.value = err.message || t('calendar.create.saveError')
  } finally {
    saving.value = false
  }
}

onMounted(loadScopes)
</script>

<template>
  <section class="calendar-create-page" aria-labelledby="calendar-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean calendar-create-frame" @submit.prevent="submitEvent">
      <div class="create-topline calendar-create-topline">
        <RouterLink class="small-action" to="/calendar">{{ t('common.back') }}</RouterLink>
        <div>
          <p class="eyebrow">{{ t('common.calendar') }}</p>
          <h1 id="calendar-create-title">{{ t('calendar.create.title') }}</h1>
          <p>{{ t('calendar.create.subtitle') }}</p>
        </div>
      </div>

      <div v-if="!loadingScopes && !canCreate" class="wire-section empty-state">
        <h2>{{ t('calendar.create.noPermissionTitle') }}</h2>
        <p>{{ t('calendar.create.noPermissionText') }}</p>
        <RouterLink class="button-box" to="/squads">{{ t('calendar.create.openSquads') }}</RouterLink>
      </div>

      <template v-else>
        <section class="wire-section form-section calendar-form-section" :aria-label="t('calendar.create.sections.basics')">
          <div class="section-title">
            <span>01</span>
            <h2>{{ t('calendar.create.sections.basics') }}</h2>
          </div>
          <p class="section-helper-text">{{ t('calendar.create.sections.basicsText') }}</p>

          <div class="section-fields calendar-basic-grid">
            <label class="field-stack calendar-title-field">
              <span class="field-label">{{ t('calendar.fields.title') }}</span>
              <span class="input-panel embedded-field">
                <input v-model="form.title" required maxlength="160" :placeholder="t('calendar.create.titlePlaceholder')" />
              </span>
            </label>

            <label class="field-stack">
              <span class="field-label">{{ t('calendar.fields.scope') }}</span>
              <span class="select-shell full-select-shell">
                <select v-model="form.scope" required :disabled="loadingScopes">
                  <option value="">{{ loadingScopes ? t('calendar.create.loadingScopes') : t('calendar.create.selectScope') }}</option>
                  <option v-for="option in scopeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </span>
            </label>

            <label class="field-stack">
              <span class="field-label">{{ t('calendar.fields.category') }}</span>
              <span class="select-shell full-select-shell">
                <select v-model="form.category">
                  <option v-for="option in categoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </span>
            </label>

            <label class="field-stack calendar-location-field">
              <span class="field-label">{{ t('calendar.fields.location') }}</span>
              <span class="input-panel embedded-field">
                <input v-model="form.location" maxlength="200" :placeholder="t('calendar.create.locationPlaceholder')" />
              </span>
            </label>
          </div>
        </section>

        <section class="wire-section form-section calendar-form-section" :aria-label="t('calendar.create.sections.time')">
          <div class="section-title">
            <span>02</span>
            <h2>{{ t('calendar.create.sections.time') }}</h2>
          </div>
          <p class="section-helper-text">{{ t('calendar.create.sections.timeText') }}</p>

          <div class="section-fields calendar-time-grid">
            <label class="toggle-card calendar-all-day-toggle">
              <span>
                <strong>{{ t('calendar.fields.allDay') }}</strong>
                <small>{{ t('calendar.create.allDayHint') }}</small>
              </span>
              <input v-model="form.allDay" type="checkbox" />
            </label>

            <LocalDateTimeFields
              v-model:date="form.startDate"
              v-model:time="form.startTime"
              :date-label="t('calendar.fields.startDate')"
              :time-label="t('calendar.fields.startTime')"
              date-required
              :time-required="!form.allDay"
              :show-time="!form.allDay"
            />
            <LocalDateTimeFields
              v-model:date="form.endDate"
              v-model:time="form.endTime"
              :date-label="t('calendar.fields.endDate')"
              :time-label="t('calendar.fields.endTime')"
              date-required
              :time-required="!form.allDay"
              :show-time="!form.allDay"
            />
          </div>
        </section>

        <section class="wire-section form-section calendar-form-section" :aria-label="t('calendar.create.sections.details')">
          <div class="section-title">
            <span>03</span>
            <h2>{{ t('calendar.create.sections.details') }}</h2>
          </div>
          <p class="section-helper-text">{{ t('calendar.create.sections.detailsText') }}</p>
          <label class="field-stack">
            <span class="field-label">{{ t('calendar.fields.description') }}</span>
            <span class="input-panel embedded-field textarea-shell">
              <textarea v-model="form.description" rows="7" maxlength="3000" :placeholder="t('calendar.create.descriptionPlaceholder')"></textarea>
            </span>
          </label>
        </section>

        <p v-if="dateRangeInvalid" class="error-text form-message">{{ t('calendar.create.dateRangeInvalid') }}</p>
        <p v-if="error" class="error-text form-message">{{ error }}</p>
        <div class="form-actions calendar-create-actions">
          <button class="wire-section form-button primary" type="submit" :disabled="saving || dateRangeInvalid || loadingScopes || !form.scope">
            {{ saving ? t('calendar.create.saving') : t('calendar.create.save') }}
          </button>
        </div>
      </template>
    </form>
  </section>
</template>
