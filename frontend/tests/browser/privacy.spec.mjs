import { expect, test } from '@playwright/test'
import { mockAnonymousApi } from './apiMocks.mjs'

test.beforeEach(async ({ page }) => {
  await mockAnonymousApi(page)
})

test('cookie settings retry a failed initial load and show the saved choice', async ({ page }) => {
  let requestCount = 0
  await page.route(/^https?:\/\/[^/]+\/api\/privacy\/cookie-consent$/, async (route) => {
    requestCount += 1
    if (requestCount === 1) {
      await route.fulfill({ status: 503, json: { detail: 'Temporarily unavailable.' } })
      return
    }
    await route.fulfill({
      json: {
        has_decision: true,
        policy_version: '2026-07-11',
        necessary: true,
        preferences: true,
        analytics: false,
        external_media: true,
      },
    })
  })

  await page.goto('/login')
  await page.getByRole('button', { name: /Cookie settings|Cookie-Einstellungen/ }).click()

  const dialog = page.getByRole('dialog', { name: /Cookie settings|Cookie-Einstellungen/ })
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('checkbox').nth(1)).toBeChecked()
  await expect(dialog.getByRole('checkbox').nth(2)).not.toBeChecked()
  await expect(dialog.getByRole('checkbox').nth(3)).toBeChecked()
  expect(requestCount).toBe(2)
})

test('cookie settings persist the explicit category choice and close after success', async ({ page }) => {
  let savedChoice
  await page.route(/^https?:\/\/[^/]+\/api\/privacy\/cookie-consent$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: { has_decision: false, necessary: true } })
      return
    }
    savedChoice = route.request().postDataJSON()
    await route.fulfill({ json: { has_decision: true, ...savedChoice, policy_version: '2026-07-11' } })
  })

  await page.goto('/login')
  await page.getByRole('button', { name: /Cookie settings|Cookie-Einstellungen/ }).click()
  const dialog = page.getByRole('dialog', { name: /Cookie settings|Cookie-Einstellungen/ })
  await dialog.getByRole('checkbox').nth(1).check()
  await dialog.getByRole('checkbox').nth(3).check()
  await dialog.getByRole('button', { name: /Save selection|Auswahl speichern/ }).click()

  await expect.poll(() => savedChoice).toEqual({
    necessary: true,
    preferences: true,
    analytics: false,
    external_media: true,
  })
  await expect(dialog).toBeHidden()
})

test('cookie settings remain open with an accessible error after a failed save', async ({ page }) => {
  await page.route(/^https?:\/\/[^/]+\/api\/privacy\/cookie-consent$/, async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: { has_decision: false, necessary: true } })
      return
    }
    await route.fulfill({ status: 503, json: { detail: 'Consent storage unavailable.' } })
  })

  await page.goto('/login')
  await page.getByRole('button', { name: /Cookie settings|Cookie-Einstellungen/ }).click()
  const dialog = page.getByRole('dialog', { name: /Cookie settings|Cookie-Einstellungen/ })
  await dialog.getByRole('button', { name: /Save selection|Auswahl speichern/ }).click()

  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('alert')).toBeVisible()
})
