import { API_BASE_URL } from '@/config/runtime'

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
let csrfBootstrap = null

function cookieValue(name) {
  if (typeof document === 'undefined') return ''
  const prefix = `${encodeURIComponent(name)}=`
  return document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix))
    ?.slice(prefix.length) || ''
}

async function ensureCsrfCookie() {
  if (cookieValue('XSRF-TOKEN')) return
  csrfBootstrap ||= fetch(`${API_BASE_URL}/auth/me`, {
    credentials: 'include',
    cache: 'no-store',
    headers: { Accept: 'application/json' },
  }).finally(() => { csrfBootstrap = null })
  await csrfBootstrap
}

async function request(path, options = {}) {
  const method = String(options.method || 'GET').toUpperCase()
  if (UNSAFE_METHODS.has(method)) await ensureCsrfCookie()

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const headers = isFormData
    ? { ...(options.headers || {}) }
    : { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = cookieValue('XSRF-TOKEN')
  if (UNSAFE_METHODS.has(method) && token) headers['X-XSRF-TOKEN'] = decodeURIComponent(token)

  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers,
    ...options,
  })

  if (!response.ok) {
    let message = `API error ${response.status}`
    try {
      const payload = await response.json()
      if (typeof payload.detail === 'string') {
        message = payload.detail
      } else if (Array.isArray(payload.detail)) {
        message = payload.detail
          .map((item) => item?.msg || item?.message)
          .filter(Boolean)
          .join(' ') || message
      }
    } catch {
      // Keep the status-based fallback.
    }
    const error = new Error(message)
    error.status = response.status
    error.requestId = response.headers.get('X-Request-Id') || ''
    throw error
  }

  if (response.status === 204) return null
  return response.json()
}

export function get(path, options = {}) {
  return request(path, options)
}

export function post(path, payload, options = {}) {
  return request(path, { ...options, method: 'POST', body: JSON.stringify(payload) })
}

export function postForm(path, formData) {
  return request(path, { method: 'POST', body: formData })
}

export function put(path, payload, options = {}) {
  return request(path, { ...options, method: 'PUT', body: JSON.stringify(payload) })
}

export function putForm(path, formData) {
  return request(path, { method: 'PUT', body: formData })
}

export function deleteRequest(path, options = {}) {
  return request(path, { ...options, method: 'DELETE' })
}
