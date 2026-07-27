import { computed } from 'vue'

import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'

export function useDiscordWebhooksPage() {
  const { t } = useLocale()
  const { isAdmin, user } = useSession()
  const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))

  return {
    t,
    isAdmin,
    user,
    navigationGroups,
  }
}
