<script setup>
import LocalDateTimeFields from '@/shared/components/LocalDateTimeFields.vue'
import { useCalendarCreatePage } from '@/modules/calendar/composables/useCalendarCreatePage'

const {
  route,
  router,
  t,
  canManageFleet,
  now,
  later,
  squads,
  loadingScopes,
  saving,
  error,
  form,
  managedSquads,
  scopeOptions,
  canCreate,
  categoryOptions,
  startAt,
  endAt,
  dateRangeInvalid,
  loadScopes,
  submitEvent,
  dateInputValue,
  localDateFromInputs,
  timeInputValue,
} = useCalendarCreatePage()
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
