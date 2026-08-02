import { onMounted, reactive, ref } from 'vue'

import { listPrivacyContacts, listPrivacyRequests, resolvePrivacyContact, resolvePrivacyRequest } from '@/modules/admin/api/admin'

export function usePrivacyRequestsPage({ t }) {
  const requests = ref([])
  const contacts = ref([])
  const loading = ref(false)
  const busy = ref(null)
  const error = ref('')
  const notes = reactive({})

  async function load() {
    loading.value = true
    error.value = ''
    try {
      ;[requests.value, contacts.value] = await Promise.all([
        listPrivacyRequests(),
        listPrivacyContacts(),
      ])
    } catch (err) {
      error.value = err.message || t('privacy.data.loadError')
    } finally {
      loading.value = false
    }
  }

  async function resolve(request, decision) {
    busy.value = request.id
    error.value = ''
    try {
      await resolvePrivacyRequest(request.id, {
        decision,
        resolution_note: notes[request.id] || (decision === 'complete' ? 'Request completed.' : 'Request rejected.'),
      })
      await load()
    } catch (err) {
      error.value = err.message || t('privacy.data.requestError')
    } finally {
      busy.value = null
    }
  }

  async function resolveContact(request, decision) {
    busy.value = `contact-${request.id}`
    error.value = ''
    try {
      await resolvePrivacyContact(request.id, {
        decision,
        resolution_note: notes[`contact-${request.id}`] || (decision === 'complete' ? 'Contact handled.' : 'Contact rejected.'),
      })
      await load()
    } catch (err) {
      error.value = err.message || t('privacy.data.requestError')
    } finally {
      busy.value = null
    }
  }

  onMounted(load)
  return { requests, contacts, loading, busy, error, notes, load, resolve, resolveContact }
}
