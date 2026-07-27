import { readFileSync, readdirSync } from 'node:fs'

const stylesRoot = new URL('../../src/styles/', import.meta.url)
const layersRoot = new URL('../../src/styles/layers/', import.meta.url)

export function readGlobalStyles() {
  const manifest = readFileSync(new URL('main.css', stylesRoot), 'utf8')
  const layers = readdirSync(layersRoot)
    .filter((name) => name.endsWith('.css'))
    .sort()
    .map((name) => readFileSync(new URL(name, layersRoot), 'utf8'))

  return [manifest, ...layers].join('\n')
}
