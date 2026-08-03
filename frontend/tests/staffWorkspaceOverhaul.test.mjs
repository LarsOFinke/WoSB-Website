import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { readGlobalStyles } from './helpers/readGlobalStyles.mjs'
import { readCssBundle } from './helpers/readCssBundle.mjs'

const adminSource = await readFile(new URL('../src/modules/admin/pages/AdminPage.vue', import.meta.url), 'utf8')
const systemLogSource = await readFile(new URL('../src/modules/admin/components/SystemLogPanel.vue', import.meta.url), 'utf8')
const auditSource = await readFile(new URL('../src/modules/admin/components/AuditLogPanel.vue', import.meta.url), 'utf8')
const webhookSource = await readFile(new URL('../src/modules/admin/components/OutboundWebhookManagementPanel.vue', import.meta.url), 'utf8')
const broadcastSource = await readFile(new URL('../src/modules/admin/components/DiscordBroadcastPanel.vue', import.meta.url), 'utf8')
const broadcastManagementSource = await readFile(new URL('../src/modules/admin/components/BroadcastWebhookManagementPanel.vue', import.meta.url), 'utf8')
const deliveryMonitorSource = await readFile(new URL('../src/modules/admin/components/WebhookDeliveryMonitor.vue', import.meta.url), 'utf8')
const broadcastPageSource = await readFile(new URL('../src/modules/admin/pages/DiscordBroadcastsPage.vue', import.meta.url), 'utf8')
const discordPageSource = await readFile(new URL('../src/modules/admin/pages/DiscordWebhooksPage.vue', import.meta.url), 'utf8')
const masterDataPageSource = await readFile(new URL('../src/modules/admin/pages/MasterDataPage.vue', import.meta.url), 'utf8')
const filterSurfaceSource = await readFile(new URL('../src/modules/admin/components/StaffFilterSurface.vue', import.meta.url), 'utf8')
const staffOverviewSource = await readFile(new URL('../src/modules/admin/components/StaffOverviewPanel.vue', import.meta.url), 'utf8')
const navigationSource = await readFile(new URL('../src/modules/admin/components/StaffWorkspaceNavigation.vue', import.meta.url), 'utf8')
const shellSource = await readFile(new URL('../src/modules/admin/components/StaffWorkspaceShell.vue', import.meta.url), 'utf8')
const staffStylesSource = readCssBundle([
  '../src/modules/admin/styles/staffWorkspaceShell.css',
  '../src/modules/admin/styles/staffWorkspaceOverview.css',
  '../src/modules/admin/styles/staffWorkspaceResponsive.css',
  '../src/modules/admin/styles/staffSecurityWorkspace.css',
], import.meta.url)
const adminIntegrationsSource = readCssBundle([
  '../src/modules/admin/styles/adminWebhookConfiguration.css',
  '../src/modules/admin/styles/adminWebhookEditorDrawer.css',
], import.meta.url)
const navigationDomainSource = await readFile(new URL('../src/modules/admin/domain/staffNavigation.js', import.meta.url), 'utf8')
const stylesSource = `${readGlobalStyles()}\n${staffStylesSource}\n${adminIntegrationsSource}`

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


test('staff filters use one reusable presentational surface', () => {
  assert.equal((adminSource.match(/<StaffFilterSurface/g) || []).length, 5)
  assert.ok(filterSurfaceSource.includes('<slot />'))
  assert.ok(filterSurfaceSource.includes('<slot name="actions">'))
  assert.ok(filterSurfaceSource.includes("defineEmits(['reset'])"))
})

test('audit history includes newly introduced administrative entity types', () => {
  for (const entity of ['registration_request', 'user_account', 'fleet_membership', 'ip_block', 'app_log', 'outbound_webhook', 'master_data']) {
    assert.ok(auditSource.includes(`value="${entity}"`), entity)
  }
})

test('website webhook management and delivery history remain focused and filterable', () => {
  for (const binding of ['webhookSearch', 'webhookState', 'form.scope_type']) {
    assert.ok(webhookSource.includes(`v-model="${binding}"`), binding)
  }
  for (const binding of ['deliveryWebhook', 'deliveryStatus', 'deliveryEvent']) {
    assert.ok(deliveryMonitorSource.includes(`v-model="${binding}"`), binding)
  }
  assert.ok(webhookSource.includes("row.event_types[0] || 'integration.test'"))
  assert.ok(webhookSource.includes(':events="events"'))
  assert.ok(deliveryMonitorSource.includes('<details class="webhook-delivery-panel webhook-delivery-disclosure"'))
  assert.ok(!deliveryMonitorSource.includes('<details open'))
  assert.ok(deliveryMonitorSource.includes('deleteOutboundWebhookDeliveryHistory'))
  assert.ok(deliveryMonitorSource.includes('deleteOutboundWebhookDelivery'))
})


test('Discord broadcasts have a separate workspace and target administration', () => {
  for (const binding of ['form.webhook_ids', 'form.message', 'form.discord_username']) {
    assert.ok(broadcastSource.includes(binding), binding)
  }
  assert.ok(!broadcastSource.includes('form.discord_avatar_url'))
  assert.ok(!broadcastManagementSource.includes('form.discord_avatar_url'))
  assert.ok(!webhookSource.includes('form.discord_avatar_url'))
  assert.ok(broadcastSource.includes('listBroadcastWebhookTargets'))
  assert.ok(broadcastSource.includes('sendDiscordBroadcast'))
  assert.ok(broadcastManagementSource.includes("listOutboundWebhooks('broadcast')"))
  assert.ok(broadcastManagementSource.includes('broadcast_enabled: true'))
  assert.ok(broadcastManagementSource.includes('sharedWithAutomation'))
  assert.ok(broadcastManagementSource.includes('broadcast_enabled: false'))
  assert.ok(broadcastPageSource.includes('<BroadcastWebhookManagementPanel'))
  assert.ok(broadcastPageSource.includes('<DiscordBroadcastPanel'))
  assert.ok(broadcastPageSource.includes('fixed-event-type="broadcast.manual"'))
  assert.ok(!discordPageSource.includes('<DiscordBroadcastPanel'))
  assert.ok(!webhookSource.includes('v-model="form.broadcast_enabled"'))
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
  assert.ok(!discordPageSource.includes('docs/integrations/webhook-templates/message-templates/'))
  assert.ok(webhookSource.includes('webhook-editor-backdrop'))
  assert.ok(webhookSource.includes('role="dialog"'))
  assert.ok(webhookSource.includes('openCreateWebhook'))
  assert.ok(webhookSource.includes('Moderation inbox'))
  assert.ok(webhookSource.includes('Operations audit'))
  assert.ok(webhookSource.includes('Calendar shoutouts'))
  assert.ok(webhookSource.includes('applyChannelPreset'))
  assert.ok(stylesSource.includes('.webhook-editor-backdrop'))
})

test('IP-ban candidates use a dedicated purpose-limited panel without raw request logs', () => {
  assert.ok(adminSource.includes('<SystemLogPanel'))
  assert.ok(systemLogSource.includes('security-privacy-notice'))
  assert.ok(systemLogSource.includes('<SecurityLogDashboard'))
  assert.ok(stylesSource.includes('.security-privacy-notice'))
  assert.ok(!systemLogSource.includes('staff-log-list'))
  assert.ok(!systemLogSource.includes('expandedLogId'))
  assert.ok(!systemLogSource.includes('logIncludeBlocked'))
  assert.ok(!systemLogSource.includes('deleteFilteredLogs'))
  assert.ok(!systemLogSource.includes('deleteLogEntry'))
})

test('all staff routes share one stable grouped navigation shell', () => {
  assert.ok(adminSource.includes('<StaffWorkspaceShell'))
  assert.ok(discordPageSource.includes('<StaffWorkspaceShell'))
  assert.ok(broadcastPageSource.includes('<StaffWorkspaceShell'))
  assert.ok(masterDataPageSource.includes('<StaffWorkspaceShell'))
  assert.ok(shellSource.includes('<StaffWorkspaceNavigation'))
  assert.ok(navigationSource.includes('<Teleport to="body">'))
  assert.ok(navigationSource.includes('role="dialog"'))
  assert.ok(navigationSource.includes('staff-navigation-mobile-panel'))
  assert.ok(staffStylesSource.includes('.staff-navigation-trigger'))
  assert.ok(staffStylesSource.includes('.staff-navigation-mobile-layer'))
  assert.ok(navigationDomainSource.includes("key: 'master-data'"))
  assert.ok(navigationDomainSource.includes("key: 'webhooks'"))
  assert.ok(navigationDomainSource.includes("key: 'broadcasts'"))
})

test('staff overview prioritizes work and uses compact responsive metric bands', () => {
  for (const className of [
    'staff-overview-panel', 'staff-priority-board', 'staff-priority-row',
    'staff-overview-metric-band', 'staff-role-scope-note',
  ]) {
    assert.ok(staffOverviewSource.includes(className), className)
    assert.ok(stylesSource.includes(`.${className}`), `${className} CSS`)
  }
  assert.ok(staffStylesSource.includes('grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr))'))
  assert.ok(staffStylesSource.includes('@media (max-width: 480px)'))
})
