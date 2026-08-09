import assert from 'node:assert/strict'
import test from 'node:test'

import {
  normalizeDiscordWebhookUrl,
  outboundWebhookPayload,
  webhookEventTemplate,
  webhookDraftIssues,
} from '../src/modules/admin/domain/outboundWebhook.js'

test('event template selection resolves the matching event instead of reusing one default', () => {
  const events = [
    { key: 'build.created', default_template: 'Build {resource.id} created' },
    { key: 'fleet.updated', default_template: 'Fleet {resource.id} updated' },
  ]

  assert.equal(webhookEventTemplate(events, 'build.created'), 'Build {resource.id} created')
  assert.equal(webhookEventTemplate(events, 'fleet.updated'), 'Fleet {resource.id} updated')
  assert.equal(webhookEventTemplate(events, 'missing.event'), '')
})

test('Discord webhook drafts accept copied and versioned official URLs', () => {
  const copied = '<https://discord.com/api/webhooks/123/copied-token>'
  const versioned = 'https://discord.com/api/v10/webhooks/123/versioned-token'

  assert.equal(normalizeDiscordWebhookUrl(copied), copied.slice(1, -1))
  assert.deepEqual(webhookDraftIssues({ name: 'Fleet', endpoint_url: copied, scope_type: 'global', event_types: ['build.created'] }), [])
  assert.deepEqual(webhookDraftIssues({ name: 'Fleet', endpoint_url: versioned, scope_type: 'global', event_types: [], broadcast_enabled: true }), [])
})

test('Discord webhook drafts expose actionable validation issues before requesting the API', () => {
  assert.deepEqual(
    webhookDraftIssues({ name: 'x', endpoint_url: 'https://example.com/hook', scope_type: 'fleet', scope_id: '', event_types: [] }),
    ['name', 'endpointInvalid', 'scope', 'events'],
  )
})

test('Discord webhook payloads trim optional values and normalize global scope', () => {
  assert.deepEqual(outboundWebhookPayload({
    name: '  Fleet alerts  ', endpoint_url: ' <https://discord.com/api/webhooks/123/token> ',
    scope_type: 'global', scope_id: 44, message_template: ' ', discord_username: ' RBF ',
    broadcast_enabled: false, is_active: true,
    event_types: ['guide.updated', 'guide.updated', 'build.created'],
  }), {
    name: 'Fleet alerts', endpoint_url: 'https://discord.com/api/webhooks/123/token',
    scope_type: 'global', scope_id: null, message_template: null, discord_username: 'RBF',
    broadcast_enabled: false, is_active: true,
    event_types: ['build.created', 'guide.updated'],
  })
})
