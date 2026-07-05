import { get, put } from './api'

export function getProfile() {
  return get('/profile')
}

export function updateProfile(payload) {
  return put('/profile', payload)
}
