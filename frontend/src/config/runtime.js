function requireEnvValue(name, value) {
  if (!value) {
    throw new Error(`Missing frontend environment value: ${name}. Create frontend/.env from frontend/.env.example.`)
  }
  return value
}

// Vite replaces only statically referenced import.meta.env properties in a
// production bundle. Keep this access explicit; a dynamic [name] lookup passes
// local file validation but resolves against Vite's reduced runtime object.
export const API_BASE_URL = requireEnvValue('VITE_API_BASE_URL', import.meta.env.VITE_API_BASE_URL)
