import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

import {
  createWarehouseDraft,
  formatWarehouseAmount,
  warehouseDraftFromEntry,
  warehouseDraftIssue,
  warehousePayload,
} from '../src/modules/warehouse/domain/warehouse.js'

test('warehouse drafts enforce one holder source and integral bounded stock', () => {
  const draft = createWarehouseDraft(2)
  assert.equal(warehouseDraftIssue(draft), 'member')

  Object.assign(draft, {
    holder_mode: 'custom',
    custom_holder_name: ' Blackwater ',
    port: ' Nassau ',
    resource: ' Iron ',
    amount: 1250,
    reserved: true,
  })

  assert.equal(warehouseDraftIssue(draft), '')
  assert.deepEqual(warehousePayload(draft), {
    fleet_id: 2,
    member_user_id: null,
    custom_holder_name: 'Blackwater',
    port: 'Nassau',
    resource: 'Iron',
    amount: 1250,
    reserved: true,
  })
})

test('existing entries retain optimistic versions in update payloads', () => {
  const draft = warehouseDraftFromEntry({
    fleet_id: 2,
    member_user_id: 17,
    custom_holder_name: null,
    port: 'Nassau',
    resource: 'Iron',
    amount: 650,
    reserved: false,
    version: 4,
  })

  assert.equal(draft.holder_mode, 'member')
  assert.equal(warehousePayload(draft, { updating: true }).version, 4)
  assert.equal(formatWarehouseAmount(1250, 'en'), '1,250')
})

test('warehouse route is administrator-only and pages delegate flows to a composable', async () => {
  const [routes, page, composable, api] = await Promise.all([
    readFile(new URL('../src/modules/warehouse/routes.js', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/pages/WarehousePage.vue', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/composables/useWarehousePage.js', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/api/warehouse.js', import.meta.url), 'utf8'),
  ])
  assert.match(routes, /requiresAdmin: true/)
  assert.match(page, /useWarehousePage/)
  assert.doesNotMatch(page, /\/admin\/warehouse/)
  assert.match(composable, /createWarehouseEntry/)
  assert.match(api, /\/admin\/warehouse/)
})
