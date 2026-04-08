const ACCESS_TOKEN_KEY = 'xueta_access_token'
const REFRESH_TOKEN_KEY = 'xueta_refresh_token'
const USER_KEY = 'xueta_current_user'

const canUseStorage = () => typeof window !== 'undefined' && !!window.localStorage

export const getAccessToken = () => {
  if (!canUseStorage()) return ''
  return window.localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export const getRefreshToken = () => {
  if (!canUseStorage()) return ''
  return window.localStorage.getItem(REFRESH_TOKEN_KEY) || ''
}

export const getStoredUser = () => {
  if (!canUseStorage()) return null
  const raw = window.localStorage.getItem(USER_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const hasAccessToken = () => Boolean(getAccessToken())

export const saveAuthSession = ({ accessToken, refreshToken, user }) => {
  if (!canUseStorage()) return

  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  window.localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const clearAuthSession = () => {
  if (!canUseStorage()) return

  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
  window.localStorage.removeItem(REFRESH_TOKEN_KEY)
  window.localStorage.removeItem(USER_KEY)
}
