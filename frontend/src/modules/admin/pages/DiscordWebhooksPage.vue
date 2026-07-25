<script setup>
import { computed } from 'vue'

import DiscordBroadcastPanel from '@/modules/admin/components/DiscordBroadcastPanel.vue'
import OutboundWebhookManagementPanel from '@/modules/admin/components/OutboundWebhookManagementPanel.vue'
import StaffWorkspaceShell from '@/modules/admin/components/StaffWorkspaceShell.vue'
import { createStaffNavigationGroups } from '@/modules/admin/domain/staffNavigation'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { isAdmin, user } = useSession()
const navigationGroups = computed(() => createStaffNavigationGroups(t, { isAdmin: isAdmin.value }))
</script>

<template>
  <StaffWorkspaceShell
    :eyebrow="t('webhookSetup.eyebrow')"
    :title="t('webhookSetup.title')"
    :description="t('webhookSetup.subtitle')"
    title-id="webhook-workspace-title"
    :groups="navigationGroups"
    active-key="webhooks"
    :user="user"
    :role-label="user ? t(`roles.${user.role}`) : ''"
    :is-admin="isAdmin"
  >
    <template #actions><RouterLink class="button-box" to="/admin">{{ t('masterData.back') }}</RouterLink></template>
    <div class="discord-webhooks-page staff-subworkspace">

      <OutboundWebhookManagementPanel :can-manage="isAdmin" />

      <DiscordBroadcastPanel :can-manage="isAdmin" />

      <details class="wire-section webhook-delivery-guide webhook-help-disclosure">
        <summary><span>{{ t('webhookSetup.delivery.title') }}</span><small>{{ t('webhookSetup.delivery.text') }}</small></summary>
        <div class="webhook-routing-cards">
          <article><strong>{{ t('webhookSetup.delivery.directTitle') }}</strong><p>{{ t('webhookSetup.delivery.directText') }}</p></article>
          <article><strong>{{ t('webhookSetup.delivery.scopesTitle') }}</strong><p>{{ t('webhookSetup.delivery.scopesText') }}</p></article>
          <article><strong>{{ t('webhookSetup.delivery.historyTitle') }}</strong><p>{{ t('webhookSetup.delivery.historyText') }}</p></article>
          <article><strong>{{ t('webhookSetup.delivery.multiChannelTitle') }}</strong><p>{{ t('webhookSetup.delivery.multiChannelText') }}</p></article>
        </div>
      </details>
    </div>
  </StaffWorkspaceShell>
</template>
