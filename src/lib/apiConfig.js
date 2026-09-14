/**
 * Configuration API frontend. Aucun secret ici.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function getAuthHeaders() {
  return {}
}
