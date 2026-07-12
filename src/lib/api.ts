export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function formatApiError(response: Response) {
  const data = await response.json().catch(() => null)

  if (!data) return 'Request failed'
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((error: { msg?: string; message?: string }) => error.msg ?? error.message ?? 'Invalid field')
      .join(', ')
  }
  if (data.detail) return JSON.stringify(data.detail)
  return data.message ?? 'Request failed'
}

interface ApiOptions extends RequestInit {
  token?: string | null
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}) {
  const headers = new Headers(options.headers)
  const token = options.token ?? localStorage.getItem('access_token')

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    })
  } catch (err) {
    throw new ApiError(err instanceof Error ? err.message : 'Network request failed', 0)
  }

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('token_type')
      localStorage.removeItem('profile_completed')
    }
    throw new ApiError(await formatApiError(response), response.status)
  }

  if (response.status === 204) {
    return null as T
  }

  return await response.json() as T
}
