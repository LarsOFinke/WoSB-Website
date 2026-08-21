import { expect, test } from '@playwright/test'
import { mockAnonymousApi } from './apiMocks.mjs'

test.beforeEach(async ({ page }) => {
  await mockAnonymousApi(page)
})

test('moderator filters and creates a linked-member warehouse entry', async ({ page }) => {
  let createdPayload
  let assignmentPayload
  let items = []
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 7, username: 'quartermaster', display_name: 'Quartermaster', role: 'moderator', is_active: true },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/fleets$/, (route) => route.fulfill({
    json: [{ id: 2, name: 'Royal Blackwater Fleet', slug: 'rbf', focus: 'mixed', sort_order: 1, is_active: true, created_at: '2030-01-01T00:00:00', updated_at: '2030-01-01T00:00:00' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/fleets\/2\/manage$/, (route) => route.fulfill({
    json: { id: 2, memberships: [{ status: 'active', user: { id: 17, username: 'blackwater', display_name: 'Blackwater', role: 'user' } }] },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/ports$/, (route) => route.fulfill({
    json: [{ id: 1, name: 'Tortuga', sort_order: 10, is_active: true, created_at: '2030-01-01T00:00:00', updated_at: '2030-01-01T00:00:00' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/resources$/, (route) => route.fulfill({
    json: ['Battlemark', 'Captives', 'Coal', 'Construction License', 'Iron', 'Sailcloth', 'Wood'],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/port-assignments\?fleet_id=2$/, (route) => route.fulfill({
    json: [{ fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', port_id: 1, port_name: 'Tortuga', assignee_user_id: null, assignee_name: null, updated_at: '2030-01-01T00:00:00' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse(?:\/\d+)?(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      createdPayload = route.request().postDataJSON()
      items = [{
        id: 41, fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', member_user_id: 17,
        custom_holder_name: null, holder_name: 'Blackwater', port: 'Tortuga', resource: 'Iron',
        amount: 1250, reserved: false, collection_status: 'up_for_collection', version: 1,
        created_at: '2030-01-15T12:00:00', updated_at: '2030-01-15T12:00:00', updated_by: 'Lars',
      }]
      await route.fulfill({ status: 201, json: items[0] })
      return
    }
    if (route.request().method() === 'PUT') {
      await route.fulfill({ status: 409, json: { detail: 'Warehouse entry changed; reload before saving again.' } })
      return
    }
    await route.fulfill({ json: {
      items, total: items.length, matching_stock: items.reduce((sum, item) => sum + item.amount, 0),
      reserved_stock: 0, available_stock: items.reduce((sum, item) => sum + item.amount, 0),
      holders: items.map((item) => item.holder_name), ports: items.map((item) => item.port),
      resources: ['Iron'],
    } })
  })

  await page.goto('/warehouse')
  await expect(page.getByRole('heading', { level: 1, name: 'Guild warehouse' })).toBeVisible()
  await expect(page.getByText('No warehouse entries match')).toBeVisible()
  await page.getByRole('button', { name: 'Add stock entry' }).first().click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('combobox', { name: 'Fleet', exact: true }).selectOption('2')
  await dialog.getByRole('combobox', { name: 'Linked fleet member', exact: true }).selectOption('17')
  await dialog.getByRole('combobox', { name: 'Port' }).selectOption('Tortuga')
  await dialog.getByLabel('Resource').selectOption('Iron')
  await dialog.getByLabel('Amount').fill('1250')
  await dialog.getByRole('button', { name: 'Save entry' }).click()

  await expect(page.locator('.warehouse-table')).toContainText('Blackwater')
  await expect(page.locator('.warehouse-table')).toContainText('1,250')
  expect(createdPayload).toMatchObject({
    fleet_id: 2, member_user_id: 17, custom_holder_name: null,
    port: 'Tortuga', resource: 'Iron', amount: 1250, reserved: false,
    collection_status: 'up_for_collection',
  })

  await page.getByRole('button', { name: 'Edit' }).click()
  await page.getByRole('dialog').getByRole('button', { name: 'Save entry' }).click()
  await expect(page.getByRole('alert')).toContainText('changed in another staff session')
  await expect(page.getByRole('dialog')).toBeHidden()

  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/port-assignments\/1$/, async (route) => {
    assignmentPayload = route.request().postDataJSON()
    await route.fulfill({ json: { fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', port_id: 1, port_name: 'Tortuga', assignee_user_id: 17, assignee_name: 'Blackwater', updated_at: '2030-01-15T12:00:00' } })
  })
  await page.getByRole('button', { name: 'Manage pickup assignments' }).click()
  const assignmentDialog = page.getByRole('dialog', { name: 'Port pickup assignments' })
  await expect(assignmentDialog).toBeVisible()
  await assignmentDialog.locator('select').nth(1).selectOption('17')
  await expect.poll(() => assignmentPayload).toMatchObject({ fleet_id: 2, assignee_user_id: 17 })
  await assignmentDialog.getByRole('button', { name: 'Close', exact: true }).last().click()
  await expect(assignmentDialog).toBeHidden()
})

test('ordinary member can browse warehouse without mutation controls', async ({ page }) => {
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 8, username: 'member', display_name: 'Fleet Member', role: 'user', is_active: true },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/fleets$/, (route) => route.fulfill({
    json: [{ id: 2, name: 'Royal Blackwater Fleet', slug: 'rbf', focus: 'mixed', sort_order: 1, is_active: true, created_at: '2030-01-01T00:00:00', updated_at: '2030-01-01T00:00:00' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/ports$/, (route) => route.fulfill({
    json: [{ id: 1, name: 'Tortuga', sort_order: 10, is_active: true, created_at: '2030-01-01T00:00:00', updated_at: '2030-01-01T00:00:00' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/resources$/, (route) => route.fulfill({
    json: ['Battlemark', 'Captives', 'Coal', 'Construction License', 'Iron', 'Sailcloth', 'Wood'],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse(?:\?.*)?$/, (route) => route.fulfill({ json: {
    items: [{
      id: 41, fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', member_user_id: 17,
      custom_holder_name: null, holder_name: 'Blackwater', port: 'Nassau', resource: 'Iron',
      amount: 1250, reserved: false, collection_status: 'in_warehouse', version: 1,
      created_at: '2030-01-15T12:00:00', updated_at: '2030-01-15T12:00:00', updated_by: 'Quartermaster',
    }],
    total: 1, matching_stock: 1250, reserved_stock: 0, available_stock: 1250,
    holders: ['Blackwater'], ports: ['Nassau'], resources: ['Iron'],
  } }))

  await page.goto('/warehouse')

  await expect(page.getByRole('heading', { level: 1, name: 'Guild warehouse' })).toBeVisible()
  await expect(page.locator('.warehouse-table')).toContainText('Blackwater')
  await expect(page.getByRole('button', { name: 'Add stock entry' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Edit' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Delete' })).toHaveCount(0)
})

test('warehouse collection filters and pagination stay in sync with the API', async ({ page }) => {
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 8, username: 'member', display_name: 'Fleet Member', role: 'user', is_active: true },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/fleets$/, (route) => route.fulfill({
    json: [{ id: 2, name: 'Royal Blackwater Fleet', is_active: true }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/ports$/, (route) => route.fulfill({ json: [] }))
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse\/resources$/, (route) => route.fulfill({ json: [] }))
  const requests = []
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse(?:\?.*)?$/, (route) => {
    const url = new URL(route.request().url())
    requests.push(url.search)
    const offset = Number(url.searchParams.get('offset') || 0)
    const items = Array.from({ length: offset ? 1 : 100 }, (_, index) => ({
      id: offset + index + 1, fleet_id: 2, fleet_name: 'Royal Blackwater Fleet',
      member_user_id: null, custom_holder_name: 'Quartermaster', holder_name: 'Quartermaster',
      port: 'Tortuga', resource: 'Iron', amount: 1, reserved: false,
      collection_status: url.searchParams.get('collection_status') || 'in_warehouse', version: 1,
      created_at: '2030-01-15T12:00:00', updated_at: '2030-01-15T12:00:00', updated_by: 'Quartermaster',
    }))
    return route.fulfill({ json: {
      items, total: 101, matching_stock: 101, reserved_stock: 0, available_stock: 101,
      holders: ['Quartermaster'], ports: ['Tortuga'], resources: ['Iron'],
    } })
  })

  await page.goto('/warehouse')
  await page.getByLabel('Collection status').selectOption('in_warehouse')
  await expect.poll(() => requests.at(-1)).toContain('collection_status=in_warehouse')
  await expect(page.getByRole('button', { name: 'Next' })).toBeEnabled()
  await page.getByRole('button', { name: 'Next' }).click()
  await expect.poll(() => requests.at(-1)).toContain('offset=100')
  await expect(page.getByText('101 / 101')).toBeVisible()
})
