import fs from 'node:fs'
import path from 'node:path'
import { compileScript, compileTemplate, parse } from '@vue/compiler-sfc'

const pages = []

function collectVuePages(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const filePath = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      collectVuePages(filePath)
    } else if (entry.name.endsWith('.vue') && filePath.includes(`${path.sep}pages${path.sep}`)) {
      pages.push(filePath)
    }
  }
}

collectVuePages('src/modules')

const problems = []
for (const filePath of pages) {
  const source = fs.readFileSync(filePath, 'utf8')
  const { descriptor, errors } = parse(source, { filename: filePath })
  if (errors.length) throw new Error(`${filePath}: ${errors.join(', ')}`)
  if (!descriptor.scriptSetup || !descriptor.template) continue

  const script = compileScript(descriptor, { id: filePath })
  const template = compileTemplate({
    id: filePath,
    filename: filePath,
    source: descriptor.template.content,
    compilerOptions: { bindingMetadata: script.bindings },
  })
  if (template.errors.length) throw new Error(`${filePath}: ${template.errors.join(', ')}`)

  const unresolved = [...new Set(
    [...template.code.matchAll(/_ctx\.([A-Za-z_$][\w$]*)/g)].map((match) => match[1]),
  )]
  if (unresolved.length) problems.push({ filePath, unresolved })
}

if (problems.length) {
  for (const { filePath, unresolved } of problems) {
    console.error(`${filePath}: unresolved template bindings: ${unresolved.join(', ')}`)
  }
  process.exit(1)
}

console.log(`Checked ${pages.length} route pages; unresolved template bindings: 0`)
