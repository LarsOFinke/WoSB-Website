import { readFileSync, readdirSync } from 'node:fs'
import { extname, join, relative, resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..', 'src')
const allowedMaxWidths = new Set([480, 620, 720, 900, 1050, 1180, 1320, 1480])
const colorLiteralBudget = 880
const failures = []
let colorLiterals = 0

function sourceFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    return ['.css', '.vue'].includes(extname(path)) ? [path] : []
  })
}

function lineNumber(source, index) {
  return source.slice(0, index).split('\n').length
}

function fail(path, source, index, message) {
  failures.push(`${relative(root, path)}:${lineNumber(source, index)} ${message}`)
}

for (const path of sourceFiles(root)) {
  const source = readFileSync(path, 'utf8')
  colorLiterals += (source.match(/#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)/g) || []).length

  for (const match of source.matchAll(/@media\s*\([^)]*max-width:\s*(\d+)px[^)]*\)/g)) {
    const width = Number(match[1])
    if (!allowedMaxWidths.has(width)) {
      fail(path, source, match.index, `uses non-standard max-width ${width}px`)
    }
  }

  for (const match of source.matchAll(/font-size:\s*(0?\.\d+)rem/g)) {
    if (Number(match[1]) < 0.75) {
      fail(path, source, match.index, `uses text smaller than 0.75rem (${match[1]}rem)`)
    }
  }

  for (const match of source.matchAll(/font-size:\s*(\d+(?:\.\d+)?)px/g)) {
    if (Number(match[1]) < 12) {
      fail(path, source, match.index, `uses text smaller than 12px (${match[1]}px)`)
    }
  }
}

const globalRoot = join(root, 'styles/global')
function readGlobalGroup(fragment) {
  return readdirSync(globalRoot)
    .filter((filename) => filename.endsWith('.css') && filename.includes(fragment))
    .sort()
    .map((filename) => readFileSync(join(globalRoot, filename), 'utf8'))
    .join('\n')
}

const foundation = readGlobalGroup('-foundation-')
const bodyBlock = foundation.match(/body\s*\{([^}]*)\}/s)?.[1] || ''
if (/overflow-x:\s*(?:hidden|clip)/.test(bodyBlock)) {
  failures.push('global foundation styles hide horizontal body overflow')
}

const shell = readGlobalGroup('-shell-')
for (const selector of ['body,\\s*#app', '\\.app-shell', '\\.app-sidebar']) {
  const block = shell.match(new RegExp(`${selector}[^,{]*\\{([^}]*)\\}`, 's'))?.[1] || ''
  if (!/100dvh/.test(block)) failures.push(`global shell ${selector} lacks a dvh viewport fallback`)
}

if (colorLiterals > colorLiteralBudget) {
  failures.push(`color literal budget exceeded: ${colorLiterals} > ${colorLiteralBudget}`)
}

if (failures.length) {
  console.error(failures.join('\n'))
  process.exit(1)
}

console.log(`Responsive CSS checks passed: ${allowedMaxWidths.size} breakpoints, ${colorLiterals}/${colorLiteralBudget} color literals.`)
