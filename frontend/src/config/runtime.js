function requireEnvValue(name) {
  const value = import.meta.env[name]
  if (!value) {
    throw new Error(`Missing frontend environment value: ${name}. Create frontend/.env from frontend/.env.example.`)
  }
  return value
}

export const API_BASE_URL = requireEnvValue('VITE_API_BASE_URL')
