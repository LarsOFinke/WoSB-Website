import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const botSetupPage = await readFile(new URL('../src/modules/admin/pages/BotSetupPage.vue', import.meta.url), 'utf8')
const webhookPage = await readFile(new URL('../src/modules/admin/pages/DiscordWebhooksPage.vue', import.meta.url), 'utf8')
const adminRoutes = await readFile(new URL('../src/modules/admin/routes.js', import.meta.url), 'utf8')
const workspaceLinks = await readFile(new URL('../src/core/navigation/workspaceLinks.js', import.meta.url), 'utf8')
const botPanel = await readFile(new URL('../src/modules/admin/components/DiscordBotOperationsPanel.vue', import.meta.url), 'utf8')
const api = await readFile(new URL('../src/modules/admin/api/admin.js', import.meta.url), 'utf8')

test('Discord bot and Discord webhooks have independent administrator routes', () => {
  assert.ok(adminRoutes.includes("path: '/admin/bot-setup'"))
  assert.ok(adminRoutes.includes("path: '/admin/discord-webhooks'"))
  assert.ok(botSetupPage.includes('<DiscordBotOperationsPanel />'))
  assert.ok(!botSetupPage.includes('OutboundWebhookManagementPanel'))
  assert.ok(!botSetupPage.includes('activeArea'))
  assert.ok(webhookPage.includes('<OutboundWebhookManagementPanel'))
  assert.ok(!webhookPage.includes('DiscordBotOperationsPanel'))
})

test('staff navigation exposes separate bot and webhook entries', () => {
  assert.ok(workspaceLinks.includes("to: '/admin/bot-setup'"))
  assert.ok(workspaceLinks.includes("to: '/admin/discord-webhooks'"))
  assert.ok(workspaceLinks.includes("t('botSetup.navigation')"))
  assert.ok(workspaceLinks.includes("t('webhookSetup.navigation')"))
})

test('Discord bot manager exposes only allow-listed operations', () => {
  for (const operation of ['install', 'update', 'start', 'stop', 'restart']) {
    assert.ok(botPanel.includes(`trigger('${operation}')`))
  }
  assert.ok(api.includes("post('/admin/system/discord-bot', { operation })"))
})

test('Discord bot runtime configuration is sent through a dedicated administrator endpoint', () => {
  assert.ok(api.includes("put('/admin/system/discord-bot/configuration', configuration)"))
  assert.ok(botPanel.includes('@submit.prevent="saveConfiguration"'))
  assert.ok(botPanel.includes('configurationForm.discord_bot_token'))
  assert.ok(botPanel.includes('configurationForm.webhook_secret'))
  assert.ok(!botPanel.includes('channel_id'))
  assert.ok(botPanel.includes('configurationForm.restart_after_save'))
})

test('Discord bot secrets are write-only in the staff panel', () => {
  assert.ok(botPanel.includes('type="password"'))
  assert.ok(botPanel.includes('Leave blank') || botPanel.includes("configuration.keepSecret"))
  assert.ok(!botPanel.includes(':value="config.discord_bot_token"'))
  assert.ok(!botPanel.includes(':value="config.webhook_secret"'))
})

test('Discord bot panel surfaces the gateway binding and firewall mode without exposing secrets', () => {
  assert.ok(botPanel.includes('config.bind_host'))
  assert.ok(botPanel.includes('config.listen_port'))
  assert.ok(botPanel.includes('config.firewall_mode'))
})
