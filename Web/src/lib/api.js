import { clearAuthSession, getAccessToken } from './auth'

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
export const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '')

export class ApiError extends Error {
  constructor(message, { status = 500, payload = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

const getErrorMessage = (payload, status) => {
  if (!payload) return `请求失败（${status}）`
  if (typeof payload === 'string') return payload
  if (typeof payload.detail === 'string') return payload.detail
  if (typeof payload.message === 'string') return payload.message
  return `请求失败（${status}）`
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
  const token = getAccessToken()
  if (auth && !token) {
    throw new ApiError('请先登录后再使用该功能。', { status: 401 })
  }

  const requestHeaders = new Headers(headers)
  if (auth && token) {
    requestHeaders.set('Authorization', `Bearer ${token}`)
  }

  let requestBody = body
  if (body && !(body instanceof FormData)) {
    requestHeaders.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body: requestBody,
    signal
  })

  const payload = await parseJsonSafely(response)
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthSession()
    }
    throw new ApiError(getErrorMessage(payload, response.status), {
      status: response.status,
      payload
    })
  }

  return payload
}

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

export const streamSseRequest = async (
  path,
  { method = 'POST', body, headers = {}, auth = true, onEvent } = {}
) => {
  const token = getAccessToken()
  if (auth && !token) {
    throw new ApiError('请先登录后再使用该功能。', { status: 401 })
  }

  const requestHeaders = new Headers(headers)
  requestHeaders.set('Accept', 'text/event-stream')
  if (auth && token) {
    requestHeaders.set('Authorization', `Bearer ${token}`)
  }
  if (body && !(body instanceof FormData)) {
    requestHeaders.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body: body instanceof FormData ? body : JSON.stringify(body)
  })

  if (!response.ok || !response.body) {
    const payload = await parseJsonSafely(response)
    if (response.status === 401) {
      clearAuthSession()
    }
    throw new ApiError(getErrorMessage(payload, response.status), {
      status: response.status,
      payload
    })
  }

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
