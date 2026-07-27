<script setup>
import LocalDateTimeFields from '@/shared/components/LocalDateTimeFields.vue'
import { useGroupCreatePage } from '@/modules/groups/composables/useGroupCreatePage'

const {
  router,
  t,
  saving,
  error,
  focusOptions,
  rateOptions,
  form,
  rateRangeInvalid,
  scheduledStartAt,
  scheduledEndAt,
  scheduleHasAnyValue,
  scheduleIncomplete,
  timeRangeInvalid,
  submitGroup,
  localDateTimeValue,
  localDateFromInputs,
} = useGroupCreatePage()
</script>

<template>
  <section class="group-create-page" aria-labelledby="group-create-title">
    <form class="wire-frame page-frame create-frame create-frame-clean group-create-frame-clean" @submit.prevent="submitGroup">
      <div class="create-topline group-create-topline-clean">
        <RouterLink class="small-action" to="/groups">{{ t('common.back') }}</RouterLink>
        <div>
          <p class="eyebrow">{{ t('common.groups') }}</p>
          <h1 id="group-create-title">{{ t('groups.create.title') }}</h1>
          <p>{{ t('groups.create.subtitle') }}</p>
        </div>
      </div>

      <section class="wire-section form-section group-form-section" :aria-label="t('groups.create.sections.basics')">
        <div class="section-title">
          <span>01</span>
          <h2>{{ t('groups.create.sections.basics') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('groups.create.sections.basicsText') }}</p>

        <div class="section-fields group-basic-grid announcement-basic-grid">
          <label class="field-stack group-title-field">
            <span class="field-label">{{ t('groups.fields.title') }}</span>
            <span class="input-panel embedded-field">
              <input v-model="form.title" required maxlength="140" :placeholder="t('groups.create.titlePlaceholder')" />
            </span>
          </label>

          <label class="field-stack">
            <span class="field-label">{{ t('groups.fields.focus') }}</span>
            <span class="select-shell full-select-shell">
              <select v-model="form.focus">
                <option v-for="focus in focusOptions" :key="focus" :value="focus">{{ t(`focus.${focus}`) }}</option>
              </select>
            </span>
          </label>
        </div>
      </section>

      <section class="wire-section form-section group-form-section" :aria-label="t('groups.create.sections.requirements')">
        <div class="section-title">
          <span>02</span>
          <h2>{{ t('groups.create.sections.requirements') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('groups.create.sections.requirementsText') }}</p>

        <div class="section-fields group-requirement-grid announcement-requirement-grid">
          <label class="field-stack">
            <span class="field-label">{{ t('groups.fields.maxShipRate') }}</span>
            <span class="select-shell full-select-shell">
              <select v-model="form.max_ship_rate">
                <option value="">{{ t('groups.create.anyMaxRate') }}</option>
                <option v-for="rate in rateOptions" :key="`max-${rate}`" :value="rate">{{ rate }}</option>
              </select>
            </span>
          </label>

          <label class="field-stack">
            <span class="field-label">{{ t('groups.fields.minShipRate') }}</span>
            <span class="select-shell full-select-shell">
              <select v-model="form.min_ship_rate">
                <option value="">{{ t('groups.create.anyMinRate') }}</option>
                <option v-for="rate in rateOptions" :key="`min-${rate}`" :value="rate">{{ rate }}</option>
              </select>
            </span>
          </label>

          <label class="field-stack group-fleet-field">
            <span class="field-label">{{ t('groups.fields.fleetRestriction') }}</span>
            <span class="input-panel embedded-field">
              <input v-model="form.fleet_restriction" maxlength="120" :placeholder="t('groups.create.fleetPlaceholder')" />
            </span>
          </label>

          <label class="field-stack">
            <span class="field-label">{{ t('groups.fields.maxMembers') }}</span>
            <span class="input-panel embedded-field">
              <input v-model.number="form.max_members" type="number" min="2" max="50" />
            </span>
          </label>

          <label class="field-stack checkbox-field-stack">
            <span class="field-label">{{ t('groups.fields.allowGuests') }}</span>
            <span class="checkbox-card-control inline-checkbox-control">
              <input v-model="form.allow_guests" type="checkbox" />
              <strong>{{ t('groups.create.allowGuestsHint') }}</strong>
            </span>
          </label>
        </div>
      </section>

      <section class="wire-section form-section group-form-section" :aria-label="t('groups.create.sections.schedule')">
        <div class="section-title">
          <span>03</span>
          <h2>{{ t('groups.create.sections.schedule') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('groups.create.sections.scheduleText') }}</p>

        <div class="section-fields group-time-grid">
          <LocalDateTimeFields
            v-model:date="form.scheduled_start_date"
            v-model:time="form.scheduled_start_time"
            :date-label="t('calendar.fields.startDate')"
            :time-label="t('groups.fields.startTime')"
          />
          <LocalDateTimeFields
            v-model:date="form.scheduled_end_date"
            v-model:time="form.scheduled_end_time"
            :date-label="t('calendar.fields.endDate')"
            :time-label="t('groups.fields.endTime')"
          />
        </div>
      </section>

      <section class="wire-section form-section group-form-section" :aria-label="t('groups.create.sections.details')">
        <div class="section-title">
          <span>04</span>
          <h2>{{ t('groups.create.sections.details') }}</h2>
        </div>
        <p class="section-helper-text">{{ t('groups.create.sections.detailsText') }}</p>

        <div class="announcement-copy-grid">
          <label class="field-stack details-field">
            <span class="field-label">{{ t('groups.fields.description') }}</span>
            <span class="input-panel embedded-field textarea-shell">
              <textarea v-model="form.description" rows="5" maxlength="2000" :placeholder="t('groups.create.descriptionPlaceholder')"></textarea>
            </span>
          </label>

          <label class="field-stack details-field">
            <span class="field-label">{{ t('groups.fields.expectations') }}</span>
            <span class="input-panel embedded-field textarea-shell">
              <textarea v-model="form.expectations" rows="5" maxlength="2000" :placeholder="t('groups.create.expectationsPlaceholder')"></textarea>
            </span>
          </label>

          <label class="field-stack details-field">
            <span class="field-label">{{ t('groups.fields.activityPlan') }}</span>
            <span class="input-panel embedded-field textarea-shell">
              <textarea v-model="form.activity_plan" rows="5" maxlength="2000" :placeholder="t('groups.create.activityPlanPlaceholder')"></textarea>
            </span>
          </label>

          <label class="field-stack details-field">
            <span class="field-label">{{ t('groups.fields.contactNote') }}</span>
            <span class="input-panel embedded-field textarea-shell">
              <textarea v-model="form.contact_note" rows="3" maxlength="300" :placeholder="t('groups.create.contactPlaceholder')"></textarea>
            </span>
          </label>
        </div>
      </section>

      <p v-if="rateRangeInvalid" class="error-text form-message">{{ t('groups.create.rateRangeInvalid') }}</p>
      <p v-if="scheduleIncomplete" class="error-text form-message">{{ t('groups.create.scheduleIncomplete') }}</p>
      <p v-if="timeRangeInvalid" class="error-text form-message">{{ t('groups.create.timeRangeInvalid') }}</p>
      <p v-if="error" class="error-text form-message">{{ error }}</p>
      <div class="form-actions group-create-actions">
        <button class="wire-section form-button primary" type="submit" :disabled="saving || rateRangeInvalid || scheduleIncomplete || timeRangeInvalid">
          {{ saving ? t('groups.create.saving') : t('groups.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
