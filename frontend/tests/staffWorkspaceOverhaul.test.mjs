import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const adminSource = await readFile(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')
const auditSource = await readFile(new URL('../src/modules/admin/components/AuditLogPanel.vue', import.meta.url), 'utf8')
const webhookSource = await readFile(new URL('../src/modules/admin/components/OutboundWebhookManagementPanel.vue', import.meta.url), 'utf8')
const broadcastSource = await readFile(new URL('../src/modules/admin/components/DiscordBroadcastPanel.vue', import.meta.url), 'utf8')
const discordPageSource = await readFile(new URL('../src/modules/admin/pages/DiscordWebhooksPage.vue', import.meta.url), 'utf8')
const staffOverviewSource = await readFile(new URL('../src/modules/admin/components/StaffOverviewPanel.vue', import.meta.url), 'utf8')
const stylesSource = await readFile(new URL('../src/styles/main.css', import.meta.url), 'utf8')

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
  assert.ok(webhookSource.includes('formIsReady'))
})


test('webhook editor offers compact subscriptions and repository template autofill', () => {
  for (const binding of ['templateEventKey', 'eventSearch']) {
    assert.ok(webhookSource.includes(`v-model="${binding}"`), binding)
  }
  assert.ok(webhookSource.includes('applyTemplatePreset'))
  assert.ok(webhookSource.includes('<details class="webhook-event-dropdown">'))
  assert.ok(webhookSource.includes('filteredEventGroups'))
  assert.ok(webhookSource.includes('selectVisibleEvents'))
  assert.ok(webhookSource.includes('clearMessageTemplate'))
  assert.ok(!discordPageSource.includes('webhook-template-reference'))
  assert.ok(!discordPageSource.includes('docs/webhook-templates/message-templates/'))
  assert.ok(webhookSource.includes('webhook-editor-backdrop'))
  assert.ok(webhookSource.includes('role="dialog"'))
  assert.ok(webhookSource.includes('openCreateWebhook'))
  assert.ok(stylesSource.includes('.webhook-editor-backdrop'))
})

test('system logs use expandable request rows and defer the dense security dashboard', () => {
  for (const className of ['staff-log-summary-strip', 'staff-log-list', 'staff-log-entry-details', 'staff-log-security-disclosure']) {
    assert.ok(adminSource.includes(className), className)
    assert.ok(stylesSource.includes(`.${className}`), `${className} CSS`)
  }
  assert.ok(adminSource.includes(':aria-expanded="expandedLogId === entry.id"'))
  assert.ok(!adminSource.includes('<table class="security-table staff-log-table">'))
})

test('mobile staff navigation uses one stable grouped picker instead of an overflowing tab rail', () => {
  assert.ok(adminSource.includes('staff-mobile-tab-picker'))
  assert.ok(adminSource.includes('<Teleport to="body">'))
  assert.ok(adminSource.includes('role="dialog"'))
  assert.ok(adminSource.includes('staff-mobile-tab-sheet'))
  assert.ok(adminSource.includes('selectMobileTab'))
  assert.ok(stylesSource.includes('.staff-mobile-tab-picker'))
  assert.ok(stylesSource.includes('.staff-mobile-tab-layer'))
  assert.ok(stylesSource.includes('.staff-workspace-frame > .staff-tabs {\n    display: none;'))
})

test('staff overview has dedicated responsive dashboard styling', () => {
  for (const className of [
    'staff-overview-panel', 'staff-overview-card-grid', 'staff-overview-card-copy',
    'staff-overview-queue-grid', 'staff-role-scope-note',
  ]) {
    assert.ok(staffOverviewSource.includes(className), className)
    assert.ok(stylesSource.includes(`.${className}`), `${className} CSS`)
  }
  assert.ok(stylesSource.includes('grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr))'))
})
