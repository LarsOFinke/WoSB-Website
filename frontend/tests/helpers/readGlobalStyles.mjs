import { readFileSync } from 'node:fs'

const globalRoot = new URL('../../src/styles/global/', import.meta.url)

export function globalStyleFiles() {
  const manifest = readFileSync(new URL('index.js', globalRoot), 'utf8')
  return [...manifest.matchAll(/import '\.\/(\d{2}-[^']+\.css)'/g)].map((match) => match[1])
}

export function readGlobalStyles() {
  return globalStyleFiles()
    .map((filename) => readFileSync(new URL(filename, globalRoot), 'utf8'))
    .join('\n')
}
