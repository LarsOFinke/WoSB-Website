import { get, post } from '@/shared/api/client'

export function getCookieConsent() {
  return get('/privacy/cookie-consent', { cache: 'no-store' })
}

export function saveCookieConsent(choice) {
  return post('/privacy/cookie-consent', choice)
}
