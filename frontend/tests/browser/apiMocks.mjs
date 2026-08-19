export async function mockAnonymousApi(page) {
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
