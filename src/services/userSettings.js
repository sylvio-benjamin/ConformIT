'use client'

import { API_URL, getAuthHeaders } from '@/lib/apiConfig'

const API_BASE = API_URL

async function handleResponse(response) {
  if (!response.ok) {
    const text = await response.text()
    let message = text
    try {
      const data = JSON.parse(text)
      message = data.detail || data.error || JSON.stringify(data)
    } catch (error) {
      // noop
    }
    throw new Error(message || 'Erreur réseau')
  }
  return response
}

export async function fetchSessions(userId) {
  const res = await handleResponse(await fetch(`${API_BASE}/users/${userId}/sessions`, {
    credentials: 'include',
    headers: getAuthHeaders()
  }))
  return res.json()
}

export async function revokeSessions(userId) {
  const res = await handleResponse(await fetch(`${API_BASE}/users/${userId}/logout`, {
    method: 'POST',
    credentials: 'include',
    headers: getAuthHeaders()
  }))
  return res.json()
}

export async function exportUserData(userId) {
  const res = await handleResponse(await fetch(`${API_BASE}/users/${userId}/export`, {
    method: 'POST',
    credentials: 'include',
    headers: getAuthHeaders()
  }))
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `export_${userId}.zip`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
  return true
}

export async function updatePreferences(userId, preferences) {
  const res = await handleResponse(await fetch(`${API_BASE}/users/${userId}/preferences`, {
    method: 'PUT',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders()
    },
    body: JSON.stringify(preferences)
  }))
  return res.json()
}

