import { readFileSync } from 'node:fs'

const stylesRoot = new URL('../../src/styles/', import.meta.url)

export function readGlobalStyles() {
  return readFileSync(new URL('main.css', stylesRoot), 'utf8')
}
