import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const adminSource = await readFile(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')
const auditSource = await readFile(new URL('../src/modules/admin/components/AuditLogPanel.vue', import.meta.url), 'utf8')
const webhookSource = await readFile(new URL('../src/modules/admin/components/OutboundWebhookManagementPanel.vue', import.meta.url), 'utf8')
const broadcastSource = await readFile(new URL('../src/modules/admin/components/DiscordBroadcastPanel.vue', import.meta.url), 'utf8')

test('staff workspace exposes combined filters for all shared management modules', () => {
  for (const binding of [
    'registrationSearch', 'registrationFromDate', 'registrationToDate',
    'calendarSearch', 'calendarFromDate', 'calendarToDate',
    'contentScope', 'contentOwner',
    'buildType', 'buildRate', 'buildVisibility',
    'userSearch', 'userRole', 'userStatus',
  ]) {
    assert.ok(adminSource.includes(`v-model="${binding}"`), binding)
  }
})

test('audit history includes newly introduced administrative entity types', () => {
  for (const entity of ['registration_request', 'user_account', 'fleet_membership', 'ip_block', 'outbound_webhook']) {
    assert.ok(auditSource.includes(`value="${entity}"`), entity)
  }
})

test('integration management filters endpoints and delivery history', () => {
  for (const binding of ['webhookSearch', 'webhookState', 'deliveryWebhook', 'deliveryStatus', 'deliveryEvent', 'form.scope_type']) {
    assert.ok(webhookSource.includes(`v-model="${binding}"`), binding)
  }
  assert.ok(webhookSource.includes("row.event_types[0] || 'integration.test'"))
})


test('Discord broadcasts can target several configured channel webhooks', () => {
  for (const binding of ['form.webhook_ids', 'form.message', 'form.discord_username', 'form.discord_avatar_url']) {
    assert.ok(broadcastSource.includes(binding), binding)
  }
  assert.ok(broadcastSource.includes('listBroadcastWebhookTargets'))
  assert.ok(broadcastSource.includes('sendDiscordBroadcast'))
  assert.ok(webhookSource.includes('form.broadcast_enabled'))
  assert.ok(webhookSource.includes('(form.event_types.length === 0 && !form.broadcast_enabled)'))
})
