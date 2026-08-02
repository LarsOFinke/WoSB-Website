import { onMounted, reactive, ref } from 'vue'

import {
  createPrivacyRequest,
  exportPersonalData,
  listPrivacyRequests,
} from '@/modules/accounts/api/profile'

export function usePrivacySelfService({ t, username }) {
  const requests = ref([])
  const loading = ref(false)
  const busy = ref('')
  const error = ref('')
  const success = ref('')
  const form = reactive({ request_type: 'correction', details: '', confirmation: '' })

  async function loadRequests() {
    loading.value = true
    try {
      requests.value = await listPrivacyRequests()
    } catch (err) {
      error.value = err.message || t('privacy.data.loadError')
    } finally {
      loading.value = false
    }
  }

  async function downloadExport() {
    busy.value = 'export'
    error.value = ''
    try {
      const payload = await exportPersonalData()
      const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `wosb-personal-data-${new Date().toISOString().slice(0, 10)}.json`
      link.click()
      URL.revokeObjectURL(url)
      success.value = t('privacy.data.exportReady')
    } catch (err) {
      error.value = err.message || t('privacy.data.exportError')
    } finally {
      busy.value = ''
    }
  }

  async function submitRequest() {
    busy.value = 'request'
    error.value = ''
    success.value = ''
    try {
      await createPrivacyRequest({
        request_type: form.request_type,
        details: form.details || null,
        confirmation: form.request_type === 'deletion' ? form.confirmation : null,
      })
      form.details = ''
      form.confirmation = ''
      success.value = t('privacy.data.requestCreated')
      await loadRequests()
    } catch (err) {
      error.value = err.message || t('privacy.data.requestError')
    } finally {
      busy.value = ''
    }
  }

  onMounted(loadRequests)
  return { requests, loading, busy, error, success, form, username, downloadExport, submitRequest }
}
