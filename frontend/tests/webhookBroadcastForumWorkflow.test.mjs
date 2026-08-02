import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { readCssBundle } from './helpers/readCssBundle.mjs'

const deliverySource = await readFile(new URL('../src/modules/admin/components/WebhookDeliveryMonitor.vue', import.meta.url), 'utf8')
const broadcastPageSource = await readFile(new URL('../src/modules/admin/pages/DiscordBroadcastsPage.vue', import.meta.url), 'utf8')
const forumPageSource = await readFile(new URL('../src/modules/forum/pages/ForumDetailPage.vue', import.meta.url), 'utf8')
const forumModelSource = await readFile(new URL('../src/modules/forum/composables/useForumDetailPage.js', import.meta.url), 'utf8')
const forumApiSource = await readFile(new URL('../src/modules/forum/api/forum.js', import.meta.url), 'utf8')
const routeSource = await readFile(new URL('../src/modules/admin/routes.js', import.meta.url), 'utf8')
const adminIntegrationsStyles = readCssBundle([
  '../src/modules/admin/styles/adminWebhookHistory.css',
], import.meta.url)
const forumReplyStyles = await readFile(new URL('../src/modules/forum/styles/forumReplies.css', import.meta.url), 'utf8')

test('delivery monitor starts collapsed and supports deliberate cleanup', () => {
  assert.ok(deliverySource.includes('<details class="webhook-delivery-panel webhook-delivery-disclosure"'))
  assert.ok(!deliverySource.includes('<details open'))
  assert.ok(deliverySource.includes('confirmClearHistory'))
  assert.ok(deliverySource.includes('pendingDeliveryDeleteId'))
  assert.ok(deliverySource.includes('deleteOutboundWebhookDeliveryHistory'))
  assert.ok(adminIntegrationsStyles.includes('.webhook-delivery-disclosure'))
  assert.ok(adminIntegrationsStyles.includes('.webhook-history-delete-confirmation'))
})

test('broadcast communication is routed to its own staff subpage', () => {
  assert.ok(routeSource.includes("path: '/admin/discord-broadcasts'"))
  assert.ok(broadcastPageSource.includes('<BroadcastWebhookManagementPanel'))
  assert.ok(broadcastPageSource.includes('<DiscordBroadcastPanel'))
  assert.ok(broadcastPageSource.includes('fixed-event-type="broadcast.manual"'))
})

test('forum reply deletion has API, page model and inline confirmation', () => {
  assert.ok(forumApiSource.includes('export function deletePost(id)'))
  assert.ok(forumModelSource.includes('async function submitPostDelete'))
  assert.ok(forumModelSource.includes('pendingDeletePostId'))
  assert.ok(forumPageSource.includes('forum-post-delete-confirmation'))
  assert.ok(forumPageSource.includes("t('forum.detail.deletePostConfirmTitle')"))
  assert.ok(forumReplyStyles.includes('.forum-post-delete-confirmation'))
})
