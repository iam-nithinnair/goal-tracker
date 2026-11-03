import { supabase } from './supabase'

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://127.0.0.1:8000/api/v1'

export class ApiError extends Error {
  status: number
  code: string
  fields?: Record<string, string>

  constructor(status: number, code: string, message: string, fields?: Record<string, string>) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fields = fields
  }
}

async function accessToken(forceRefresh = false): Promise<string | null> {
  if (forceRefresh) {
    const { data } = await supabase.auth.refreshSession()
    return data.session?.access_token ?? null
  }
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}

async function send(path: string, init: RequestInit, token: string | null): Promise<Response> {
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  try {
    return await fetch(`${BASE}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'network_error', "Can't reach the server. Check your connection.")
  }
}

export async function api<T = unknown>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, ...rest } = init
  const options: RequestInit = json !== undefined ? { ...rest, body: JSON.stringify(json) } : rest

  let res = await send(path, options, await accessToken())
  if (res.status === 401) {
    // The access token may just have expired: refresh once and retry.
    const fresh = await accessToken(true)
    if (fresh) res = await send(path, options, fresh)
  }

  if (res.status === 204) return undefined as T
  const text = await res.text()
  const body = text ? safeJson(text) : null
  if (!res.ok) {
    const err = (body as { error?: { code?: string; message?: string; fields?: Record<string, string> } } | null)
      ?.error
    throw new ApiError(
      res.status,
      err?.code ?? 'http_error',
      err?.message ?? `Request failed (${res.status})`,
      err?.fields,
    )
  }
  return body as T
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

/** A friendly message for any thrown value. */
export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return 'Something went wrong'
}
