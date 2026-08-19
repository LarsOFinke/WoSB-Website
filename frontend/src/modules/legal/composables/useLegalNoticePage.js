import { computed, onMounted, ref } from 'vue'

import { useLocale } from '@/locales'
import { getPublicLegalNotice } from '@/modules/legal/api/legalNotice'

const EMPTY_NOTICE = Object.freeze({ published: false })

export function useLegalNoticePage() {
  const { locale, t } = useLocale()
  const notice = ref({ ...EMPTY_NOTICE })
  const loading = ref(true)
  const error = ref('')

  const providerAddress = computed(() => [
    notice.value.street,
    [notice.value.postal_code, notice.value.city].filter(Boolean).join(' '),
    notice.value.country,
  ].filter(Boolean))

  const editorialAddress = computed(() => [
    notice.value.editorial_responsible_street,
    [notice.value.editorial_responsible_postal_code, notice.value.editorial_responsible_city].filter(Boolean).join(' '),
    notice.value.editorial_responsible_country,
  ].filter(Boolean))

  const registerDetails = computed(() => [
    notice.value.register_name,
    notice.value.register_court,
    notice.value.register_number,
  ].filter(Boolean))

  const hasRegisterDetails = computed(() => registerDetails.value.length > 0)
  const hasTaxDetails = computed(() => Boolean(notice.value.vat_id || notice.value.business_id))
  const hasEditorialResponsibility = computed(() => Boolean(notice.value.editorial_responsible_name))
  const publicRepositoryUrl = computed(() => {
    try {
      const url = new URL(notice.value.public_repository_url || '')
      return url.protocol === 'https:' ? url.href : ''
    } catch {
      return ''
    }
  })
  const lastUpdated = computed(() => {
    if (!notice.value.updated_at) return ''
    return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(notice.value.updated_at))
  })

  async function loadNotice() {
    loading.value = true
    error.value = ''
    try {
      notice.value = await getPublicLegalNotice()
    } catch (err) {
      error.value = err.message || t('legalNotice.public.loadError')
    } finally {
      loading.value = false
    }
  }

  onMounted(loadNotice)

  return {
    t,
    notice,
    loading,
    error,
    providerAddress,
    editorialAddress,
    registerDetails,
    hasRegisterDetails,
    hasTaxDetails,
    hasEditorialResponsibility,
    publicRepositoryUrl,
    lastUpdated,
    loadNotice,
  }
}
