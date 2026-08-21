<script setup>
import { computed, onMounted } from 'vue'

import { useLocale } from '@/locales'
import { useCookieConsent } from '@/modules/privacy/composables/useCookieConsent'

const { t } = useLocale()
const {
  state,
  initialize,
  acceptAll,
  rejectOptional,
  saveCustom,
  toggleSettings,
} = useCookieConsent()

const disabled = computed(() => state.loading || state.saving)

onMounted(initialize)
</script>

<template>
  <Teleport to="body">
    <section
      v-if="state.visible"
      class="cookie-consent"
      role="dialog"
      aria-modal="false"
      :aria-labelledby="'cookie-consent-title'"
    >
      <div class="cookie-consent__body">
        <div>
          <span class="cookie-consent__eyebrow">{{ t('privacy.cookies.eyebrow') }}</span>
          <h2 id="cookie-consent-title">{{ t('privacy.cookies.title') }}</h2>
          <p>{{ t('privacy.cookies.description') }}</p>
        </div>

        <div v-if="state.settingsOpen" class="cookie-consent__settings">
          <label class="cookie-consent__category is-locked">
            <span>
              <strong>{{ t('privacy.cookies.categories.necessary.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.necessary.description') }}</small>
            </span>
            <input type="checkbox" checked disabled />
          </label>
          <label class="cookie-consent__category">
            <span>
              <strong>{{ t('privacy.cookies.categories.preferences.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.preferences.description') }}</small>
            </span>
            <input v-model="state.choice.preferences" type="checkbox" :disabled="disabled" />
          </label>
          <label class="cookie-consent__category">
            <span>
              <strong>{{ t('privacy.cookies.categories.analytics.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.analytics.description') }}</small>
            </span>
            <input v-model="state.choice.analytics" type="checkbox" :disabled="disabled" />
          </label>
          <label class="cookie-consent__category">
            <span>
              <strong>{{ t('privacy.cookies.categories.externalMedia.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.externalMedia.description') }}</small>
            </span>
            <input v-model="state.choice.external_media" type="checkbox" :disabled="disabled" />
          </label>
        </div>

        <p v-if="state.error" class="cookie-consent__error" role="alert">{{ state.error }}</p>

        <div class="cookie-consent__actions">
          <button type="button" class="cookie-action cookie-action--choice" :disabled="disabled" @click="rejectOptional">
            {{ t('privacy.cookies.rejectOptional') }}
          </button>
          <button type="button" class="cookie-action" :disabled="disabled" @click="toggleSettings">
            {{ state.settingsOpen ? t('privacy.cookies.hideSettings') : t('privacy.cookies.settings') }}
          </button>
          <button
            v-if="state.settingsOpen"
            type="button"
            class="cookie-action cookie-action--primary"
            :disabled="disabled"
            @click="saveCustom"
          >
            {{ t('privacy.cookies.saveSelection') }}
          </button>
          <button
            v-else
            type="button"
            class="cookie-action cookie-action--choice"
            :disabled="disabled"
            @click="acceptAll"
          >
            {{ t('privacy.cookies.acceptAll') }}
          </button>
        </div>
      </div>
    </section>
  </Teleport>
</template>

<style scoped>
.cookie-consent {
  position: fixed;
  /* Keep the consent surface above shell drawers even if a custom theme omits the token. */
  z-index: var(--z-consent, 900);
  right: 1rem;
  bottom: 1rem;
  left: 1rem;
  display: flex;
  justify-content: center;
  isolation: isolate;
  pointer-events: none;
}

.cookie-consent__body {
  width: min(60rem, 100%);
  max-height: min(80vh, 48rem);
  overflow: auto;
  padding: 1.1rem;
  border: 1px solid var(--line-strong, rgba(255, 255, 255, 0.24));
  background: var(--panel-solid, #111820);
  box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.45);
  pointer-events: auto;
}

.cookie-consent__eyebrow,
.cookie-consent__category small {
  color: var(--text-muted, #a9b4bf);
}

.cookie-consent h2 {
  margin: 0.2rem 0 0.45rem;
}

.cookie-consent p {
  margin: 0;
  line-height: 1.55;
}

.cookie-consent__settings {
  display: grid;
  gap: 0.6rem;
  margin-top: 1rem;
}

.cookie-consent__category {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid var(--line-soft, rgba(255, 255, 255, 0.12));
}

.cookie-consent__category span {
  display: grid;
  gap: 0.2rem;
}

.cookie-consent__category input {
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 auto;
}

.cookie-consent__category.is-locked {
  opacity: 0.8;
}

.cookie-consent__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1rem;
}

.cookie-action {
  min-height: 2.75rem;
  padding: 0.65rem 1rem;
  border: 1px solid var(--line-strong, rgba(255, 255, 255, 0.24));
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.cookie-action--choice {
  background: rgba(197, 164, 109, 0.14);
  border-color: var(--accent, #c5a46d);
}

.cookie-action--primary {
  background: var(--accent, #c5a46d);
  color: #101318;
}

.cookie-action:disabled {
  cursor: wait;
  opacity: 0.6;
}

.cookie-consent__error {
  margin-top: 0.75rem;
  color: var(--danger, #ff8a8a);
}

@media (max-width: 720px) {
  .cookie-consent {
    right: 0.5rem;
    bottom: 0.5rem;
    left: 0.5rem;
  }

  .cookie-consent__actions {
    display: grid;
  }

  .cookie-action {
    width: 100%;
  }
}
</style>
