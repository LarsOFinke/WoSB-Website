import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const systemPanel = await readFile(new URL('../src/modules/admin/components/SystemOperationsPanel.vue', import.meta.url), 'utf8')
const botPanel = await readFile(new URL('../src/modules/admin/components/DiscordBotOperationsPanel.vue', import.meta.url), 'utf8')
const api = await readFile(new URL('../src/modules/admin/api/admin.js', import.meta.url), 'utf8')

test('Discord bot manager is embedded only in the administrator system panel', () => {
  assert.ok(systemPanel.includes('<DiscordBotOperationsPanel v-if="isAdmin" />'))
})

test('Discord bot manager exposes only allow-listed operations', () => {
  for (const operation of ['install', 'update', 'start', 'stop', 'restart']) {
    assert.ok(botPanel.includes(`trigger('${operation}')`))
  }
  assert.ok(api.includes("post('/admin/system/discord-bot', { operation })"))
})
