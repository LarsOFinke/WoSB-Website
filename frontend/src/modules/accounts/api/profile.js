import { get, put } from '@/shared/api/client'

export function getProfile() {
  return get('/profile')
}

export function updateProfile(payload) {
  return put('/profile', payload)
}
