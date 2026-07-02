import { apiClient } from './apiClient'

export const groupService = {
  async list() {
    const { data } = await apiClient.get('/groups')
    return data
  },

  async manageable() {
    const { data } = await apiClient.get('/groups/manageable')
    return data
  },

  async get(id) {
    const { data } = await apiClient.get(`/groups/${id}`)
    return data
  },

  async create(payload) {
    const { data } = await apiClient.post('/groups', payload)
    return data
  },

  async update(id, payload) {
    const { data } = await apiClient.put(`/groups/${id}`, payload)
    return data
  },

  async join(id, payload = {}) {
    const { data } = await apiClient.post(`/groups/${id}/join`, payload)
    return data
  },

  async close(id) {
    const { data } = await apiClient.post(`/groups/${id}/close`)
    return data
  },

  async remove(id) {
    await apiClient.delete(`/groups/${id}`)
  },
}
