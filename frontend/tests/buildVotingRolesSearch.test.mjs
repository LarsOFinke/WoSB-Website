import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import { filterOptionGroups } from '../src/modules/builds/domain/optionSearch.js'

const read = (path) => readFile(new URL(path, import.meta.url), 'utf8')

test('specialist filtering is immediate and operates on preloaded options', () => {
  const groups = [{ key: 'specialists', options: [
    { value: 'Doctor', label: 'Doctor', meta: 'Survivability' },
    { value: 'First Mate', label: 'First Mate', meta: 'Sails' },
  ] }]
  assert.deepEqual(filterOptionGroups(groups, 'doc')[0].options.map((row) => row.value), ['Doctor'])
  assert.deepEqual(filterOptionGroups(groups, 'sails')[0].options.map((row) => row.value), ['First Mate'])
})

test('build voting is exposed in API, detail and overview', async () => {
  const [api, detail, table] = await Promise.all([
    read('../src/modules/builds/api/builds.js'),
    read('../src/modules/builds/pages/BuildDetailPage.vue'),
    read('../src/modules/builds/components/BuildResultTable.vue'),
  ])
  assert.match(api, /\/builds\/\$\{id\}\/upvote/)
  assert.match(detail, /toggleUpvote/)
  assert.match(detail, /build\.upvote_count/)
  assert.match(table, /row\.upvotes/)
})

test('moderators receive build role CRUD and assignment controls', async () => {
  const [api, page] = await Promise.all([
    read('../src/modules/admin/api/admin.js'),
    read('../src/modules/admin/pages/AdminPage.vue'),
  ])
  assert.match(api, /\/admin\/build-roles/)
  assert.match(api, /\/admin\/builds\/\$\{buildId\}\/role/)
  assert.match(page, /submitBuildRole/)
  assert.match(page, /changeBuildRole/)
  assert.match(page, /v-for="role in buildRoles"/)
})

test('planner dropdowns raise their parent stacking context without covering dialogs', async () => {
  const css = await read('../src/modules/builds/styles/buildOptionPicker.css')
  assert.match(css, /:has\(\.build-option-picker\.is-open\)/)
  assert.match(css, /z-index: 70/)
  assert.match(css, /z-index: 110/)
})
