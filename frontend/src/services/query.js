export function toQueryString(params = {}) {
  const searchParams = new URLSearchParams()

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, value)
    }
  }

  return searchParams.toString()
}

export function withQuery(path, params = {}) {
  const query = toQueryString(params)
  return query ? `${path}?${query}` : path
}
