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
      v-if="state.visible || state.loading"
      class="rbf-choice-surface"
      :class="{ 'is-loading': state.loading }"
      :data-consent-state="state.loading ? 'loading' : state.error ? 'error' : state.settingsOpen ? 'settings' : 'banner'"
      role="dialog"
      aria-modal="false"
      :aria-busy="state.loading ? 'true' : 'false'"
      :aria-labelledby="'rbf-choice-title'"
    >
      <div class="rbf-choice-surface__body">
        <div>
          <span class="rbf-choice-surface__eyebrow">{{ t('privacy.cookies.eyebrow') }}</span>
          <h2 id="rbf-choice-title">{{ t('privacy.cookies.title') }}</h2>
          <p>{{ t('privacy.cookies.description') }}</p>
        </div>

        <div v-if="state.settingsOpen" class="rbf-choice-surface__settings">
          <label class="rbf-choice-surface__category is-locked">
            <span>
              <strong>{{ t('privacy.cookies.categories.necessary.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.necessary.description') }}</small>
            </span>
            <input type="checkbox" checked disabled />
          </label>
          <label class="rbf-choice-surface__category">
            <span>
              <strong>{{ t('privacy.cookies.categories.preferences.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.preferences.description') }}</small>
            </span>
            <input v-model="state.choice.preferences" type="checkbox" :disabled="disabled" />
          </label>
          <label class="rbf-choice-surface__category">
            <span>
              <strong>{{ t('privacy.cookies.categories.analytics.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.analytics.description') }}</small>
            </span>
            <input v-model="state.choice.analytics" type="checkbox" :disabled="disabled" />
          </label>
          <label class="rbf-choice-surface__category">
            <span>
              <strong>{{ t('privacy.cookies.categories.externalMedia.title') }}</strong>
              <small>{{ t('privacy.cookies.categories.externalMedia.description') }}</small>
            </span>
            <input v-model="state.choice.external_media" type="checkbox" :disabled="disabled" />
          </label>
        </div>

        <p v-if="state.error" class="rbf-choice-surface__error" role="alert">{{ state.error }}</p>

        <div class="rbf-choice-surface__actions">
          <button type="button" class="rbf-choice-action rbf-choice-action--choice" :disabled="disabled" @click="rejectOptional">
            {{ t('privacy.cookies.rejectOptional') }}
          </button>
          <button type="button" class="rbf-choice-action" :disabled="disabled" @click="toggleSettings">
            {{ state.settingsOpen ? t('privacy.cookies.hideSettings') : t('privacy.cookies.settings') }}
          </button>
          <button
            v-if="state.settingsOpen"
            type="button"
            class="rbf-choice-action rbf-choice-action--primary"
            :disabled="disabled"
            @click="saveCustom"
          >
            {{ t('privacy.cookies.saveSelection') }}
          </button>
          <button
            v-else
            type="button"
            class="rbf-choice-action rbf-choice-action--choice"
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
.rbf-choice-surface {
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

.rbf-choice-surface__body {
  width: min(60rem, 100%);
  max-height: min(80vh, 48rem);
  overflow: auto;
  padding: 1.1rem;
  border: 1px solid var(--line-strong, rgba(255, 255, 255, 0.24));
  background: var(--panel-solid, #111820);
  box-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.45);
  pointer-events: auto;
}

.rbf-choice-surface.is-loading .rbf-choice-surface__body {
  pointer-events: none;
}

.rbf-choice-surface__eyebrow,
.rbf-choice-surface__category small {
  color: var(--text-muted, #a9b4bf);
}

.rbf-choice-surface h2 {
  margin: 0.2rem 0 0.45rem;
}

.rbf-choice-surface p {
  margin: 0;
  line-height: 1.55;
}

.rbf-choice-surface__settings {
  display: grid;
  gap: 0.6rem;
  margin-top: 1rem;
}

.rbf-choice-surface__category {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid var(--line-soft, rgba(255, 255, 255, 0.12));
}

.rbf-choice-surface__category span {
  display: grid;
  gap: 0.2rem;
}

.rbf-choice-surface__category input {
  width: 1.25rem;
  height: 1.25rem;
  flex: 0 0 auto;
}

.rbf-choice-surface__category.is-locked {
  opacity: 0.8;
}

.rbf-choice-surface__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.6rem;
  margin-top: 1rem;
}

.rbf-choice-action {
  min-height: 2.75rem;
  padding: 0.65rem 1rem;
  border: 1px solid var(--line-strong, rgba(255, 255, 255, 0.24));
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.rbf-choice-action--choice {
  background: rgba(197, 164, 109, 0.14);
  border-color: var(--accent, #c5a46d);
}

.rbf-choice-action--primary {
  background: var(--accent, #c5a46d);
  color: #101318;
}

.rbf-choice-action:disabled {
  cursor: wait;
  opacity: 0.6;
}

.rbf-choice-surface__error {
  margin-top: 0.75rem;
  color: var(--danger, #ff8a8a);
}

@media (max-width: 720px) {
  .rbf-choice-surface {
    right: 0.5rem;
    bottom: 0.5rem;
    left: 0.5rem;
  }

  .rbf-choice-surface__actions {
    display: grid;
  }

  .rbf-choice-action {
    width: 100%;
  }
}
</style>
