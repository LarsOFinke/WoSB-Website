import { deleteRequest, get, post, put } from '@/shared/api/client'
import { withQuery } from '@/shared/api/query'


export function getSystemUpdateStatus() {
  return get('/admin/system/update')
}

export function requestSystemUpdate(operation = 'update') {
  return post('/admin/system/update', { operation })
}

export function listRegistrationRequests({ status = 'pending', search = '', fromDate = '', toDate = '' } = {}) {
  return get(withQuery('/admin/registration-requests', {
    status,
    search,
    from_date: fromDate,
    to_date: toDate,
  }))
}

export function approveRegistrationRequest(id, note = '') {
  return post(`/admin/registration-requests/${id}/approve`, { note: note || null })
}

export function rejectRegistrationRequest(id, note = '') {
  return post(`/admin/registration-requests/${id}/reject`, { note: note || null })
}

export function listAdminBuilds(search = '', buildType = '') {
  return get(withQuery('/admin/builds', { search, build_type: buildType }))
}

export function deleteAdminBuild(id) {
  return deleteRequest(`/admin/builds/${id}`)
}

export function listBuildRoles() {
  return get('/admin/build-roles')
}

export function createBuildRole(payload) {
  return post('/admin/build-roles', payload)
}

export function updateBuildRole(slug, payload) {
  return put(`/admin/build-roles/${encodeURIComponent(slug)}`, payload)
}

export function deleteBuildRole(slug) {
  return deleteRequest(`/admin/build-roles/${encodeURIComponent(slug)}`)
}

export function assignAdminBuildRole(buildId, buildType) {
  return put(`/admin/builds/${buildId}/role`, { build_type: buildType })
}

export function listAdminForumThreads(search = '', category = '') {
  return get(withQuery('/admin/forum/threads', { search, category }))
}

export function deleteAdminForumThread(id) {
  return deleteRequest(`/admin/forum/threads/${id}`)
}

export function listAdminGuides(search = '', category = '') {
  return get(withQuery('/admin/guides', { search, category }))
}

export function deleteAdminGuide(id) {
  return deleteRequest(`/admin/guides/${id}`)
}

export function listUsers() {
  return get('/admin/users')
}

export function createModerator(payload) {
  return post('/admin/moderators', payload)
}

export function updateUser(id, payload) {
  return put(`/admin/users/${id}`, payload)
}

export function getMasterDataOverview() {
  return get('/admin/master-data/overview')
}

export function getMasterDataTaxonomy() {
  return get('/admin/master-data/taxonomy')
}

export function restoreAllMasterDataSeedDefaults() {
  return post('/admin/master-data/restore-seed-defaults', {})
}

export function listMasterDataCategories() {
  return get('/admin/master-data/categories')
}

export function createMasterDataCategory(payload) {
  return post('/admin/master-data/categories', payload)
}

export function updateMasterDataCategory(id, payload) {
  return put(`/admin/master-data/categories/${id}`, payload)
}

export function deactivateMasterDataCategory(id) {
  return deleteRequest(`/admin/master-data/categories/${id}`)
}

export function restoreMasterDataCategory(id) {
  return post(`/admin/master-data/categories/${id}/restore-seed`, {})
}

export function listMasterDataOptions({ category = '', search = '' } = {}) {
  return get(withQuery('/admin/master-data/options', { category, search }))
}

export function createMasterDataOption(payload) {
  return post('/admin/master-data/options', payload)
}

export function updateMasterDataOption(id, payload) {
  return put(`/admin/master-data/options/${id}`, payload)
}

export function deactivateMasterDataOption(id) {
  return deleteRequest(`/admin/master-data/options/${id}`)
}

export function restoreMasterDataOption(id) {
  return post(`/admin/master-data/options/${id}/restore-seed`, {})
}

export function listMasterDataShips(search = '') {
  return get(withQuery('/admin/master-data/ships', { search }))
}

export function createMasterDataShip(payload) {
  return post('/admin/master-data/ships', payload)
}

export function updateMasterDataShip(id, payload) {
  return put(`/admin/master-data/ships/${id}`, payload)
}

export function deactivateMasterDataShip(id) {
  return deleteRequest(`/admin/master-data/ships/${id}`)
}

export function restoreMasterDataShip(id) {
  return post(`/admin/master-data/ships/${id}/restore-seed`, {})
}

export function getSecurityDashboard({ fromDate = '', toDate = '', threatLevel = '', clientIp = '', sort = 'threat', limit = 100 } = {}) {
  return get(withQuery('/admin/logs/security-dashboard', {
    from_date: fromDate,
    to_date: toDate,
    threat_level: threatLevel,
    client_ip: clientIp,
    sort,
    limit,
  }))
}

export function listAuditLogs({ entityType = '', action = '', actor = '', fromDate = '', toDate = '', limit = 200 } = {}) {
  return get(withQuery('/admin/audit-logs', {
    entity_type: entityType,
    action,
    actor,
    from_date: fromDate,
    to_date: toDate,
    limit,
  }))
}

export function listIpBlocks({ status = 'active', search = '', limit = 200 } = {}) {
  return get(withQuery('/admin/ip-blocks', { status, search, limit }))
}

export function getIpBlockSummary() {
  return get('/admin/ip-blocks/summary')
}

export function createIpBlock(payload) {
  return post('/admin/ip-blocks', payload)
}

export function unblockIpBlock(id, reason = '') {
  return post(`/admin/ip-blocks/${id}/unblock`, { reason: reason || null })
}


export function listBroadcastWebhookTargets() {
  return get('/admin/discord-webhooks/broadcast/targets')
}

export function sendDiscordBroadcast(payload) {
  return post('/admin/discord-webhooks/broadcast/send', payload)
}

export function listOutboundWebhookEvents() {
  return get('/admin/discord-webhooks/events')
}

export function getOutboundWebhookSummary(purpose = '') {
  return get(withQuery('/admin/discord-webhooks/summary', { purpose }))
}

export function listOutboundWebhooks(purpose = '') {
  return get(withQuery('/admin/discord-webhooks', { purpose }))
}

export function createOutboundWebhook(payload) {
  return post('/admin/discord-webhooks', payload)
}

export function updateOutboundWebhook(id, payload) {
  return put(`/admin/discord-webhooks/${id}`, payload)
}

export function testOutboundWebhook(id, eventType = 'integration.test') {
  return post(`/admin/discord-webhooks/${id}/test`, { event_type: eventType })
}

export function deleteOutboundWebhook(id) {
  return deleteRequest(`/admin/discord-webhooks/${id}`)
}

export function listOutboundWebhookDeliveries({ webhookId = '', status = '', eventType = '', limit = 100 } = {}) {
  return get(withQuery('/admin/discord-webhooks/deliveries/history', {
    webhook_id: webhookId,
    status,
    event_type: eventType,
    limit,
  }))
}

export function deleteOutboundWebhookDelivery(id) {
  return deleteRequest(`/admin/discord-webhooks/deliveries/${id}`)
}

export function deleteOutboundWebhookDeliveryHistory({ webhookId = '', status = '', eventType = '' } = {}) {
  return deleteRequest(withQuery('/admin/discord-webhooks/deliveries/history', {
    webhook_id: webhookId,
    status,
    event_type: eventType,
  }))
}

export function retryOutboundWebhookDelivery(id) {
  return post(`/admin/discord-webhooks/deliveries/${id}/retry`, {})
}

export function getBackupControlStatus() {
  return get('/admin/backups/status')
}

export function discoverBackupHost(payload) {
  return post('/admin/backups/discover', payload)
}

export function configureBackupConnection(payload) {
  return put('/admin/backups/configuration', payload)
}

export function testBackupConnection() {
  return post('/admin/backups/test', {})
}

export function runDatabaseBackup() {
  return post('/admin/backups/run', {})
}

export function deleteBackupConnection() {
  return deleteRequest('/admin/backups/configuration')
}

export function listRaidHelperProfiles() {
  return get('/admin/raid-helper/profiles')
}

export function createRaidHelperProfile(payload) {
  return post('/admin/raid-helper/profiles', payload)
}

export function updateRaidHelperProfile(id, payload) {
  return put(`/admin/raid-helper/profiles/${id}`, payload)
}

export function deleteRaidHelperProfile(id) {
  return deleteRequest(`/admin/raid-helper/profiles/${id}`)
}

export function testRaidHelperProfile(id) {
  return post(`/admin/raid-helper/profiles/${id}/test`, {})
}

export function listRaidHelperDestinations() {
  return get('/admin/raid-helper/destinations')
}

export function createRaidHelperDestination(payload) {
  return post('/admin/raid-helper/destinations', payload)
}

export function updateRaidHelperDestination(id, payload) {
  return put(`/admin/raid-helper/destinations/${id}`, payload)
}

export function deleteRaidHelperDestination(id) {
  return deleteRequest(`/admin/raid-helper/destinations/${id}`)
}

export function listRaidHelperTemplates() {
  return get('/admin/raid-helper/templates')
}

export function createRaidHelperTemplate(payload) {
  return post('/admin/raid-helper/templates', payload)
}

export function updateRaidHelperTemplate(id, payload) {
  return put(`/admin/raid-helper/templates/${id}`, payload)
}

export function deleteRaidHelperTemplate(id) {
  return deleteRequest(`/admin/raid-helper/templates/${id}`)
}
