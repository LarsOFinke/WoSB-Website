<script setup>
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { useRaidHelperPage } from '@/modules/admin/pages/useRaidHelperPage'

const {
  t, isAdmin, user, navigationGroups, profiles, destinations, templates, loading, error, notice,
  profileEditId, destinationEditId, templateEditId, destinationTestTemplateIds, profileForm, destinationForm, templateForm,
  profileOptions, activeSquads, templatesForDestination, FLEET_EVENT_CATEGORIES, RAID_HELPER_CALENDAR_PRESETS,
  applyRaidHelperCalendarPreset, applyRaidHelperFreePayload, applyRaidHelperPremiumPayload, setRaidHelperPremiumFeatures,
  toggleCategory, resetProfile, editProfile, saveProfile, removeProfile,
  testProfile, resetDestination, editDestination, saveDestination, testDestination, removeDestination, resetTemplate,
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
          <div class="raid-helper-row-actions">
            <label class="raid-helper-test-template">
              <span>{{ t('raidHelper.testTemplate') }}</span>
              <select v-model="destinationTestTemplateIds[row.id]">
                <option value="">{{ t('raidHelper.minimalPayload') }}</option>
                <option v-for="template in templatesForDestination(row)" :key="template.id" :value="template.id">
                  {{ template.name }}{{ template.raid_template_id ? ` · ${template.raid_template_id}` : ` · ${t('raidHelper.serverDefaultTemplate')}` }}
                </option>
              </select>
            </label>
            <button class="small-action" @click="testDestination(row)">{{ t('raidHelper.testDestination') }}</button>
            <button class="small-action" @click="editDestination(row)">{{ t('common.edit') }}</button>
            <button class="small-action danger" @click="removeDestination(row)">{{ t('common.delete') }}</button>
          </div>
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
          <label class="is-wide raid-helper-premium-toggle"><input v-model="templateForm.uses_premium_features" type="checkbox" @change="setRaidHelperPremiumFeatures(templateForm, templateForm.uses_premium_features)" /> <span>{{ t('raidHelper.premiumFeatures') }}</span><small>{{ t('raidHelper.premiumFeaturesHelp') }}</small></label>
          <label><span>{{ t('raidHelper.raidTemplateId') }}</span><input v-model="templateForm.raid_template_id" :disabled="!templateForm.uses_premium_features" :placeholder="t('raidHelper.raidTemplateIdPlaceholder')" /><small>{{ t('raidHelper.raidTemplateIdHelp') }}</small></label>
          <select v-model="templateForm.scope_type"><option value="both">{{ t('raidHelper.bothScopes') }}</option><option value="fleet">{{ t('raidHelper.fleet') }}</option><option value="squad">{{ t('raidHelper.squad') }}</option></select>
          <fieldset><legend>{{ t('raidHelper.categories') }}</legend><label v-for="category in FLEET_EVENT_CATEGORIES" :key="category"><input type="checkbox" :checked="templateForm.categories.includes(category)" @change="toggleCategory(templateForm, category)" /> {{ t(`calendar.categories.${category}`) }}</label></fieldset>
          <label class="is-wide"><span>{{ t('raidHelper.titleTemplate') }}</span><input v-model="templateForm.title_template" required /></label>
          <label class="is-wide"><span>{{ t('raidHelper.descriptionTemplate') }}</span><textarea v-model="templateForm.description_template" rows="5"></textarea></label>
          <label class="is-wide"><span>{{ t('raidHelper.announcementTemplate') }}</span><textarea v-model="templateForm.announcement_template" :disabled="!templateForm.uses_premium_features" rows="3"></textarea></label>
          <label class="is-wide"><span>{{ t('raidHelper.payloadTemplate') }}</span><textarea v-model="templateForm.payload_template_json" rows="12" spellcheck="false"></textarea><small>{{ t('raidHelper.payloadHelp') }}</small><span class="raid-helper-payload-actions"><button class="small-action raid-helper-payload-preset" type="button" @click="applyRaidHelperFreePayload(templateForm)">{{ t('raidHelper.freePayload') }}</button><button class="small-action raid-helper-payload-preset" type="button" @click="applyRaidHelperPremiumPayload(templateForm)">{{ t('raidHelper.premiumPayload') }}</button></span></label>
          <label><input v-model="templateForm.is_default" type="checkbox" /> {{ t('raidHelper.defaultTemplate') }}</label>
          <label><input v-model="templateForm.is_active" type="checkbox" /> {{ t('common.active') }}</label>
          <div class="form-actions is-wide"><button class="button-box primary-action" type="submit">{{ t('common.save') }}</button><button v-if="templateEditId" class="button-box" type="button" @click="resetTemplate">{{ t('common.cancel') }}</button></div>
        </form>
        <article v-for="row in templates" :key="row.id" class="raid-helper-row">
          <div><strong>{{ row.name }}</strong><small>{{ row.profile_name }} · {{ row.raid_template_id || t('raidHelper.serverDefaultTemplate') }} · {{ row.scope_type }} · {{ row.uses_premium_features ? t('raidHelper.premiumMode') : t('raidHelper.freeMode') }}</small></div>
          <div><button class="small-action" @click="editTemplate(row)">{{ t('common.edit') }}</button><button class="small-action danger" @click="removeTemplate(row)">{{ t('common.delete') }}</button></div>
        </article>
      </section>
    </div>
  </StaffWorkspaceShell>
</template>
