import { get, post, put } from '@/shared/api/client'

export function getPublicLegalNotice() {
  return get('/legal-notice')
}

export function getAdminLegalNotice() {
  return get('/admin/legal-notice')
}

export function updateAdminLegalNotice(payload) {
  return put('/admin/legal-notice', payload)
}

export function resetAdminLegalNoticeToEnvironment() {
  return post('/admin/legal-notice/reset-environment', {})
}
