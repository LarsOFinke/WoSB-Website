<script setup>
import PageHeader from '@/core/components/PageHeader.vue'
import DiscordBroadcastPanel from '@/modules/admin/components/DiscordBroadcastPanel.vue'
import OutboundWebhookManagementPanel from '@/modules/admin/components/OutboundWebhookManagementPanel.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { isAdmin } = useSession()
</script>

<template>
  <div class="page-shell discord-webhooks-page">
    <PageHeader :eyebrow="t('webhookSetup.eyebrow')" :title="t('webhookSetup.title')" :subtitle="t('webhookSetup.subtitle')" />

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
</template>
