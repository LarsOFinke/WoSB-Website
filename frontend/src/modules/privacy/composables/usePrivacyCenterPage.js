import { reactive, ref } from 'vue'

import { createPrivacyContact } from '@/modules/privacy/api/privacyCenter'


export function usePrivacyCenterPage({ t }) {
  const form = reactive({ reply_email: '', subject: '', message: '', website: '' })
  const busy = ref(false)
  const error = ref('')
  const success = ref('')

  async function submitContact() {
    busy.value = true
    error.value = ''
    success.value = ''
    try {
      await createPrivacyContact(form)
      form.subject = ''
      form.message = ''
      success.value = t('privacy.center.contactSuccess')
    } catch (err) {
      error.value = err.message || t('privacy.center.contactError')
    } finally {
      busy.value = false
    }
  }

  return { form, busy, error, success, submitContact }
}
