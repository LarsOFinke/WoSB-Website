import { apiClient } from './apiClient'

export const adminService = {
  async listGroups() {
    const { data } = await apiClient.get('/admin/groups')
    return data
  },
}
