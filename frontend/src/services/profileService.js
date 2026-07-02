import { apiClient } from "./apiClient";

export const profileService = {
  async getMe() {
    const { data } = await apiClient.get("/profile/me");
    return data;
  },

  async updateMe(payload) {
    const { data } = await apiClient.put("/profile/me", payload);
    return data;
  },
};
