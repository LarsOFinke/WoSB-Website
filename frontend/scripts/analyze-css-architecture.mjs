import { readdir, readFile } from 'node:fs/promises'
import { relative, resolve } from 'node:path'

import postcss from 'postcss'

const root = resolve(import.meta.dirname, '..')
const sourceRoot = resolve(root, 'src')

async function walkFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const paths = await Promise.all(entries.map((entry) => {
    const path = resolve(directory, entry.name)
    return entry.isDirectory() ? walkFiles(path) : [path]
  }))
  return paths.flat()
}

const files = (await walkFiles(sourceRoot)).filter((file) => file.endsWith('.css'))
const selectors = new Map()
const declarationSets = new Map()
const declarationsByRule = new Map()

function contextFor(rule) {
  const context = []
  for (let parent = rule.parent; parent; parent = parent.parent) {
    if (parent.type === 'atrule') context.unshift(`@${parent.name} ${parent.params}`)
  }
  return context.join(' > ') || 'base'
}

for (const file of files) {
  const css = await readFile(file, 'utf8')
  const tree = postcss.parse(css, { from: file })
  tree.walkRules((rule) => {
    const location = `${relative(root, file)}:${rule.source.start.line}`
    const context = contextFor(rule)
    const ruleKey = `${relative(root, file)}\n${context}\n${rule.selector}`
    const ruleEntries = declarationsByRule.get(ruleKey) ?? []
    for (const node of rule.nodes.filter((child) => child.type === 'decl')) {
      ruleEntries.push({ location, property: node.prop, value: node.value })
    }
    declarationsByRule.set(ruleKey, ruleEntries)
    for (const selector of rule.selectors.map((value) => value.trim())) {
      const key = `${context}\n${selector}`
      const entries = selectors.get(key) ?? []
      entries.push(location)
      selectors.set(key, entries)
    }

    const declarations = rule.nodes
      .filter((node) => node.type === 'decl')
      .map((node) => `${node.prop.trim()}:${node.value.trim()}${node.important ? '!important' : ''}`)
      .sort()
    if (declarations.length < 3) return
    const key = declarations.join(';')
    const entries = declarationSets.get(key) ?? []
    entries.push({ location, selector: rule.selector, context })
    declarationSets.set(key, entries)
  })
}

const repeatedSelectors = [...selectors]
  .filter(([, locations]) => locations.length > 1)
  .sort((left, right) => right[1].length - left[1].length)
const repeatedDeclarationSets = [...declarationSets.values()]
  .filter((entries) => entries.length > 1)
  .sort((left, right) => right.length - left.length)
const overriddenDeclarations = [...declarationsByRule]
  .map(([key, entries]) => {
    const properties = new Map()
    for (const entry of entries) {
      const values = properties.get(entry.property) ?? []
      values.push(entry)
      properties.set(entry.property, values)
    }
    return [key, [...properties].filter(([, values]) => values.length > 1)]
  })
  .filter(([, properties]) => properties.length)

console.log(`CSS architecture: ${files.length} files, ${repeatedSelectors.length} repeated selector contexts, ${repeatedDeclarationSets.length} repeated declaration sets.`)
for (const [key, locations] of repeatedSelectors.slice(0, 40)) {
  const [context, selector] = key.split('\n')
  console.log(`SELECTOR ${selector} [${context}] -> ${locations.join(', ')}`)
}
for (const entries of repeatedDeclarationSets.slice(0, 30)) {
  console.log(`DECLARATIONS -> ${entries.map(({ selector, location }) => `${selector} (${location})`).join(', ')}`)
}
for (const [key, properties] of overriddenDeclarations.slice(0, 60)) {
  const [file, context, selector] = key.split('\n')
  console.log(`OVERRIDE ${selector} [${context}] (${file}) -> ${properties.map(([property, values]) => `${property}: ${values.map(({ value, location }) => `${value} @ ${location}`).join(' => ')}`).join('; ')}`)
}
