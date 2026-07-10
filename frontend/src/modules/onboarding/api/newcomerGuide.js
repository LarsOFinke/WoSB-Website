import { get, put } from '@/shared/api/client'

export function getNewcomerGuide() {
  return get('/newcomer-guide')
}

export function updateNewcomerGuide(payload) {
  return put('/newcomer-guide', payload)
}
