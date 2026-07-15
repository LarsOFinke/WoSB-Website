<script setup>
import { ref } from 'vue'

import PageHeader from '@/core/components/PageHeader.vue'
import DiscordBotOperationsPanel from '@/modules/admin/components/DiscordBotOperationsPanel.vue'
import OutboundWebhookManagementPanel from '@/modules/admin/components/OutboundWebhookManagementPanel.vue'
import { useLocale } from '@/locales'
import { useSession } from '@/modules/accounts/session'

const { t } = useLocale()
const { isAdmin } = useSession()
const activeArea = ref('bot')
</script>

<template>
  <div class="page-shell bot-setup-page">
    <PageHeader :eyebrow="t('botSetup.eyebrow')" :title="t('botSetup.title')" :subtitle="t('botSetup.subtitle')" />

    <nav class="wire-section staff-tab-navigation" :aria-label="t('botSetup.tabs.label')">
      <button class="staff-tab-button" :class="{ 'is-active': activeArea === 'bot' }" type="button" @click="activeArea = 'bot'">{{ t('botSetup.tabs.bot') }}</button>
      <button class="staff-tab-button" :class="{ 'is-active': activeArea === 'webhooks' }" type="button" @click="activeArea = 'webhooks'">{{ t('botSetup.tabs.chatWebhooks') }}</button>
    </nav>

    <template v-if="activeArea === 'bot'">
      <section class="wire-section bot-setup-intro">
        <div><span class="command-deck-eyebrow">{{ t('botSetup.bot.eyebrow') }}</span><h2>{{ t('botSetup.bot.title') }}</h2><p>{{ t('botSetup.bot.text') }}</p></div>
      </section>
      <DiscordBotOperationsPanel />
    </template>

    <template v-else>
      <section class="wire-section bot-routing-guide">
        <div><span class="command-deck-eyebrow">{{ t('botSetup.chatWebhooks.eyebrow') }}</span><h2>{{ t('botSetup.chatWebhooks.title') }}</h2><p>{{ t('botSetup.chatWebhooks.text') }}</p></div>
        <div class="bot-routing-cards">
          <article><strong>{{ t('botSetup.chatWebhooks.directTitle') }}</strong><p>{{ t('botSetup.chatWebhooks.directText') }}</p></article>
          <article><strong>{{ t('botSetup.chatWebhooks.eventsTitle') }}</strong><p>{{ t('botSetup.chatWebhooks.eventsText') }}</p></article>
          <article><strong>{{ t('botSetup.chatWebhooks.scopesTitle') }}</strong><p>{{ t('botSetup.chatWebhooks.scopesText') }}</p></article>
        </div>
      </section>
      <OutboundWebhookManagementPanel :can-manage="isAdmin" />
    </template>
  </div>
</template>
