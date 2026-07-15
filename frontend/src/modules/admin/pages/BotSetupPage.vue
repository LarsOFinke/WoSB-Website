<script setup>
import PageHeader from '@/core/components/PageHeader.vue'
import DiscordBotOperationsPanel from '@/modules/admin/components/DiscordBotOperationsPanel.vue'
import { useLocale } from '@/locales'

const { t } = useLocale()
</script>

<template>
  <div class="page-shell bot-setup-page">
    <PageHeader :eyebrow="t('botSetup.eyebrow')" :title="t('botSetup.title')" :subtitle="t('botSetup.subtitle')" />

    <section class="wire-section bot-setup-intro">
      <div>
        <span class="command-deck-eyebrow">{{ t('botSetup.bot.eyebrow') }}</span>
        <h2>{{ t('botSetup.bot.title') }}</h2>
        <p>{{ t('botSetup.bot.text') }}</p>
      </div>
    </section>

    <DiscordBotOperationsPanel />
  </div>
</template>
