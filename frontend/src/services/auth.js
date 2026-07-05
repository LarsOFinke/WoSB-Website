import { get, post } from './api'

export function getCurrentUser() {
  return get('/auth/me')
}

export function login(username, password) {
  return post('/auth/login', { username, password })
}

export function register(payload) {
  return post('/auth/register', payload)
}

export function changePassword(payload) {
  return post('/auth/change-password', payload)
}

export function logout() {
  return post('/auth/logout', {})
}
