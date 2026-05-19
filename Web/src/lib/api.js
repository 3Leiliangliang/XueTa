import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  saveAuthSession
} from './auth'
import { getActiveLlmRequestHeaders } from './settings'

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '')
const REFRESH_PATH = '/auth/refresh'

let refreshPromise = null

export class ApiError extends Error {
  constructor(message, { status = 500, payload = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

const isNetworkError = (error) =>
  error instanceof TypeError && String(error.message || '').toLowerCase().includes('fetch')

const createNetworkError = (error) =>
  new ApiError(
    '无法连接后端服务，请确认后端已启动且当前前端地址已被后端 CORS 允许。',
    {
      status: 0,
      payload: {
        cause: error.message,
        baseUrl: API_BASE_URL
      }
    }
  )

const getErrorMessage = (payload, status) => {
  if (!payload) return `Request failed (${status})`
  if (typeof payload === 'string') return payload
  if (typeof payload.detail === 'string') return payload.detail
  if (Array.isArray(payload.detail)) {
    const firstIssue = payload.detail[0]
    if (typeof firstIssue === 'string') return firstIssue
    if (firstIssue && typeof firstIssue.msg === 'string') return firstIssue.msg
    return `Request failed (${status})`
  }
  if (typeof payload.message === 'string') return payload.message
  return `Request failed (${status})`
}

const parseJsonSafely = async (response) => {
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    return response.text()
  }

  try {
    return await response.json()
  } catch {
    return null
  }
}

const normalizePath = (path) => (path.startsWith('/') ? path : `/${path}`)
const buildUrl = (path) => `${API_BASE_URL}${normalizePath(path)}`

const getAuthTokenOrThrow = (auth) => {
  const token = getAccessToken()
  if (auth && !token) {
    throw new ApiError('Please sign in before using this feature.', { status: 401 })
  }
  return token
}

const buildRequestHeaders = ({
  headers,
  auth,
  token,
  body,
  acceptSse = false
}) => {
  const requestHeaders = new Headers(getActiveLlmRequestHeaders())
  new Headers(headers || {}).forEach((value, key) => {
    requestHeaders.set(key, value)
  })
  if (acceptSse) {
    requestHeaders.set('Accept', 'text/event-stream')
  }
  if (auth && token) {
    requestHeaders.set('Authorization', `Bearer ${token}`)
  }
  if (body && !(body instanceof FormData)) {
    requestHeaders.set('Content-Type', 'application/json')
  }
  return requestHeaders
}

const buildRequestBody = (body) => {
  if (body == null) return undefined
  if (body instanceof FormData) return body
  return JSON.stringify(body)
}

const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    clearAuthSession()
    throw new ApiError('Login session expired, please sign in again.', { status: 401 })
  }

  if (!refreshPromise) {
    refreshPromise = (async () => {
      let response
      try {
        response = await fetch(buildUrl(REFRESH_PATH), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken })
        })
      } catch (error) {
        if (isNetworkError(error)) {
          throw createNetworkError(error)
        }
        throw error
      }

      const payload = await parseJsonSafely(response)
      if (!response.ok) {
        clearAuthSession()
        throw new ApiError(getErrorMessage(payload, response.status), {
          status: response.status,
          payload
        })
      }

      saveAuthSession({
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
        user: payload.user
      })

      return payload.access_token
    })().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

const shouldRefreshAndRetry = (response, { auth, path, attempt }) =>
  auth &&
  attempt === 0 &&
  response.status === 401 &&
  normalizePath(path) !== REFRESH_PATH

const parseSseBlock = (block) => {
  const lines = block.split('\n')
  let event = 'message'
  const dataLines = []

  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }

  const rawData = dataLines.join('\n')
  if (!rawData) {
    return { event, data: null }
  }

  try {
    return { event, data: JSON.parse(rawData) }
  } catch {
    return { event, data: rawData }
  }
}

const consumeSseStream = async (response, onEvent) => {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''

    for (const block of blocks) {
      if (!block.trim()) continue
      onEvent?.(parseSseBlock(block))
    }

    if (done) {
      if (buffer.trim()) {
        onEvent?.(parseSseBlock(buffer))
      }
      break
    }
  }
}

export const apiRequest = async (
  path,
  {
    method = 'GET',
    body,
    headers = {},
    auth = true,
    signal
  } = {}
) => {
  let token = getAuthTokenOrThrow(auth)

  for (let attempt = 0; attempt < 2; attempt += 1) {
    let response
    try {
      response = await fetch(buildUrl(path), {
        method,
        headers: buildRequestHeaders({ headers, auth, token, body }),
        body: buildRequestBody(body),
        signal
      })
    } catch (error) {
      if (isNetworkError(error)) {
        throw createNetworkError(error)
      }
      throw error
    }

    const payload = await parseJsonSafely(response)
    if (response.ok) {
      return payload
    }

    if (shouldRefreshAndRetry(response, { auth, path, attempt })) {
      token = await refreshAccessToken()
      continue
    }

    if (response.status === 401) {
      clearAuthSession()
    }

    throw new ApiError(getErrorMessage(payload, response.status), {
      status: response.status,
      payload
    })
  }

  throw new ApiError('Request failed after retry.', { status: 401 })
}

export const apiRawRequest = async (
  path,
  {
    method = 'GET',
    body,
    headers = {},
    auth = true,
    signal
  } = {}
) => {
  let token = getAuthTokenOrThrow(auth)

  for (let attempt = 0; attempt < 2; attempt += 1) {
    let response
    try {
      response = await fetch(buildUrl(path), {
        method,
        headers: buildRequestHeaders({ headers, auth, token, body }),
        body: buildRequestBody(body),
        signal
      })
    } catch (error) {
      if (isNetworkError(error)) {
        throw createNetworkError(error)
      }
      throw error
    }

    if (response.ok) {
      return response
    }

    const payload = await parseJsonSafely(response)
    if (shouldRefreshAndRetry(response, { auth, path, attempt })) {
      token = await refreshAccessToken()
      continue
    }

    if (response.status === 401) {
      clearAuthSession()
    }

    throw new ApiError(getErrorMessage(payload, response.status), {
      status: response.status,
      payload
    })
  }

  throw new ApiError('Request failed after retry.', { status: 401 })
}

export const streamSseRequest = async (
  path,
  { method = 'POST', body, headers = {}, auth = true, onEvent } = {}
) => {
  let token = getAuthTokenOrThrow(auth)

  for (let attempt = 0; attempt < 2; attempt += 1) {
    let response
    try {
      response = await fetch(buildUrl(path), {
        method,
        headers: buildRequestHeaders({
          headers,
          auth,
          token,
          body,
          acceptSse: true
        }),
        body: buildRequestBody(body)
      })
    } catch (error) {
      if (isNetworkError(error)) {
        throw createNetworkError(error)
      }
      throw error
    }

    if (response.ok && response.body) {
      await consumeSseStream(response, onEvent)
      return
    }

    const payload = await parseJsonSafely(response)
    if (shouldRefreshAndRetry(response, { auth, path, attempt })) {
      token = await refreshAccessToken()
      continue
    }

    if (response.status === 401) {
      clearAuthSession()
    }

    throw new ApiError(getErrorMessage(payload, response.status), {
      status: response.status,
      payload
    })
  }

  throw new ApiError('Streaming request failed after retry.', { status: 401 })
}
