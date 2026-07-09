const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request(path, options = {}) {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: isFormData
      ? { ...(options.headers || {}) }
      : {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
    ...options,
  })

  if (!response.ok) {
    let message = `API error ${response.status}`
    try {
      const payload = await response.json()
      message = payload.detail || message
    } catch {
      // keep fallback message
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export function get(path) {
  return request(path)
}

export function post(path, payload) {
  return request(path, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function postForm(path, formData) {
  return request(path, {
    method: 'POST',
    body: formData,
  })
}

export function put(path, payload) {
  return request(path, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteRequest(path) {
  return request(path, { method: 'DELETE' })
}
