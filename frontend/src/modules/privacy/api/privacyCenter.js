import { post } from '@/shared/api/client'

export function createPrivacyContact(payload) {
  return post('/privacy/contact', payload)
}
