<script setup>
import { useRegisterPage } from '@/modules/accounts/composables/useRegisterPage'

const {
  t,
  register,
  username,
  displayName,
  password,
  wantsFleetMembership,
  fleetApplicationNote,
  officialFleet,
  fleetLoading,
  fleetError,
  isSubmitting,
  error,
  success,
  submittedRequest,
  loadOfficialFleet,
  submitRegister,
} = useRegisterPage()
</script>

<template>
  <section class="auth-page" aria-labelledby="register-title">
    <div class="wire-frame page-frame auth-frame register-frame">
      <section class="wire-section auth-card refined-auth-card register-card">
        <div class="auth-copy register-copy">
          <p class="eyebrow">{{ t('auth.registerEyebrow') }}</p>
          <h1 id="register-title">{{ t('auth.registerTitle') }}</h1>
          <p>{{ t('auth.registerSubtitle') }}</p>

          <div class="register-benefits" :aria-label="t('auth.registerBenefitsLabel')">
            <span>{{ t('auth.registerBenefit.profile') }}</span>
            <span>{{ t('auth.registerBenefit.fleet') }}</span>
            <span>{{ t('auth.registerBenefit.tools') }}</span>
          </div>
        </div>

        <form class="auth-form register-form" @submit.prevent="submitRegister">
          <section class="register-form-section" aria-labelledby="register-account-heading">
            <div class="form-section-heading compact-form-heading">
              <span class="step-marker">01</span>
              <div>
                <h2 id="register-account-heading">{{ t('auth.registerStepAccount') }}</h2>
                <p>{{ t('auth.registerStepAccountHint') }}</p>
              </div>
            </div>

            <label class="input-panel elevated-input-panel">
              <span>{{ t('auth.username') }}</span>
              <input v-model="username" type="text" autocomplete="username" required minlength="3" maxlength="80" :placeholder="t('auth.usernamePlaceholder')" />
              <small>{{ t('auth.usernameHint') }}</small>
            </label>

            <label class="input-panel elevated-input-panel">
              <span>{{ t('profile.displayName') }}</span>
              <input v-model="displayName" type="text" autocomplete="nickname" required maxlength="120" :placeholder="t('auth.displayNamePlaceholder')" />
              <small>{{ t('auth.displayNameHint') }}</small>
            </label>

            <label class="input-panel elevated-input-panel">
              <span>{{ t('auth.password') }}</span>
              <input v-model="password" type="password" autocomplete="new-password" required minlength="12" :placeholder="t('auth.passwordPlaceholder')" />
              <small>{{ t('auth.passwordHint') }}</small>
            </label>
          </section>

          <section class="register-form-section fleet-registration-option" aria-labelledby="register-fleet-heading">
            <div class="form-section-heading compact-form-heading">
              <span class="step-marker">02</span>
              <div>
                <h2 id="register-fleet-heading">{{ t('auth.registerStepFleet') }}</h2>
                <p>{{ t('auth.registerStepFleetHint') }}</p>
              </div>
            </div>

            <p v-if="fleetLoading" class="muted">{{ t('auth.registerFleetLoading') }}</p>
            <div v-else-if="officialFleet" class="fleet-registration-card">
              <div>
                <small>{{ t('auth.fleetChoice') }}</small>
                <strong>{{ officialFleet.name }}</strong>
              </div>
              <label class="fleet-registration-toggle">
                <input v-model="wantsFleetMembership" type="checkbox" />
                <span>
                  <strong>{{ t('auth.joinOfficialFleet') }}</strong>
                  <small>{{ t('auth.joinOfficialFleetExistingMemberHint') }}</small>
                </span>
              </label>

              <label v-if="wantsFleetMembership" class="input-panel elevated-input-panel">
                <span>{{ t('auth.fleetApplicationNote') }}</span>
                <textarea v-model="fleetApplicationNote" rows="4" maxlength="1000" :placeholder="t('auth.fleetApplicationNotePlaceholder')"></textarea>
                <small>{{ t('auth.fleetApplicationNoteHint') }}</small>
              </label>
            </div>
            <div v-else class="fleet-registration-unavailable">
              <p class="error-text">{{ fleetError || t('auth.registerFleetUnavailable') }}</p>
              <button class="small-action" type="button" :disabled="fleetLoading" @click="loadOfficialFleet">{{ t('auth.registerFleetRetry') }}</button>
            </div>
          </section>

          <p v-if="error" class="error-text">{{ error }}</p>
          <div v-if="success" class="success-panel registration-review-panel">
            <strong>{{ t('auth.registerPendingTitle') }}</strong>
            <p>{{ submittedRequest?.wants_fleet_membership ? t('auth.registerSuccessWithFleet') : t('auth.registerSuccess') }}</p>
            <small v-if="submittedRequest">{{ t('auth.registerRequestId', { id: submittedRequest.id }) }}</small>
          </div>

          <button class="form-button primary-action register-submit" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? t('auth.creatingAccount') : t('auth.createAccount') }}
          </button>

          <p class="muted auth-hint">
            {{ t('auth.alreadyAccount') }}
            <RouterLink to="/login">{{ t('auth.login') }}</RouterLink>
          </p>
        </form>
      </section>
    </div>
  </section>
</template>
