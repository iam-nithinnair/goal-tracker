import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const getSession = vi.fn()
const refreshSession = vi.fn()
vi.mock('./supabase', () => ({
  supabase: { auth: { getSession: () => getSession(), refreshSession: () => refreshSession() } },
}))

import { api, ApiError, errorMessage } from './api'

const json = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status })

describe('api()', () => {
  beforeEach(() => {
    getSession.mockResolvedValue({ data: { session: { access_token: 'tok-1' } } })
    refreshSession.mockResolvedValue({ data: { session: { access_token: 'tok-2' } } })
  })
  afterEach(() => vi.restoreAllMocks())

  it('sends the bearer token and parses JSON', async () => {
    const f = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(200, { ok: 1 }))
    expect(await api('/me')).toEqual({ ok: 1 })
    const headers = f.mock.calls[0][1]!.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer tok-1')
  })

  it('turns the standard error shape into an ApiError', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      json(400, { error: { code: 'validation_error', message: 'Bad', fields: { name: 'required' } } }),
    )
    const err = await api('/challenges', { method: 'POST', json: {} }).catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 400, code: 'validation_error', fields: { name: 'required' } })
    expect(errorMessage(err)).toBe('Bad')
  })

  it('refreshes the session once on 401 and retries', async () => {
    const f = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(json(401, { error: { code: 'unauthorized', message: 'Token expired' } }))
      .mockResolvedValueOnce(json(200, { id: 'me' }))
    expect(await api('/me')).toEqual({ id: 'me' })
    expect(f).toHaveBeenCalledTimes(2)
    expect((f.mock.calls[1][1]!.headers as Headers).get('Authorization')).toBe('Bearer tok-2')
  })

  it('does not loop when the retry is also 401', async () => {
    const f = vi.spyOn(globalThis, 'fetch').mockResolvedValue(json(401, { error: { code: 'unauthorized', message: 'no' } }))
    await expect(api('/me')).rejects.toMatchObject({ status: 401 })
    expect(f).toHaveBeenCalledTimes(2)
  })

  it('handles 204 with no body', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }))
    expect(await api('/goals/1', { method: 'DELETE' })).toBeUndefined()
  })

  it('reports an unreachable server in plain words', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('failed'))
    await expect(api('/me')).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })
})
