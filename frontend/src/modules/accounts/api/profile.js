import { get, put } from '@/shared/api/client'

export function getProfile() {
  return get('/profile')
}

export function getProfilePreferenceOptions() {
  return get('/profile/preferences/options')
}

export function updateProfile(payload) {
  return put('/profile', payload)
}
