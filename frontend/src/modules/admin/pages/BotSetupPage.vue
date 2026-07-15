<script setup>
import { computed } from 'vue'

import PageHeader from '@/core/components/PageHeader.vue'
import DiscordBotOperationsPanel from '@/modules/admin/components/DiscordBotOperationsPanel.vue'
import OutboundWebhookManagementPanel from '@/modules/admin/components/OutboundWebhookManagementPanel.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { isAdmin } = useSession()
const receiverUrl = computed(() => typeof window === 'undefined'
  ? '/integrations/discord/webhooks/rbf'
  : `${window.location.origin}/integrations/discord/webhooks/rbf`)
</script>

<template>
  <div class="page-shell bot-setup-page">
    <PageHeader
      :eyebrow="t('botSetup.eyebrow')"
      :title="t('botSetup.title')"
      :subtitle="t('botSetup.subtitle')"
    />

    <section class="wire-section bot-setup-intro">
      <div>
        <span class="command-deck-eyebrow">{{ t('botSetup.pipeline.eyebrow') }}</span>
        <h2>{{ t('botSetup.pipeline.title') }}</h2>
        <p>{{ t('botSetup.pipeline.text') }}</p>
      </div>
      <ol class="bot-pipeline-steps">
        <li><strong>1</strong><span>{{ t('botSetup.pipeline.event') }}</span></li>
        <li><strong>2</strong><span>{{ t('botSetup.pipeline.delivery') }}</span></li>
        <li><strong>3</strong><span>{{ t('botSetup.pipeline.receiver') }}</span></li>
        <li><strong>4</strong><span>{{ t('botSetup.pipeline.discord') }}</span></li>
      </ol>
      <div class="bot-receiver-card">
        <span>{{ t('botSetup.receiverLabel') }}</span>
        <code>{{ receiverUrl }}</code>
        <small>{{ t('botSetup.receiverHint') }}</small>
      </div>
    </section>

    <DiscordBotOperationsPanel />

    <section class="wire-section bot-routing-guide">
      <div>
        <span class="command-deck-eyebrow">{{ t('botSetup.routing.eyebrow') }}</span>
        <h2>{{ t('botSetup.routing.title') }}</h2>
        <p>{{ t('botSetup.routing.text') }}</p>
      </div>
      <div class="bot-routing-cards">
        <article><strong>{{ t('botSetup.routing.webhook') }}</strong><p>{{ t('botSetup.routing.webhookText') }}</p></article>
        <article><strong>{{ t('botSetup.routing.channel') }}</strong><p>{{ t('botSetup.routing.channelText') }}</p></article>
        <article><strong>{{ t('botSetup.routing.template') }}</strong><p>{{ t('botSetup.routing.templateText') }}</p></article>
      </div>
    </section>

    <OutboundWebhookManagementPanel :can-manage="isAdmin" />
  </div>
</template>
