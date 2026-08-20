import { expect, test } from '@playwright/test'

test('moderator filters and creates a linked-member warehouse entry', async ({ page }) => {
  let createdPayload
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
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      createdPayload = route.request().postDataJSON()
      items = [{
        id: 41, fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', member_user_id: 17,
        custom_holder_name: null, holder_name: 'Blackwater', port: 'Tortuga', resource: 'Iron',
        amount: 1250, reserved: false, version: 1,
        created_at: '2030-01-15T12:00:00', updated_at: '2030-01-15T12:00:00', updated_by: 'Lars',
      }]
      await route.fulfill({ status: 201, json: items[0] })
      return
    }
    await route.fulfill({ json: {
      items, total: items.length, matching_stock: items.reduce((sum, item) => sum + item.amount, 0),
      reserved_stock: 0, available_stock: items.reduce((sum, item) => sum + item.amount, 0),
      holders: items.map((item) => item.holder_name), ports: items.map((item) => item.port),
      resources: items.map((item) => item.resource),
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
  await dialog.getByLabel('Resource').fill('Iron')
  await dialog.getByLabel('Amount').fill('1250')
  await dialog.getByRole('button', { name: 'Save entry' }).click()

  await expect(page.locator('.warehouse-table')).toContainText('Blackwater')
  await expect(page.locator('.warehouse-table')).toContainText('1,250')
  expect(createdPayload).toMatchObject({
    fleet_id: 2, member_user_id: 17, custom_holder_name: null,
    port: 'Tortuga', resource: 'Iron', amount: 1250, reserved: false,
  })
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
  await page.route(/^https?:\/\/[^/]+\/api\/warehouse(?:\?.*)?$/, (route) => route.fulfill({ json: {
    items: [{
      id: 41, fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', member_user_id: 17,
      custom_holder_name: null, holder_name: 'Blackwater', port: 'Nassau', resource: 'Iron',
      amount: 1250, reserved: false, version: 1,
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
