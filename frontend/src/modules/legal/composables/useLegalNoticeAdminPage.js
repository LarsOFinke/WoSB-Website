import { computed, onMounted, reactive, ref } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import {
  getAdminLegalNotice,
  resetAdminLegalNoticeToEnvironment,
  updateAdminLegalNotice,
} from '@/modules/legal/api/legalNotice'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

const FIELD_NAMES = [
  'published', 'provider_name', 'legal_form', 'represented_by', 'street', 'postal_code',
  'city', 'country', 'email', 'phone', 'register_name', 'register_court', 'register_number',
  'vat_id', 'business_id', 'supervisory_authority', 'editorial_responsible_name',
  'editorial_responsible_street', 'editorial_responsible_postal_code',
  'editorial_responsible_city', 'editorial_responsible_country', 'dispute_resolution_text',
  'additional_information', 'public_repository_url',
]

function emptyForm() {
  return {
    published: false,
    provider_name: '', legal_form: '', represented_by: '', street: '', postal_code: '', city: '',
    country: 'Deutschland', email: '', phone: '', register_name: '', register_court: '',
    register_number: '', vat_id: '', business_id: '', supervisory_authority: '',
    editorial_responsible_name: '', editorial_responsible_street: '',
    editorial_responsible_postal_code: '', editorial_responsible_city: '',
    editorial_responsible_country: 'Deutschland', dispute_resolution_text: '',
    additional_information: '', public_repository_url: '',
  }
}

export function useLegalNoticeAdminPage() {
  const { locale, t } = useLocale()
  const { isAdmin, user } = useSession()
  const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))
  const form = reactive(emptyForm())
  const meta = reactive({ source: 'environment', updated_at: '', updated_by_username: 'environment' })
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const success = ref('')

  const sourceLabel = computed(() => t(`legalNotice.admin.sources.${meta.source || 'environment'}`))
  const updatedLabel = computed(() => {
    if (!meta.updated_at) return ''
    return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(meta.updated_at))
  })

  function hydrate(payload) {
    for (const field of FIELD_NAMES) form[field] = payload[field] ?? emptyForm()[field]
    meta.source = payload.source || 'environment'
    meta.updated_at = payload.updated_at || ''
    meta.updated_by_username = payload.updated_by_username || 'environment'
  }

  async function load() {
    loading.value = true
    error.value = ''
    try {
      hydrate(await getAdminLegalNotice())
    } catch (err) {
      error.value = err.message || t('legalNotice.admin.loadError')
    } finally {
      loading.value = false
    }
  }

  async function save() {
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      const payload = Object.fromEntries(FIELD_NAMES.map((field) => [field, form[field]]))
      hydrate(await updateAdminLegalNotice(payload))
      success.value = t('legalNotice.admin.saved')
    } catch (err) {
      error.value = err.message || t('legalNotice.admin.saveError')
    } finally {
      saving.value = false
    }
  }

  async function resetToEnvironment() {
    if (!window.confirm(t('legalNotice.admin.resetConfirm'))) return
    saving.value = true
    error.value = ''
    success.value = ''
    try {
      hydrate(await resetAdminLegalNoticeToEnvironment())
      success.value = t('legalNotice.admin.resetSuccess')
    } catch (err) {
      error.value = err.message || t('legalNotice.admin.resetError')
    } finally {
      saving.value = false
    }
  }

  onMounted(load)

  return {
    t, isAdmin, user, navigationGroups, form, meta, loading, saving, error, success,
    sourceLabel, updatedLabel, load, save, resetToEnvironment,
  }
}
