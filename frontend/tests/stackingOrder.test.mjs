import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'
import test from 'node:test'

const srcRoot = new URL('../src/', import.meta.url)
const tokensUrl = new URL('../src/styles/global/00-tokens.css', import.meta.url)

async function sourceFiles(directory) {
  const rows = await readdir(directory, { withFileTypes: true })
  const nested = await Promise.all(rows.map(async (row) => {
    const url = new URL(`${row.name}${row.isDirectory() ? '/' : ''}`, directory)
    if (row.isDirectory()) return sourceFiles(url)
    return /\.(css|vue)$/.test(row.name) ? [url] : []
  }))
  return nested.flat()
}

function tokenValue(source, name) {
  const match = source.match(new RegExp(`${name}:\\s*(-?\\d+);`))
  assert.ok(match, `missing ${name}`)
  return Number(match[1])
}

test('global overlay layers have a documented monotonic order', async () => {
  const tokens = await readFile(tokensUrl, 'utf8')
  const ordered = [
    '--z-behind',
    '--z-base',
    '--z-raised',
    '--z-local-sticky',
    '--z-sticky-content',
    '--z-shell-sidebar',
    '--z-shell-topbar',
    '--z-popover',
    '--z-scrim',
    '--z-drawer',
    '--z-modal',
    '--z-notice',
    '--z-consent',
    '--z-skip-link',
  ].map((name) => tokenValue(tokens, name))

  for (let index = 1; index < ordered.length; index += 1) {
    assert.ok(ordered[index] > ordered[index - 1], `layer ${index} must be above layer ${index - 1}`)
  }
})

test('application styles use semantic z-index tokens instead of local magic numbers', async () => {
  const files = await sourceFiles(srcRoot)
  for (const file of files) {
    const source = await readFile(file, 'utf8')
    assert.doesNotMatch(source, /z-index:\s*-?\d+\s*;/, file.pathname)
  }
})
