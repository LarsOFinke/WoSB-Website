import { get, post, put } from '@/shared/api/client'

export function getProfile() {
  return get('/profile')
}

export function getProfilePreferenceOptions() {
  return get('/profile/preferences/options')
}

export function updateProfile(payload) {
  return put('/profile', payload)
}

export function exportPersonalData() {
  return get('/privacy/data-export')
}

export function listPrivacyRequests() {
  return get('/privacy/requests')
}

export function createPrivacyRequest(payload) {
  return post('/privacy/requests', payload)
}
