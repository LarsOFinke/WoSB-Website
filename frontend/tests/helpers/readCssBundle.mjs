import { readFileSync } from 'node:fs'

export function readCssBundle(paths, baseUrl = import.meta.url) {
  return paths
    .map((path) => readFileSync(new URL(path, baseUrl), 'utf8'))
    .join('\n')
}
