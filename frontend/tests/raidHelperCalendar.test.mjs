import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const createComposableUrl = new URL('../src/modules/calendar/composables/useCalendarCreatePage.js', import.meta.url)
const createPageUrl = new URL('../src/modules/calendar/pages/CalendarCreatePage.vue', import.meta.url)
const calendarPageUrl = new URL('../src/modules/calendar/pages/CalendarPage.vue', import.meta.url)
const calendarModelUrl = new URL('../src/modules/calendar/composables/useCalendarPage.js', import.meta.url)
const calendarApiUrl = new URL('../src/modules/calendar/api/calendar.js', import.meta.url)
const adminPageUrl = new URL('../src/modules/admin/pages/RaidHelperPage.vue', import.meta.url)
const adminModelUrl = new URL('../src/modules/admin/pages/useRaidHelperPage.js', import.meta.url)
const templateDomainUrl = new URL('../src/modules/admin/domain/raidHelperTemplates.js', import.meta.url)
const routesUrl = new URL('../src/modules/admin/routes.js', import.meta.url)
const robotsUrl = new URL('../public/robots.txt', import.meta.url)
const nginxUrl = new URL('../../infrastructure/nginx/default.conf', import.meta.url)

test('calendar creation enables Raid-Helper by default and submits explicit destinations', async () => {
  const source = await readFile(createComposableUrl, 'utf8')
  assert.match(source, /raidHelperEnabled:\s*true/)
  assert.match(source, /listRaidHelperOptions/)
  assert.match(source, /watch\([\s\S]*form\.category[\s\S]*form\.scope[\s\S]*form\.raidHelperEnabled/)
  assert.match(source, /raid_helper_enabled:\s*form\.raidHelperEnabled/)
  assert.match(source, /raid_helper_dispatches:/)
  assert.match(source, /destination_id:\s*Number\(destinationId\)/)
  assert.match(source, /template_id:\s*Number\(selection\.templateId\)/)
  assert.match(source, /leader_id:\s*selection\.leaderMode === 'manual'/)
})

test('calendar UI filters targets by scope/category and exposes a per-event opt-out', async () => {
  const source = await readFile(createPageUrl, 'utf8')
  assert.match(source, /v-model="form\.raidHelperEnabled"/)
  assert.match(source, /raidHelperOptions/)
  assert.match(source, /destination\.templates/)
  assert.match(source, /toggleDestination\(destination\)/)
  assert.match(source, /destination\.default_leader_id/)
  assert.match(source, /raidHelperSelections\[destination\.id\]\.leaderMode/)
  assert.match(source, /raidHelperSelections\[destination\.id\]\.leaderId/)
})

test('Raid-Helper credentials and routing are managed only in the admin workspace', async () => {
  const [page, routes] = await Promise.all([
    readFile(adminPageUrl, 'utf8'),
    readFile(routesUrl, 'utf8'),
  ])
  assert.match(routes, /path:\s*'\/admin\/raid-helper'/)
  assert.match(routes, /requiresAdmin:\s*true/)
  assert.match(page, /type="password"/)
  assert.match(page, /profileForm\.server_id/)
  assert.match(page, /profileForm\.default_leader_id/)
  assert.match(page, /destinationForm\.scope_type/)
  assert.match(page, /templateForm\.categories/)
})

test('robots policy and NGINX limits reduce crawler load beyond voluntary directives', async () => {
  const [robots, nginx] = await Promise.all([
    readFile(robotsUrl, 'utf8'),
    readFile(nginxUrl, 'utf8'),
  ])
  assert.match(robots, /User-agent: \*/)
  assert.match(robots, /Disallow: \/api\//)
  assert.match(robots, /User-agent: GPTBot[\s\S]*Disallow: \//)
  assert.match(nginx, /zone=public_pages/)
  assert.match(nginx, /zone=api_general/)
  assert.match(nginx, /\$rbf_blocked_crawler/)
  assert.match(nginx, /X-Robots-Tag "noindex, nofollow, noarchive"/)
})


test('Raid-Helper defaults use the canonical API host and advanced timezone presentation', async () => {
  const [page, pageModel, templates] = await Promise.all([
    readFile(adminPageUrl, 'utf8'),
    readFile(adminModelUrl, 'utf8'),
    readFile(templateDomainUrl, 'utf8'),
  ])
  assert.match(pageModel, /https:\/\/raid-helper\.xyz\/api\/v4/)
  assert.match(page, /raidHelper\.timezoneHelp/)
  assert.match(page, /applyRaidHelperRecommendedPayload/)
  assert.match(templates, /"date_variant": "both"/)
  assert.match(templates, /"12h_format": false/)
  assert.match(templates, /"info_variant": "long"/)
  assert.match(templates, /"preserve_order": true/)
  assert.match(templates, /"apply_unregister": true/)
})


test('failed Raid-Helper deliveries expose an explicit manager retry action', async () => {
  const [page, pageModel, api] = await Promise.all([
    readFile(calendarPageUrl, 'utf8'),
    readFile(calendarModelUrl, 'utf8'),
    readFile(calendarApiUrl, 'utf8'),
  ])
  assert.match(page, /link\.status === 'failed'/)
  assert.match(page, /retryRaidHelper\(event\)/)
  assert.match(pageModel, /retryRaidHelperEvent\(event\.id\)/)
  assert.match(api, /\/raid-helper\/retry/)
})
