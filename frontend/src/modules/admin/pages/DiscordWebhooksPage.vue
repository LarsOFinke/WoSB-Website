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

    <section class="wire-section webhook-delivery-guide">
      <div>
        <span class="command-deck-eyebrow">{{ t('webhookSetup.delivery.eyebrow') }}</span>
        <h2>{{ t('webhookSetup.delivery.title') }}</h2>
        <p>{{ t('webhookSetup.delivery.text') }}</p>
      </div>
      <div class="webhook-routing-cards">
        <article>
          <strong>{{ t('webhookSetup.delivery.directTitle') }}</strong>
          <p>{{ t('webhookSetup.delivery.directText') }}</p>
        </article>
        <article>
          <strong>{{ t('webhookSetup.delivery.scopesTitle') }}</strong>
          <p>{{ t('webhookSetup.delivery.scopesText') }}</p>
        </article>
        <article>
          <strong>{{ t('webhookSetup.delivery.historyTitle') }}</strong>
          <p>{{ t('webhookSetup.delivery.historyText') }}</p>
        </article>
        <article>
          <strong>{{ t('webhookSetup.delivery.multiChannelTitle') }}</strong>
          <p>{{ t('webhookSetup.delivery.multiChannelText') }}</p>
        </article>
      </div>
    </section>

    <section class="wire-section webhook-template-reference">
      <div>
        <span class="command-deck-eyebrow">{{ t('webhookSetup.templates.eyebrow') }}</span>
        <h2>{{ t('webhookSetup.templates.title') }}</h2>
        <p>{{ t('webhookSetup.templates.text') }}</p>
        <code>docs/webhook-templates/message-templates/</code>
      </div>
    </section>

    <DiscordBroadcastPanel :can-manage="isAdmin" />

    <OutboundWebhookManagementPanel :can-manage="isAdmin" />
  </div>
</template>
