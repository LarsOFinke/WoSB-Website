import { apiClient } from './apiClient'

export const authService = {
  async login(username, password) {
    const { data } = await apiClient.post('/auth/login', {
      username,
      password,
    })
    return data
  },

  async register(payload) {
    const { data } = await apiClient.post('/auth/register', payload)
    return data
  },

  async me() {
    const { data } = await apiClient.get('/auth/me')
    return data
  },
}
