const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function parseJson(response) {
  const text = await response.text()
  let data = {}
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }
  if (!response.ok) {
    const detail = data.detail
    const message = typeof detail === 'string' ? detail : detail?.error || response.statusText
    const error = new Error(message || `Erreur ${response.status}`)
    error.status = response.status
    throw error
  }
  return data
}

export const authClient = {
  async register({ email, password, nom, entreprise }) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, nom, entreprise }),
    })
    return parseJson(response)
  },

  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    return parseJson(response)
  },

  async me() {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      credentials: 'include',
    })
    if (response.status === 401) {
      const refreshed = await this.refresh()
      if (!refreshed) return null
      const retry = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        credentials: 'include',
      })
      if (!retry.ok) return null
      return parseJson(retry)
    }
    if (!response.ok) return null
    return parseJson(response)
  },

  async refresh() {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    return response.ok
  },

  async logout() {
    await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    })
  },

  async forgotPassword(email) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    return parseJson(response)
  },

  async changePassword(currentPassword, newPassword) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/change-password`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    })
    return parseJson(response)
  },

  async resetPassword(token, password) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, password }),
    })
    return parseJson(response)
  },
}
