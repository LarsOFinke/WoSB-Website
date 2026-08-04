import { expect, test } from '@playwright/test'

async function mockAnonymousApi(page) {
  await page.route(/^https?:\/\/[^/]+\/api\//, async (route) => {
    const url = new URL(route.request().url())
    if (url.pathname === '/api/auth/me') {
      await route.fulfill({ json: null })
      return
    }
    if (url.pathname === '/api/fleets/public/official') {
      await route.fulfill({ json: { id: 1, name: 'Royal Blackwater Fleet' } })
      return
    }
    await route.fulfill({ status: 404, json: { detail: 'Not available in browser smoke test.' } })
  })
}

test.beforeEach(async ({ page }) => {
  await mockAnonymousApi(page)
})

test('login page supports skip navigation and semantic form controls', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('input[autocomplete="username"]')).toBeVisible()
  await expect(page.locator('input[autocomplete="current-password"]')).toBeVisible()

  await page.keyboard.press('Tab')
  const skipLink = page.locator('a.skip-link')
  await expect(skipLink).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('#main-content')).toBeFocused()
})

test('protected member navigation redirects an anonymous visitor to login', async ({ page }) => {
  await page.goto('/profile')

  await expect(page).toHaveURL(/\/login\?redirect=\/profile$/)
  await expect(page.locator('form input[autocomplete="username"]')).toBeVisible()
})

test('registration submits the browser payload and exposes its success state', async ({ page }) => {
  let registrationPayload
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/register$/, async (route) => {
    registrationPayload = route.request().postDataJSON()
    await route.fulfill({ status: 202, json: { request: { id: 17, wants_fleet_membership: true } } })
  })

  await page.goto('/register')
  await page.locator('input[autocomplete="username"]').fill('browser-smoke-user')
  await page.locator('input[autocomplete="nickname"]').fill('Browser Smoke User')
  await page.locator('input[autocomplete="new-password"]').fill('Browser-Smoke-Password-42!')
  await page.locator('input[type="checkbox"]').check()
  await page.locator('textarea').fill('Existing fleet member.')
  await page.locator('button[type="submit"]').click()

  await expect(page.locator('.registration-review-panel')).toBeVisible()
  expect(registrationPayload).toMatchObject({
    username: 'browser-smoke-user',
    display_name: 'Browser Smoke User',
    wants_fleet_membership: true,
    fleet_id: 1,
  })
})

test('mobile navigation opens through its accessible control', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/login')

  const menuButton = page.locator('button[aria-controls="workspace-sidebar"]')
  await menuButton.click()
  await expect(menuButton).toHaveAttribute('aria-expanded', 'true')
  await expect(page.locator('#workspace-sidebar')).toHaveClass(/is-open/)
})
