import { expect, test } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { mockAnonymousApi } from './apiMocks.mjs'

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

test('published Impressum presents the maintained public repository as a transparency signal', async ({ page }) => {
  await page.route(/^https?:\/\/[^/]+\/api\/legal-notice$/, (route) => route.fulfill({
    json: {
      published: true,
      provider_name: 'Community Project',
      street: 'Harbor Street 1',
      postal_code: '12345',
      city: 'Port Royal',
      country: 'Deutschland',
      email: 'crew@example.invalid',
      public_repository_url: 'https://github.com/example/community-project',
      updated_at: '2030-01-15T12:00:00',
    },
  }))

  await page.goto('/impressum')

  const repository = page.locator('.legal-notice-repository')
  await expect(repository).toContainText('Open development and continuity')
  await expect(repository).toContainText('independently of any single operator')
  await expect(repository.getByRole('link', { name: /View public repository/ }))
    .toHaveAttribute('href', 'https://github.com/example/community-project')
})

test('moderators organize the New Captain Guide through an ordered folder browser', async ({ page }) => {
  let savedPayload
  const guide = {
    id: 1,
    title: 'New Captain Guide',
    intro: 'Start here.',
    updated_at: '2030-01-15T12:00:00',
    updated_by: 'Moderator',
    blocks: [
      { id: 10, block_type: 'text', title: 'Welcome aboard', body: 'Read this first.', resources: [] },
      { id: 11, block_type: 'resources', title: 'Ready your ship', body: 'Choose a proven setup.', resources: [
        { id: 30, resource_type: 'internal', resource_id: null, label: 'Build library', description: 'Browse proven fleet builds.', href: '/builds', available: true },
      ] },
    ],
  }
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 8, username: 'moderator', display_name: 'Moderator', role: 'moderator' },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/newcomer-guide$/, async (route) => {
    if (route.request().method() === 'PUT') {
      savedPayload = route.request().postDataJSON()
      await route.fulfill({ json: {
        ...guide,
        blocks: savedPayload.blocks.map((block, index) => ({
          id: 20 + index,
          ...block,
          resources: block.resources.map((resource, resourceIndex) => ({
            id: 40 + resourceIndex,
            ...resource,
            href: resource.url || '/builds',
            available: true,
          })),
        })),
      } })
      return
    }
    await route.fulfill({ json: guide })
  })
  await page.route(/^https?:\/\/[^/]+\/api\/guides/, (route) => route.fulfill({ json: [] }))
  await page.route(/^https?:\/\/[^/]+\/api\/builds/, (route) => route.fulfill({ json: { items: [], total: 0 } }))

  await page.goto('/new-captain')
  await expect(page.getByRole('navigation', { name: 'Guide folders' })).toBeVisible()
  await expect(page.locator('.newcomer-explorer-address')).toContainText('New Captain Guide')
  await expect(page.locator('.newcomer-topic-card')).toHaveCount(2)
  await page.locator('.newcomer-explorer-search input').fill('Ready')
  await expect(page.locator('.newcomer-topic-card')).toHaveCount(1)
  await expect(page.locator('.newcomer-topic-card')).toContainText('Ready your ship')
  await page.locator('.newcomer-explorer-search input').fill('')
  await page.locator('.newcomer-topic-card').filter({ hasText: 'Ready your ship' }).click()
  await expect(page.locator('.newcomer-folder-content')).toContainText('Choose a proven setup.')
  await expect(page.locator('.newcomer-folder-content')).not.toContainText('Read this first.')
  await expect(page.locator('.newcomer-resource-row')).toContainText('Build library')
  await expect(page.locator('.newcomer-resource-row')).toContainText('Browse proven fleet builds.')
  await expect(page.locator('.newcomer-topic-progress')).toContainText('Welcome aboard')
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.locator('.newcomer-mobile-topic-picker')).toBeVisible()
  await expect(page.locator('.newcomer-explorer-workspace > .newcomer-folder-navigation')).toBeHidden()
  const mobileReaderBox = await page.locator('.newcomer-reader').boundingBox()
  expect(mobileReaderBox.width).toBeLessThanOrEqual(390)
  await page.setViewportSize({ width: 1440, height: 900 })

  await page.getByRole('button', { name: 'Edit guide' }).click()
  await expect(page.locator('.newcomer-folder-editor')).toHaveCount(1)
  await expect(page.locator('.newcomer-editor-workspace')).toBeVisible()
  const resourceEditor = page.locator('.newcomer-resource-editor-row')
  await expect(resourceEditor).not.toHaveAttribute('open', '')
  await resourceEditor.locator('summary').click()
  await expect(resourceEditor).toHaveAttribute('open', '')
  const secondFolder = page.locator('.newcomer-folder-list__item').nth(1)
  await secondFolder.getByRole('button', { name: 'Move folder up' }).click()
  await page.getByRole('button', { name: 'Save', exact: true }).click()

  await expect.poll(() => savedPayload?.blocks.map((block) => block.title)).toEqual(['Ready your ship', 'Welcome aboard'])
  await expect(page.locator('.newcomer-folder-list__item .newcomer-folder-entry').first()).toContainText('Ready your ship')
})

test('strategy planner keeps the chart separate and saves website-backed markers without a player', async ({ page }) => {
  const browserErrors = []
  page.on('pageerror', (error) => browserErrors.push(error.message))
  const publicId = '4f30d366-5d04-4bc1-ae1a-4df5b88c0834'
  let savedPayload
  let published = false
  const background = {
    id: 9, owner_id: 7, original_name: 'harbor.png', stored_name: 'harbor.png',
    relative_path: 'strategy/7/harbor.png', public_url: '/api/files/9/content',
    mime_type: 'image/png', size_bytes: 68, usage_context: 'strategy',
    is_public: false, created_at: '2030-01-15T12:00:00',
  }
  const strategyResponse = () => ({
    id: 41, owner_id: 7, ...savedPayload, public_id: publicId, is_published: published,
    background_file: { ...background, is_public: published },
    created_at: '2030-01-15T12:00:00', updated_at: '2030-01-15T12:10:00',
    published_at: published ? '2030-01-15T12:10:00' : null,
  })

  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 7, username: 'planner', display_name: 'Planner', role: 'moderator' },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/ships$/, (route) => route.fulfill({
    json: [{ id: 11, name: 'Leopard', ship_type: 'Frigate', rate: 3 }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/builds\?/, (route) => route.fulfill({
    json: { items: [
      { id: 21, build_name: 'Boarding Leopard', ship: { id: 11, name: 'Leopard' } },
      { id: 22, build_name: 'Wrong ship build', ship: { id: 12, name: 'Brig' } },
    ], total: 2 },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/guides\?/, (route) => route.fulfill({
    json: [{ id: 31, title: 'Eastern harbor approach' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/files\?usage_context=strategy$/, (route) => route.fulfill({ json: background }))
  await page.route(/^https?:\/\/[^/]+\/api\/files\/9\/content$/, (route) => route.fulfill({
    contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500"><rect width="800" height="500" fill="#16324a"/></svg>',
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/strategies$/, async (route) => {
    savedPayload = route.request().postDataJSON()
    await route.fulfill({ status: 201, json: strategyResponse() })
  })
  await page.route(/^https?:\/\/[^/]+\/api\/strategies\/41\/publication$/, async (route) => {
    published = true
    await route.fulfill({ json: strategyResponse() })
  })

  await page.goto('/strategies/new')
  const commandSections = page.locator('.strategy-command-section')
  await expect(commandSections).toHaveCount(4)
  await expect(page.locator('.strategy-setup-field')).toHaveCount(3)
  await expect(page.locator('.strategy-background-adjustments')).not.toHaveAttribute('open', '')
  const textCommand = page.locator('.strategy-text-command')
  await expect(textCommand).toHaveAttribute('open', '')
  await textCommand.locator('summary').click()
  await expect(textCommand).not.toHaveAttribute('open', '')
  await textCommand.locator('summary').click()
  const canvasToolSections = page.locator('.strategy-tool-section')
  await expect(canvasToolSections).toHaveCount(1)
  await page.getByLabel('Strategy title').fill('North harbor approach')
  await page.locator('input[type="file"]').setInputFiles({
    name: 'harbor.png', mimeType: 'image/png', buffer: Buffer.from('planner-image'),
  })
  await expect(page.locator('.strategy-command-bar')).toHaveCSS('display', 'grid')
  await expect(page.locator('.strategy-marker-tools')).toHaveCSS('position', 'absolute')
  await expect(page.locator('.strategy-marker-tools')).toHaveCSS('left', '16px')
  await expect(page.locator('.strategy-marker-tools')).toHaveCSS('overflow', 'visible')
  await expect(page.locator('.strategy-canvas-tools')).toHaveCount(0)
  await expect(page.locator('.strategy-management-panel')).toHaveCSS('overflow', 'visible')
  await expect(page.locator('.strategy-management-panel')).toHaveCSS('max-height', 'none')
  const setupBox = await page.locator('.strategy-setup-deck').boundingBox()
  const commandBox = await page.locator('.strategy-command-bar').boundingBox()
  const workspaceBox = await page.locator('.strategy-planner-workspace').boundingBox()
  const chartBox = await page.locator('.strategy-chart-column').boundingBox()
  const managementBox = await page.locator('.strategy-management-panel').boundingBox()
  expect(setupBox.height).toBeLessThan(260)
  expect(commandBox.y).toBeGreaterThanOrEqual(setupBox.y + setupBox.height)
  expect(workspaceBox.y).toBeGreaterThanOrEqual(commandBox.y + commandBox.height)
  expect(chartBox.width).toBeGreaterThan(workspaceBox.width * 0.95)
  expect(managementBox.width).toBeGreaterThan(workspaceBox.width * 0.95)
  expect(chartBox.height).toBeGreaterThan(500)
  await page.getByRole('button', { name: 'Hide marker tools' }).click()
  await expect(page.locator('.strategy-marker-tools')).toBeHidden()
  await page.getByRole('button', { name: 'Show marker tools' }).click()
  const markerSelects = page.locator('.strategy-marker-tools select')
  await markerSelects.nth(0).selectOption('11')
  await expect(markerSelects.nth(1).locator('option')).toHaveCount(2)
  await markerSelects.nth(1).selectOption('21')
  await markerSelects.nth(2).selectOption('31')
  await page.getByRole('button', { name: 'Add ship marker' }).click()
  await expect(canvasToolSections).toHaveCount(3)
  await expect(page.locator('.strategy-marker-tools')).toBeHidden()
  await expect(page.locator('.strategy-canvas-tools')).toBeVisible()
  await expect(page.locator('.strategy-canvas-tools')).toHaveCSS('right', '16px')
  await expect(page.locator('.strategy-selection-section')).toHaveAttribute('open', '')
  await expect(page.locator('.strategy-transform-section')).not.toHaveAttribute('open', '')
  await expect(page.locator('.strategy-marker-disc')).toHaveAttribute('r', '18')
  await expect(page.locator('.strategy-marker-meta')).toHaveCount(0)
  await expect(page.locator('.strategy-legend')).toContainText('Leopard')
  await expect(page.locator('.strategy-legend')).toContainText('Frigate · Rate 3')
  await expect(page.locator('.strategy-legend')).toContainText('Boarding Leopard')
  await expect(page.locator('.strategy-legend')).toContainText('Eastern harbor approach')
  const canvasShellBox = await page.locator('.strategy-canvas-shell').boundingBox()
  const legendBox = await page.locator('.strategy-legend').boundingBox()
  expect(legendBox.y).toBeGreaterThanOrEqual(canvasShellBox.y + canvasShellBox.height)
  await page.locator('.strategy-transform-section summary').click()
  await expect(page.locator('.strategy-selection-section')).not.toHaveAttribute('open', '')
  await page.locator('.strategy-transform-panel input[type="range"]').first().fill('1.5')
  await page.locator('.strategy-management-toggle').click()
  await expect(page.locator('.strategy-management-panel')).toBeVisible()
  await expect(page.locator('.strategy-management-section')).toHaveCount(0)
  await expect(page.locator('.strategy-canvas-tools')).toBeVisible()
  await page.getByRole('button', { name: 'Hide object tools' }).click()
  await expect(page.locator('.strategy-canvas-tools')).toBeHidden()
  await expect(page.locator('.strategy-canvas-tools-toggle')).toBeVisible()
  await page.locator('.strategy-canvas-tools-toggle').click()
  await expect(page.locator('.strategy-canvas-tools')).toBeVisible()
  await page.locator('.strategy-canvas').scrollIntoViewIfNeeded()
  const markerBox = await page.locator('.strategy-ship-marker').boundingBox()
  await page.mouse.move(markerBox.x + markerBox.width / 2, markerBox.y + markerBox.height / 2)
  await page.mouse.down()
  await page.mouse.move(markerBox.x + markerBox.width / 2 + 40, markerBox.y + markerBox.height / 2 + 20)
  await page.mouse.up()
  await page.locator('.strategy-management-toggle').click()
  await expect(page.locator('.strategy-management-section')).toBeVisible()
  await page.getByRole('button', { name: 'Arrow', exact: true }).click()
  await page.locator('.strategy-transform-section summary').click()
  await page.locator('.strategy-transform-panel input[type="range"]').first().fill('2')
  await page.locator('.strategy-transform-panel input[type="range"]').nth(1).fill('45')
  await expect(page.locator('.strategy-line')).toHaveAttribute('transform', /rotate\(45/)
  await expect(page.locator('.strategy-line line')).toHaveAttribute('x1', '100')
  await expect(page.locator('.strategy-line line')).toHaveAttribute('x2', '900')
  await expect(page.locator('.strategy-arrow-head')).toBeVisible()
  await page.getByRole('button', { name: 'Add text', exact: true }).click()
  await page.getByRole('button', { name: 'Text color #ef6461' }).click()
  await expect(page.locator('.strategy-text')).toHaveAttribute('fill', '#ef6461')
  await expect(page.locator('.strategy-text')).toHaveCSS('fill', 'rgb(239, 100, 97)')
  const formationSelect = page.locator('.strategy-formation-command select')
  await expect(formationSelect.locator('option')).toContainText(['Battle line', 'Circle', 'Oval', 'Wedge', 'Column', 'Box'])
  await formationSelect.selectOption('circle')
  await page.getByRole('button', { name: 'Formation', exact: true }).click()
  await expect(page.locator('.strategy-formation path')).toHaveAttribute('d', /A 75 75/)
  await page.locator('.strategy-transform-section summary').click()
  await page.locator('.strategy-transform-panel input[type="range"]').first().fill('0.25')
  await expect(page.locator('.strategy-formation path')).toHaveAttribute('d', /A 18.75 18.75/)
  await expect(page.locator('.strategy-formation path')).toHaveCSS('stroke-width', '7px')
  await page.getByRole('button', { name: 'Freehand', exact: true }).click()
  await expect(page.locator('.strategy-canvas')).toHaveClass(/is-drawing/)
  await page.locator('.strategy-canvas').scrollIntoViewIfNeeded()
  const stroke = await page.locator('.strategy-canvas').evaluate((svg) => {
    const matrix = svg.getScreenCTM()
    const height = svg.viewBox.baseVal.height
    const screen = (x, y) => new DOMPoint(x * 1000, y * height).matrixTransform(matrix)
    return { start: screen(0.15, 0.35), middle: screen(0.2, 0.4), end: screen(0.25, 0.45) }
  })
  await page.mouse.move(stroke.start.x, stroke.start.y)
  await page.mouse.down()
  await page.mouse.move(stroke.middle.x, stroke.middle.y, { steps: 3 })
  await page.mouse.move(stroke.end.x, stroke.end.y, { steps: 3 })
  await page.mouse.up()
  await page.getByRole('button', { name: 'Save strategy' }).click()

  await expect(page).toHaveURL(/\/strategies\/41\/edit$/)
  await expect(page.getByRole('status').filter({ hasText: 'Strategy saved' })).toBeVisible()
  const overlay = JSON.parse(savedPayload.overlay_json)
  expect(savedPayload.background_file_id).toBe(9)
  expect(overlay.version).toBe(2)
  expect(overlay.objects.map((item) => item.type)).toEqual(['ship', 'arrow', 'text', 'formation', 'freehand'])
  expect(overlay.objects[0]).toMatchObject({ shipId: 11, playerName: null, buildId: 21, guideId: 31, scale: 1.5 })
  expect(overlay.objects[0].x).toBeGreaterThan(0.5)
  expect(overlay.objects[0].y).toBeGreaterThan(0.5)
  expect(overlay.objects[1]).toMatchObject({ rotation: 45, scale: 2 })
  expect(overlay.objects[2]).toMatchObject({ color: '#ef6461' })
  expect(overlay.objects[3]).toMatchObject({ formation: 'circle', scale: 0.25 })
  expect(overlay.objects[4].points[0]).toBeCloseTo(0.15, 2)
  expect(overlay.objects[4].points[1]).toBeCloseTo(0.35, 2)
  expect(browserErrors).toEqual([])

  await page.getByRole('button', { name: 'Make strategy public' }).click()
  await expect(page.getByText('Published', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'View public strategy' })).toHaveAttribute('href', new RegExp(`/strategies/shared/${publicId}$`))
  await expect(page.locator('.strategy-public-link input')).toHaveValue(new RegExp(`/strategies/shared/${publicId}$`))
  await expect(page.locator('.strategy-canvas image')).toHaveAttribute('href', '/api/files/9/content')
  await expect(page.locator('.strategy-overlay-layer')).toBeVisible()
  await page.locator('.strategy-management-toggle').click()
  await expect(page.locator('.strategy-management-panel')).toBeVisible()
  await expect(page.locator('.strategy-inspector-control-card')).toBeVisible()
  await expect(page.locator('.strategy-management-toggle')).toContainText('Show strategy management')
  await expect(page.locator('.strategy-management-toggle')).toHaveAttribute('aria-expanded', 'false')
  await page.locator('.strategy-management-toggle').click()
  await expect(page.locator('.strategy-management-panel')).toBeVisible()
  await expect(page.locator('.strategy-management-toggle')).toHaveAttribute('aria-expanded', 'true')
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.locator('.strategy-management-toggle strong')).toHaveCSS('display', 'none')
  const mobileRailBox = await page.locator('.strategy-canvas-tools').boundingBox()
  expect(mobileRailBox.x).toBeGreaterThanOrEqual(0)
  expect(mobileRailBox.width).toBeLessThanOrEqual(390)
})

test('ordinary members can browse builds but cannot open shared-content editors', async ({ page }) => {
  await page.route(/^https?:\/\/[^/]+\/api\/auth\/me$/, (route) => route.fulfill({
    json: { id: 18, username: 'reader', display_name: 'Reader', role: 'user' },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/ships$/, (route) => route.fulfill({ json: [] }))
  await page.route(/^https?:\/\/[^/]+\/api\/builds\/roles$/, (route) => route.fulfill({ json: [] }))
  await page.route(/^https?:\/\/[^/]+\/api\/builds\?/, (route) => route.fulfill({
    json: { items: [], total: 0 },
  }))

  await page.goto('/builds')
  await expect(page).toHaveURL(/\/builds$/)
  await expect(page.locator('a[href="/builds/new"]')).toHaveCount(0)

  await page.goto('/builds/new')
  await expect(page).toHaveURL(/\/profile$/)
})

test('published strategies have a dedicated read-only view for other users', async ({ page }) => {
  const publicId = '4f30d366-5d04-4bc1-ae1a-4df5b88c0834'
  const overlay = JSON.stringify({
    version: 1,
    objects: [{
      id: 'ship-1', type: 'ship', shipId: 11, shipName: 'Leopard', shipType: 'Frigate', shipRate: 3,
      playerName: null, buildId: 21, guideId: 31, x: 0.4, y: 0.45, scale: 1, rotation: 0, color: '#d6b35a',
    }],
  })
  const strategy = {
    id: 41, owner_id: 7, title: 'North harbor approach', description: 'Hold the eastern entrance.',
    overlay_json: overlay, public_id: publicId, is_published: true,
    background_file: { id: 9, public_url: '/api/files/9/content', original_name: 'harbor.png' },
    created_at: '2030-01-15T12:00:00', updated_at: '2030-01-15T12:10:00', published_at: '2030-01-15T12:10:00',
  }

  await page.route(/^https?:\/\/[^/]+\/api\/strategies\/shared\//, (route) => route.fulfill({ json: strategy }))
  await page.route(/^https?:\/\/[^/]+\/api\/ships$/, (route) => route.fulfill({
    json: [{ id: 11, name: 'Leopard', ship_type: 'Frigate', rate: 3 }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/builds\?/, (route) => route.fulfill({
    json: { items: [{ id: 21, build_name: 'Boarding Leopard' }], total: 1 },
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/guides\?/, (route) => route.fulfill({
    json: [{ id: 31, title: 'Eastern harbor approach' }],
  }))
  await page.route(/^https?:\/\/[^/]+\/api\/files\/9\/content$/, (route) => route.fulfill({
    contentType: 'image/svg+xml', body: '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500"><rect width="800" height="500" fill="#16324a"/></svg>',
  }))

  await page.goto(`/strategies/shared/${publicId}`)

  await expect(page.getByRole('heading', { name: 'North harbor approach' })).toBeVisible()
  await expect(page.locator('.strategy-view-header')).toContainText('Hold the eastern entrance.')
  await expect(page.locator('.strategy-legend')).toContainText('Leopard')
  await expect(page.locator('.strategy-legend')).toContainText('Frigate · Rate 3')
  await expect(page.locator('.strategy-command-bar')).toHaveCount(0)
  await expect(page.locator('.strategy-tool-rail')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Save strategy' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Edit' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Print / save PDF' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Download SVG' })).toBeVisible()

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Download SVG' }).click(),
  ])
  const svg = await readFile(await download.path(), 'utf8')
  expect(svg).toContain('data:image/svg+xml;base64,')
  expect(svg).not.toContain('href="/api/files/9/content"')
  expect(svg).toContain('strategy-overlay-layer')

  await page.emulateMedia({ media: 'print' })
  await expect(page.locator('.strategy-view-header')).toBeHidden()
  await expect(page.locator('.strategy-print-summary')).toContainText('North harbor approach')
  await expect(page.locator('.strategy-print-summary')).toContainText('Hold the eastern entrance.')
  await expect(page.locator('.strategy-print-player-heading')).toContainText('Player list, builds and guides')
  await expect(page.locator('.strategy-print-chart-page')).toHaveCSS('break-after', 'page')
  await expect(page.locator('.strategy-legend-entry')).toHaveCSS('break-inside', 'avoid')
})
