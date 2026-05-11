import { beforeEach, describe, expect, it, vi } from 'vitest'

const authState = vi.hoisted(() => ({
  accessToken: 'old-access-token',
  refreshToken: 'refresh-token',
  clearCalls: 0,
  saveCalls: []
}))

vi.mock('./auth', () => ({
  getAccessToken: () => authState.accessToken,
  getRefreshToken: () => authState.refreshToken,
  clearAuthSession: () => {
    authState.clearCalls += 1
    authState.accessToken = ''
    authState.refreshToken = ''
  },
  saveAuthSession: (payload) => {
    authState.saveCalls.push(payload)
    authState.accessToken = payload.accessToken
    authState.refreshToken = payload.refreshToken
  }
}))

const jsonHeaders = {
  get: () => 'application/json'
}

const createJsonResponse = ({ ok, status, payload }) => ({
  ok,
  status,
  headers: jsonHeaders,
  json: async () => payload,
  text: async () => JSON.stringify(payload)
})

const loadApiModule = async () => {
  vi.resetModules()
  return import('./api')
}

beforeEach(() => {
  authState.accessToken = 'old-access-token'
  authState.refreshToken = 'refresh-token'
  authState.clearCalls = 0
  authState.saveCalls = []
  global.fetch = vi.fn()
})

describe('api auth refresh flow', () => {
  it('refreshes token and retries once after 401', async () => {
    global.fetch
      .mockResolvedValueOnce(
        createJsonResponse({
          ok: false,
          status: 401,
          payload: { detail: 'access token expired' }
        })
      )
      .mockResolvedValueOnce(
        createJsonResponse({
          ok: true,
          status: 200,
          payload: {
            access_token: 'new-access-token',
            refresh_token: 'new-refresh-token',
            user: { id: 'u1' }
          }
        })
      )
      .mockResolvedValueOnce(
        createJsonResponse({
          ok: true,
          status: 200,
          payload: { data: 'ok' }
        })
      )

    const { apiRequest } = await loadApiModule()
    const result = await apiRequest('/protected/resource')

    expect(result).toEqual({ data: 'ok' })
    expect(authState.saveCalls).toHaveLength(1)
    expect(authState.clearCalls).toBe(0)
    expect(global.fetch).toHaveBeenCalledTimes(3)

    const firstRequestHeaders = global.fetch.mock.calls[0][1].headers
    const retryRequestHeaders = global.fetch.mock.calls[2][1].headers
    expect(firstRequestHeaders.get('Authorization')).toBe('Bearer old-access-token')
    expect(retryRequestHeaders.get('Authorization')).toBe('Bearer new-access-token')
  })

  it('clears auth session when refresh fails', async () => {
    global.fetch
      .mockResolvedValueOnce(
        createJsonResponse({
          ok: false,
          status: 401,
          payload: { detail: 'access token expired' }
        })
      )
      .mockResolvedValueOnce(
        createJsonResponse({
          ok: false,
          status: 401,
          payload: { detail: 'refresh token invalid' }
        })
      )

    const { apiRequest, ApiError } = await loadApiModule()
    await expect(apiRequest('/protected/resource')).rejects.toBeInstanceOf(ApiError)
    expect(authState.clearCalls).toBe(1)
    expect(authState.saveCalls).toHaveLength(0)
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('shares one refresh request across concurrent 401 responses', async () => {
    const deferredRefresh = (() => {
      let resolve
      const promise = new Promise((r) => {
        resolve = r
      })
      return { promise, resolve }
    })()

    let protectedAttempts = 0
    global.fetch.mockImplementation((url) => {
      if (url.includes('/auth/refresh')) {
        return deferredRefresh.promise
      }

      protectedAttempts += 1
      if (protectedAttempts <= 2) {
        return Promise.resolve(
          createJsonResponse({
            ok: false,
            status: 401,
            payload: { detail: 'expired' }
          })
        )
      }

      return Promise.resolve(
        createJsonResponse({
          ok: true,
          status: 200,
          payload: { ok: true, attempt: protectedAttempts }
        })
      )
    })

    const { apiRequest } = await loadApiModule()
    const requestA = apiRequest('/chat/sessions')
    const requestB = apiRequest('/chat/sessions')

    deferredRefresh.resolve(
      createJsonResponse({
        ok: true,
        status: 200,
        payload: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          user: { id: 'u1' }
        }
      })
    )

    const [resultA, resultB] = await Promise.all([requestA, requestB])
    expect(resultA.ok).toBe(true)
    expect(resultB.ok).toBe(true)
    expect(authState.saveCalls).toHaveLength(1)

    const refreshCalls = global.fetch.mock.calls.filter(([url]) => url.includes('/auth/refresh'))
    expect(refreshCalls).toHaveLength(1)
  })
})
