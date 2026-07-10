<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import PageHeader from '@/core/components/PageHeader.vue'
import { useLocale } from '@/locales'
import { createSquad, listSquadRoster } from '@/modules/squads/api/squads'

const router = useRouter()
const { t } = useLocale()

const roster = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const form = reactive({
  name: '',
  description: '',
  focus: '',
  maxMembers: 12,
  leaderMembershipId: '',
})

const rosterOptions = computed(() => [...roster.value].sort((left, right) => left.display_name.localeCompare(right.display_name)))

async function loadRoster() {
  loading.value = true
  error.value = ''
  try {
    roster.value = await listSquadRoster()
  } catch (err) {
    error.value = err.message || t('squads.create.rosterError')
  } finally {
    loading.value = false
  }
}

async function submitSquad() {
  saving.value = true
  error.value = ''
  try {
    const squad = await createSquad({
      name: form.name,
      description: form.description || null,
      focus: form.focus || null,
      max_members: form.maxMembers ? Number(form.maxMembers) : null,
      leader_membership_id: Number(form.leaderMembershipId),
    })
    router.push(`/squads/${squad.id}`)
  } catch (err) {
    error.value = err.message || t('squads.create.saveError')
  } finally {
    saving.value = false
  }
}

onMounted(loadRoster)
</script>

<template>
  <section class="squad-page" aria-labelledby="squad-create-title">
    <form class="wire-frame page-frame create-frame squad-create-frame" @submit.prevent="submitSquad">
      <PageHeader
        :eyebrow="t('squads.create.eyebrow')"
        :title="t('squads.create.title')"
        :description="t('squads.create.subtitle')"
        title-id="squad-create-title"
      >
        <template #actions>
          <RouterLink class="button-box" to="/squads">{{ t('common.back') }}</RouterLink>
        </template>
      </PageHeader>

      <section class="wire-section form-section squad-form-section">
        <div class="section-title"><span>01</span><h2>{{ t('squads.create.identityTitle') }}</h2></div>
        <p class="section-helper-text">{{ t('squads.create.identityText') }}</p>
        <div class="section-fields squad-form-grid">
          <label class="field-stack">
            <span class="field-label">{{ t('squads.fields.name') }}</span>
            <span class="input-panel embedded-field"><input v-model="form.name" required minlength="2" maxlength="120" /></span>
          </label>
          <label class="field-stack">
            <span class="field-label">{{ t('squads.fields.focus') }}</span>
            <span class="input-panel embedded-field"><input v-model="form.focus" maxlength="160" :placeholder="t('squads.create.focusPlaceholder')" /></span>
          </label>
          <label class="field-stack">
            <span class="field-label">{{ t('squads.fields.maxMembers') }}</span>
            <span class="input-panel embedded-field"><input v-model.number="form.maxMembers" type="number" min="2" max="200" /></span>
          </label>
        </div>
        <label class="field-stack">
          <span class="field-label">{{ t('squads.fields.description') }}</span>
          <span class="input-panel embedded-field textarea-shell"><textarea v-model="form.description" rows="5" maxlength="3000" :placeholder="t('squads.create.descriptionPlaceholder')"></textarea></span>
        </label>
      </section>

      <section class="wire-section form-section squad-form-section">
        <div class="section-title"><span>02</span><h2>{{ t('squads.create.commandTitle') }}</h2></div>
        <p class="section-helper-text">{{ t('squads.create.commandText') }}</p>
        <p class="slot-hint">{{ t('squads.create.eligibleHint') }}</p>
        <label class="field-stack">
          <span class="field-label">{{ t('squads.fields.leader') }}</span>
          <span class="select-shell full-select-shell">
            <select v-model="form.leaderMembershipId" required :disabled="loading">
              <option value="">{{ loading ? t('squads.create.loadingRoster') : t('squads.create.selectLeader') }}</option>
              <option v-for="member in rosterOptions" :key="member.fleet_membership_id" :value="member.fleet_membership_id">
                {{ member.display_name }} · {{ t(`fleets.roles.${member.fleet_role}`) }}
              </option>
            </select>
          </span>
        </label>
      </section>

      <p v-if="error" class="error-text form-message">{{ error }}</p>
      <div class="form-actions">
        <button class="wire-section form-button primary" type="submit" :disabled="saving || loading || !form.leaderMembershipId">
          {{ saving ? t('squads.create.saving') : t('squads.create.save') }}
        </button>
      </div>
    </form>
  </section>
</template>
