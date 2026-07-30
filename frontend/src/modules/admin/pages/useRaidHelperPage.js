import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import {
  createRaidHelperDestination,
  createRaidHelperProfile,
  createRaidHelperTemplate,
  deleteRaidHelperDestination,
  deleteRaidHelperProfile,
  deleteRaidHelperTemplate,
  listRaidHelperDestinations,
  listRaidHelperProfiles,
  listRaidHelperTemplates,
  testRaidHelperDestination,
  testRaidHelperProfile,
  updateRaidHelperDestination,
  updateRaidHelperProfile,
  updateRaidHelperTemplate,
} from '@/modules/admin/api/admin'
import {
  RAID_HELPER_CALENDAR_PRESETS,
  RAID_HELPER_RECOMMENDED_PAYLOAD,
  applyRaidHelperCalendarPreset,
  applyRaidHelperRecommendedPayload,
} from '@/modules/admin/domain/raidHelperTemplates'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'
import { FLEET_EVENT_CATEGORIES } from '@/modules/calendar/api/calendar'
import { listSquads } from '@/modules/squads/api/squads'

const DEFAULT_API_BASE_URL = 'https://raid-helper.xyz/api/v4'
const DEFAULT_RAID_HELPER_PAYLOAD = RAID_HELPER_RECOMMENDED_PAYLOAD

function defaultProfileForm() {
  return {
    name: '',
    server_id: '',
    api_key: '',
    api_base_url: DEFAULT_API_BASE_URL,
    timezone: 'Europe/Berlin',
    default_leader_id: '',
    is_active: true,
  }
}

function defaultDestinationForm(profileId = '') {
  return {
    profile_id: profileId,
    name: '',
    channel_id: '',
    scope_type: 'fleet',
    squad_id: '',
    categories: [],
    is_default: true,
    is_active: true,
  }
}

function defaultTemplateForm(profileId = '') {
  return {
    profile_id: profileId,
    name: '',
    raid_template_id: 'Standard',
    scope_type: 'both',
    categories: [],
    title_template: '{{event.title}}',
    description_template: '**{{scope.name}}**\n{{event.description}}\nLocation: {{event.location}}',
    announcement_template: 'New {{event.category}} event: **{{event.title}}**',
    payload_template_json: DEFAULT_RAID_HELPER_PAYLOAD,
    is_default: true,
    is_active: true,
  }
}

export function useRaidHelperPage() {
  const { t } = useLocale()
  const { isAdmin, user } = useSession()
  const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))
  const profiles = ref([])
  const destinations = ref([])
  const templates = ref([])
  const squads = ref([])
  const loading = ref(false)
  const error = ref('')
  const notice = ref('')
  const profileEditId = ref(null)
  const destinationEditId = ref(null)
  const templateEditId = ref(null)

  const profileForm = reactive(defaultProfileForm())
  const destinationForm = reactive(defaultDestinationForm())
  const templateForm = reactive(defaultTemplateForm())

  const profileOptions = computed(() => profiles.value.filter((row) => row.is_active))
  const activeSquads = computed(() => squads.value.filter((row) => row.is_active))

  function toggleCategory(form, category) {
    const next = new Set(form.categories)
    next.has(category) ? next.delete(category) : next.add(category)
    form.categories = [...next]
  }

  async function loadAll() {
    loading.value = true
    error.value = ''
    try {
      ;[profiles.value, destinations.value, templates.value, squads.value] = await Promise.all([
        listRaidHelperProfiles(),
        listRaidHelperDestinations(),
        listRaidHelperTemplates(),
        listSquads({ includeInactive: true }),
      ])
      const firstProfileId = profileOptions.value[0]?.id || ''
      if (!destinationForm.profile_id) destinationForm.profile_id = firstProfileId
      if (!templateForm.profile_id) templateForm.profile_id = firstProfileId
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  function resetProfile() {
    profileEditId.value = null
    Object.assign(profileForm, defaultProfileForm())
  }

  function editProfile(row) {
    profileEditId.value = row.id
    Object.assign(profileForm, {
      name: row.name,
      server_id: row.server_id,
      api_key: '',
      api_base_url: row.api_base_url,
      timezone: row.timezone,
      default_leader_id: row.default_leader_id || '',
      is_active: row.is_active,
    })
  }

  async function saveProfile() {
    error.value = ''
    notice.value = ''
    try {
      const payload = {
        ...profileForm,
        api_key: profileForm.api_key || (profileEditId.value ? null : ''),
        default_leader_id: profileForm.default_leader_id.trim() || null,
      }
      if (profileEditId.value) await updateRaidHelperProfile(profileEditId.value, payload)
      else await createRaidHelperProfile(payload)
      notice.value = t('raidHelper.saved')
      resetProfile()
      await loadAll()
    } catch (err) {
      error.value = err.message
    }
  }

  async function removeProfile(row) {
    if (!confirm(t('raidHelper.confirmDelete'))) return
    try {
      await deleteRaidHelperProfile(row.id)
      await loadAll()
    } catch (err) {
      error.value = err.message
    }
  }

  async function testProfile(row) {
    error.value = ''
    notice.value = ''
    try {
      const result = await testRaidHelperProfile(row.id)
      notice.value = result.message
      if (!result.ok) error.value = result.message
    } catch (err) {
      error.value = err.message
    }
  }

  function resetDestination() {
    destinationEditId.value = null
    Object.assign(destinationForm, defaultDestinationForm(profileOptions.value[0]?.id || ''))
  }

  function editDestination(row) {
    destinationEditId.value = row.id
    Object.assign(destinationForm, {
      profile_id: row.profile_id,
      name: row.name,
      channel_id: row.channel_id,
      scope_type: row.scope_type,
      squad_id: row.squad_id || '',
      categories: [...row.categories],
      is_default: row.is_default,
      is_active: row.is_active,
    })
  }

  async function saveDestination() {
    error.value = ''
    notice.value = ''
    const payload = {
      ...destinationForm,
      profile_id: Number(destinationForm.profile_id),
      squad_id: destinationForm.scope_type === 'squad' ? Number(destinationForm.squad_id) : null,
    }
    try {
      if (destinationEditId.value) await updateRaidHelperDestination(destinationEditId.value, payload)
      else await createRaidHelperDestination(payload)
      notice.value = t('raidHelper.saved')
      resetDestination()
      await loadAll()
    } catch (err) {
      error.value = err.message
    }
  }

  async function testDestination(row) {
    if (!confirm(t('raidHelper.destinationTestConfirm'))) return
    error.value = ''
    notice.value = ''
    try {
      const result = await testRaidHelperDestination(row.id)
      if (result.ok) notice.value = result.message
      else error.value = result.message
    } catch (err) {
      error.value = err.message
    }
  }

  async function removeDestination(row) {
    if (!confirm(t('raidHelper.confirmDelete'))) return
    try {
      await deleteRaidHelperDestination(row.id)
      await loadAll()
    } catch (err) {
      error.value = err.message
    }
  }

  function resetTemplate() {
    templateEditId.value = null
    Object.assign(templateForm, defaultTemplateForm(profileOptions.value[0]?.id || ''))
  }

  function editTemplate(row) {
    templateEditId.value = row.id
    Object.assign(templateForm, {
      profile_id: row.profile_id,
      name: row.name,
      raid_template_id: row.raid_template_id,
      scope_type: row.scope_type,
      categories: [...row.categories],
      title_template: row.title_template,
      description_template: row.description_template,
      announcement_template: row.announcement_template,
      payload_template_json: row.payload_template_json,
      is_default: row.is_default,
      is_active: row.is_active,
    })
  }

  async function saveTemplate() {
    error.value = ''
    notice.value = ''
    const payload = { ...templateForm, profile_id: Number(templateForm.profile_id) }
    try {
      if (templateEditId.value) await updateRaidHelperTemplate(templateEditId.value, payload)
      else await createRaidHelperTemplate(payload)
      notice.value = t('raidHelper.saved')
      resetTemplate()
      await loadAll()
    } catch (err) {
      error.value = err.message
    }
  }

  async function removeTemplate(row) {
    if (!confirm(t('raidHelper.confirmDelete'))) return
    try {
      await deleteRaidHelperTemplate(row.id)
      await loadAll()
    } catch (err) {
      error.value = err.message
    }
  }

  onMounted(loadAll)

  return {
    t,
    isAdmin,
    user,
    navigationGroups,
    profiles,
    destinations,
    templates,
    loading,
    error,
    notice,
    profileEditId,
    destinationEditId,
    templateEditId,
    profileForm,
    destinationForm,
    templateForm,
    profileOptions,
    activeSquads,
    FLEET_EVENT_CATEGORIES,
    RAID_HELPER_CALENDAR_PRESETS,
    RAID_HELPER_RECOMMENDED_PAYLOAD,
    applyRaidHelperCalendarPreset,
    applyRaidHelperRecommendedPayload,
    toggleCategory,
    resetProfile,
    editProfile,
    saveProfile,
    removeProfile,
    testProfile,
    resetDestination,
    editDestination,
    saveDestination,
    testDestination,
    removeDestination,
    resetTemplate,
    editTemplate,
    saveTemplate,
    removeTemplate,
  }
}
