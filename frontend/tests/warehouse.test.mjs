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
    collection_status: 'up_for_collection',
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
    collection_status: 'up_for_collection',
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
    collection_status: 'in_warehouse',
  })

  assert.equal(draft.holder_mode, 'member')
  assert.equal(warehousePayload(draft, { updating: true }).version, 4)
  assert.equal(formatWarehouseAmount(1250, 'en'), '1,250')
})

test('warehouse is member-visible while mutations remain staff-gated', async () => {
  const [routes, page, editor, portManagement, composable, api, navigation] = await Promise.all([
    readFile(new URL('../src/modules/warehouse/routes.js', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/pages/WarehousePage.vue', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/components/WarehouseEntryEditor.vue', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/admin/components/WarehousePortManagementPanel.vue', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/composables/useWarehousePage.js', import.meta.url), 'utf8'),
    readFile(new URL('../src/modules/warehouse/api/warehouse.js', import.meta.url), 'utf8'),
    readFile(new URL('../src/core/navigation/workspaceLinks.js', import.meta.url), 'utf8'),
  ])
  assert.match(routes, /path: '\/warehouse'/)
  assert.match(routes, /requiresUser: true/)
  assert.match(page, /useWarehousePage/)
  assert.doesNotMatch(page, /\/admin\/warehouse/)
  assert.match(page, /v-if="canManageWarehouse"/)
  assert.match(editor, /v-for="port in ports"/)
  assert.doesNotMatch(editor, /draft\.port[^\n]*<input/)
  assert.match(portManagement, /listAdminWarehousePorts/)
  assert.match(composable, /canManageWarehouse/)
  assert.match(composable, /listWarehousePorts/)
  assert.match(composable, /collection_status/)
  assert.match(composable, /loadSequence/)
  assert.match(composable, /hasNextPage/)
  assert.match(composable, /err\.status === 409/)
  assert.match(composable, /createWarehouseEntry/)
  assert.match(api, /\/warehouse/)
  assert.match(api, /\/warehouse\/ports/)
  assert.match(api, /\/admin\/master-data\/warehouse-ports/)
  assert.doesNotMatch(api, /\/admin\/warehouse/)
  assert.match(navigation, /to: '\/warehouse'/)
  assert.match(page, /pageStart/)
  assert.match(page, /previousPage/)
  assert.match(page, /nextPage/)
})
