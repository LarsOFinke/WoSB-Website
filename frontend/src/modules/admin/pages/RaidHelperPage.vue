<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { useRaidHelperPage } from '@/modules/admin/pages/useRaidHelperPage'

const {
  t, isAdmin, user, navigationGroups, profiles, destinations, templates, loading, error, notice,
  profileEditId, destinationEditId, templateEditId, profileForm, destinationForm, templateForm,
  profileOptions, activeSquads, FLEET_EVENT_CATEGORIES, RAID_HELPER_CALENDAR_PRESETS,
  applyRaidHelperCalendarPreset, applyRaidHelperRecommendedPayload, toggleCategory, resetProfile, editProfile, saveProfile, removeProfile,
  testProfile, resetDestination, editDestination, saveDestination, removeDestination, resetTemplate,
  editTemplate, saveTemplate, removeTemplate,
} = useRaidHelperPage()
</script>

<template>
  <StaffWorkspaceShell
    :eyebrow="t('raidHelper.eyebrow')" :title="t('raidHelper.title')" :description="t('raidHelper.subtitle')"
    title-id="raid-helper-title" :groups="navigationGroups" active-key="raid-helper" :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''" :is-admin="isAdmin"
  >
    <template #actions><RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink></template>
    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="notice" class="success-text">{{ notice }}</p>
    <p v-if="loading">{{ t('common.loading') }}</p>

    <div v-else class="raid-helper-admin-grid">
      <section class="wire-section raid-helper-panel">
        <h2>{{ t('raidHelper.profiles') }}</h2>
        <p>{{ t('raidHelper.profileHelp') }}</p>
        <form class="raid-helper-form" @submit.prevent="saveProfile">
          <input v-model="profileForm.name" required :placeholder="t('raidHelper.name')" />
          <input v-model="profileForm.server_id" required inputmode="numeric" :placeholder="t('raidHelper.serverId')" />
          <input v-model="profileForm.api_key" :required="!profileEditId" type="password" autocomplete="new-password" :placeholder="profileEditId ? t('raidHelper.keepApiKey') : t('raidHelper.apiKey')" />
          <input v-model="profileForm.api_base_url" required aria-label="API base URL" />
          <label><span>{{ t('raidHelper.timezone') }}</span><input v-model="profileForm.timezone" required placeholder="Europe/Berlin" /><small>{{ t('raidHelper.timezoneHelp') }}</small></label>
          <label><span>{{ t('raidHelper.defaultLeaderId') }}</span><input v-model="profileForm.default_leader_id" inputmode="numeric" pattern="[0-9]+" :placeholder="t('raidHelper.defaultLeaderPlaceholder')" /><small>{{ t('raidHelper.defaultLeaderHelp') }}</small></label>
          <label><input v-model="profileForm.is_active" type="checkbox" /> {{ t('common.active') }}</label>
          <div class="form-actions"><button class="button-box primary-action" type="submit">{{ t('common.save') }}</button><button v-if="profileEditId" class="button-box" type="button" @click="resetProfile">{{ t('common.cancel') }}</button></div>
        </form>
        <article v-for="row in profiles" :key="row.id" class="raid-helper-row">
          <div><strong>{{ row.name }}</strong><small>{{ row.server_id }} · {{ row.timezone }} · {{ row.default_leader_id ? t('raidHelper.defaultLeaderConfigured', { id: row.default_leader_id }) : t('raidHelper.defaultLeaderMissing') }} · {{ row.api_key_configured ? 'API key set' : 'No API key' }}</small></div>
          <div><button class="small-action" @click="testProfile(row)">{{ t('raidHelper.test') }}</button><button class="small-action" @click="editProfile(row)">{{ t('common.edit') }}</button><button class="small-action danger" @click="removeProfile(row)">{{ t('common.delete') }}</button></div>
        </article>
      </section>

      <section class="wire-section raid-helper-panel">
        <h2>{{ t('raidHelper.destinations') }}</h2>
        <p>{{ t('raidHelper.destinationHelp') }}</p>
        <form class="raid-helper-form" @submit.prevent="saveDestination">
          <select v-model="destinationForm.profile_id" required><option disabled value="">{{ t('raidHelper.profile') }}</option><option v-for="row in profileOptions" :key="row.id" :value="row.id">{{ row.name }}</option></select>
          <input v-model="destinationForm.name" required :placeholder="t('raidHelper.name')" />
          <input v-model="destinationForm.channel_id" required inputmode="numeric" :placeholder="t('raidHelper.channelId')" />
          <select v-model="destinationForm.scope_type"><option value="fleet">{{ t('raidHelper.fleet') }}</option><option value="squad">{{ t('raidHelper.squad') }}</option></select>
          <select v-if="destinationForm.scope_type === 'squad'" v-model="destinationForm.squad_id" required><option disabled value="">{{ t('raidHelper.selectSquad') }}</option><option v-for="row in activeSquads" :key="row.id" :value="row.id">{{ row.name }}</option></select>
          <fieldset><legend>{{ t('raidHelper.categories') }}</legend><label v-for="category in FLEET_EVENT_CATEGORIES" :key="category"><input type="checkbox" :checked="destinationForm.categories.includes(category)" @change="toggleCategory(destinationForm, category)" /> {{ t(`calendar.categories.${category}`) }}</label><small>{{ t('raidHelper.emptyCategories') }}</small></fieldset>
          <label><input v-model="destinationForm.is_default" type="checkbox" /> {{ t('raidHelper.defaultTarget') }}</label>
          <label><input v-model="destinationForm.is_active" type="checkbox" /> {{ t('common.active') }}</label>
          <div class="form-actions"><button class="button-box primary-action" type="submit">{{ t('common.save') }}</button><button v-if="destinationEditId" class="button-box" type="button" @click="resetDestination">{{ t('common.cancel') }}</button></div>
        </form>
        <article v-for="row in destinations" :key="row.id" class="raid-helper-row">
          <div><strong>{{ row.name }}</strong><small>{{ row.profile_name }} · #{{ row.channel_id }} · {{ row.scope_type }}{{ row.squad_name ? ` / ${row.squad_name}` : '' }}</small></div>
          <div><button class="small-action" @click="editDestination(row)">{{ t('common.edit') }}</button><button class="small-action danger" @click="removeDestination(row)">{{ t('common.delete') }}</button></div>
        </article>
      </section>

      <section class="wire-section raid-helper-panel raid-helper-wide">
        <h2>{{ t('raidHelper.templates') }}</h2>
        <p>{{ t('raidHelper.templateHelp') }}</p>
        <form class="raid-helper-form raid-helper-template-form" @submit.prevent="saveTemplate">
          <div class="raid-helper-preset-actions is-wide">
            <span class="field-label">{{ t('raidHelper.presets') }}</span>
            <button
              v-for="preset in RAID_HELPER_CALENDAR_PRESETS"
              :key="preset.key"
              class="small-action"
              type="button"
              @click="applyRaidHelperCalendarPreset(templateForm, preset)"
            >
              {{ t(`raidHelper.preset.${preset.key}`) }}
            </button>
          </div>
          <select v-model="templateForm.profile_id" required><option disabled value="">{{ t('raidHelper.profile') }}</option><option v-for="row in profileOptions" :key="row.id" :value="row.id">{{ row.name }}</option></select>
          <input v-model="templateForm.name" required :placeholder="t('raidHelper.name')" />
          <input v-model="templateForm.raid_template_id" required :placeholder="t('raidHelper.raidTemplateId')" />
          <select v-model="templateForm.scope_type"><option value="both">{{ t('raidHelper.bothScopes') }}</option><option value="fleet">{{ t('raidHelper.fleet') }}</option><option value="squad">{{ t('raidHelper.squad') }}</option></select>
          <fieldset><legend>{{ t('raidHelper.categories') }}</legend><label v-for="category in FLEET_EVENT_CATEGORIES" :key="category"><input type="checkbox" :checked="templateForm.categories.includes(category)" @change="toggleCategory(templateForm, category)" /> {{ t(`calendar.categories.${category}`) }}</label></fieldset>
          <label class="is-wide"><span>{{ t('raidHelper.titleTemplate') }}</span><input v-model="templateForm.title_template" required /></label>
          <label class="is-wide"><span>{{ t('raidHelper.descriptionTemplate') }}</span><textarea v-model="templateForm.description_template" rows="5"></textarea></label>
          <label class="is-wide"><span>{{ t('raidHelper.announcementTemplate') }}</span><textarea v-model="templateForm.announcement_template" rows="3"></textarea></label>
          <label class="is-wide"><span>{{ t('raidHelper.payloadTemplate') }}</span><textarea v-model="templateForm.payload_template_json" rows="12" spellcheck="false"></textarea><small>{{ t('raidHelper.payloadHelp') }}</small><button class="small-action raid-helper-payload-preset" type="button" @click="applyRaidHelperRecommendedPayload(templateForm)">{{ t('raidHelper.recommendedPayload') }}</button></label>
          <label><input v-model="templateForm.is_default" type="checkbox" /> {{ t('raidHelper.defaultTemplate') }}</label>
          <label><input v-model="templateForm.is_active" type="checkbox" /> {{ t('common.active') }}</label>
          <div class="form-actions is-wide"><button class="button-box primary-action" type="submit">{{ t('common.save') }}</button><button v-if="templateEditId" class="button-box" type="button" @click="resetTemplate">{{ t('common.cancel') }}</button></div>
        </form>
        <article v-for="row in templates" :key="row.id" class="raid-helper-row">
          <div><strong>{{ row.name }}</strong><small>{{ row.profile_name }} · {{ row.raid_template_id }} · {{ row.scope_type }}</small></div>
          <div><button class="small-action" @click="editTemplate(row)">{{ t('common.edit') }}</button><button class="small-action danger" @click="removeTemplate(row)">{{ t('common.delete') }}</button></div>
        </article>
      </section>
    </div>
  </StaffWorkspaceShell>
</template>
