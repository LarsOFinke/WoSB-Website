import { expect, test } from '@playwright/test'

test('administrator filters and creates a linked-member warehouse entry', async ({ page }) => {
  let createdPayload
  let items = []
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 7, username: 'lars', display_name: 'Lars', role: 'admin', is_active: true },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/fleets$/, (route) => route.fulfill({
    json: [{ id: 2, name: 'Royal Blackwater Fleet', slug: 'rbf', focus: 'mixed', sort_order: 1, is_active: true, created_at: '2030-01-01T00:00:00', updated_at: '2030-01-01T00:00:00' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/admin\/users/, (route) => route.fulfill({
    json: [{ id: 17, username: 'blackwater', display_name: 'Blackwater', role: 'user', is_active: true, created_at: '2030-01-01T00:00:00', fleet_id: 2 }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/admin\/warehouse(?:\?.*)?$/, async (route) => {
    if (route.request().method() === 'POST') {
      createdPayload = route.request().postDataJSON()
      items = [{
        id: 41, fleet_id: 2, fleet_name: 'Royal Blackwater Fleet', member_user_id: 17,
        custom_holder_name: null, holder_name: 'Blackwater', port: 'Nassau', resource: 'Iron',
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

  await page.goto('/admin/warehouse')
  await expect(page.getByRole('heading', { level: 1, name: 'Guild warehouse' })).toBeVisible()
  await expect(page.getByText('No warehouse entries match')).toBeVisible()
  await page.getByRole('button', { name: 'Add stock entry' }).first().click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('combobox', { name: 'Fleet', exact: true }).selectOption('2')
  await dialog.getByRole('combobox', { name: 'Linked fleet member', exact: true }).selectOption('17')
  await dialog.getByLabel('Port').fill('Nassau')
  await dialog.getByLabel('Resource').fill('Iron')
  await dialog.getByLabel('Amount').fill('1250')
  await dialog.getByRole('button', { name: 'Save entry' }).click()

  await expect(page.locator('.warehouse-table')).toContainText('Blackwater')
  await expect(page.locator('.warehouse-table')).toContainText('1,250')
  expect(createdPayload).toMatchObject({
    fleet_id: 2, member_user_id: 17, custom_holder_name: null,
    port: 'Nassau', resource: 'Iron', amount: 1250, reserved: false,
  })
})
