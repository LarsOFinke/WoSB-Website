<script setup>
import { ref } from 'vue'

import BroadcastWebhookManagementPanel from '@/modules/admin/components/BroadcastWebhookManagementPanel.vue'
import DiscordBroadcastPanel from '@/modules/admin/components/DiscordBroadcastPanel.vue'
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import WebhookDeliveryMonitor from '@/modules/admin/components/WebhookDeliveryMonitor.vue'
import { useDiscordWebhooksPage } from '@/modules/admin/composables/useDiscordWebhooksPage'

const {
  t,
  isAdmin,
  user,
  navigationGroups,
} = useDiscordWebhooksPage()

const broadcastTargets = ref([])
</script>

<template>
  <StaffWorkspaceShell
    :eyebrow="t('admin.webhooks.broadcast.pageEyebrow')"
    :title="t('admin.webhooks.broadcast.pageTitle')"
    :description="t('admin.webhooks.broadcast.pageSubtitle')"
    title-id="discord-broadcast-workspace-title"
    :groups="navigationGroups"
    active-key="broadcasts"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :is-admin="isAdmin"
  >
    <template #actions>
      <RouterLink class="button-box" to="/admin/discord-webhooks">{{ t('admin.webhooks.broadcast.openAutomation') }}</RouterLink>
      <RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink>
    </template>

    <div class="discord-broadcasts-page staff-subworkspace">
      <BroadcastWebhookManagementPanel :can-manage="isAdmin" @changed="broadcastTargets = $event" />
      <DiscordBroadcastPanel :can-manage="isAdmin" />
      <WebhookDeliveryMonitor
        :webhooks="broadcastTargets"
        :can-manage="isAdmin"
        fixed-event-type="broadcast.manual"
      />
    </div>
  </StaffWorkspaceShell>
</template>
