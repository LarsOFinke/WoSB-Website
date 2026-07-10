import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const envFile = resolve(process.cwd(), '.env')
const requiredKeys = ['VITE_API_BASE_URL']

if (!existsSync(envFile)) {
  console.error('Missing frontend/.env. Copy frontend/.env.example to frontend/.env and fill all required values.')
  process.exit(1)
}

const envText = readFileSync(envFile, 'utf8')
const values = new Map()
for (const line of envText.split(/\r?\n/)) {
  const trimmed = line.trim()
  if (!trimmed || trimmed.startsWith('#')) continue
  const match = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/)
  if (!match) continue
  const [, key, rawValue] = match
  const value = rawValue.trim().replace(/^['"]|['"]$/g, '')
  values.set(key, value)
}

const missing = requiredKeys.filter((key) => !values.get(key))
if (missing.length) {
  console.error(`Missing required frontend env values: ${missing.join(', ')}`)
  process.exit(1)
}
