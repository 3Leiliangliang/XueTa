export const USER_SETTINGS_STORAGE_KEY = 'xueta_user_settings'

export const defaultUserSettings = {
  theme: 'system',
  density: 'comfortable',
  defaultEntry: '/desktop',
  dailyGoalMinutes: 60,
  defaultSubject: '',
  translateTarget: 'zh-CN',
  assistantAutoOpen: false,
  assistantVoice: true,
  autosaveNotes: true,
  focusMode: false,
  reviewReminder: true,
  weeklyDigest: true,
  reminderTime: '20:30',
  privacyAnalytics: false,
  customLlmEnabled: false,
  customLlmProvider: 'openai-compatible',
  customLlmBaseUrl: '',
  customLlmApiKey: '',
  customLlmModel: 'gpt-4o',
  customLlmEmbeddingModel: 'text-embedding-3-small',
  customLlmVisionModel: '',
  customLlmTimeoutSeconds: 20,
  customLlmTemperature: '',
  customLlmMaxTokens: ''
}

let mediaQuery = null
let mediaQueryHandler = null

export const getStoredSettings = () => {
  if (typeof localStorage === 'undefined') {
    return { ...defaultUserSettings }
  }

  try {
    const stored = JSON.parse(localStorage.getItem(USER_SETTINGS_STORAGE_KEY) || '{}')
    return {
      ...defaultUserSettings,
      ...stored
    }
  } catch {
    return { ...defaultUserSettings }
  }
}

const normalizeOptionalNumber = (value, fallback = '') => {
  if (value === '' || value == null) return fallback
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue : fallback
}

export const saveStoredSettings = (settings) => {
  const nextSettings = {
    ...defaultUserSettings,
    ...settings,
    customLlmBaseUrl: (settings.customLlmBaseUrl || '').trim().replace(/\/+$/, ''),
    customLlmApiKey: (settings.customLlmApiKey || '').trim(),
    customLlmModel: (settings.customLlmModel || defaultUserSettings.customLlmModel).trim(),
    customLlmEmbeddingModel: (
      settings.customLlmEmbeddingModel || defaultUserSettings.customLlmEmbeddingModel
    ).trim(),
    customLlmVisionModel: (settings.customLlmVisionModel || '').trim(),
    customLlmTimeoutSeconds: normalizeOptionalNumber(
      settings.customLlmTimeoutSeconds,
      defaultUserSettings.customLlmTimeoutSeconds
    ),
    customLlmTemperature: normalizeOptionalNumber(settings.customLlmTemperature),
    customLlmMaxTokens: normalizeOptionalNumber(settings.customLlmMaxTokens)
  }
  localStorage.setItem(USER_SETTINGS_STORAGE_KEY, JSON.stringify(nextSettings))
  return nextSettings
}

export const getActiveLlmRequestHeaders = (settings = getStoredSettings()) => {
  if (!settings.customLlmEnabled || !settings.customLlmApiKey || !settings.customLlmModel) {
    return {}
  }

  const headers = {
    'X-XueTa-LLM-Enabled': 'true',
    'X-XueTa-LLM-Provider': settings.customLlmProvider || 'openai-compatible',
    'X-XueTa-LLM-API-Key': settings.customLlmApiKey,
    'X-XueTa-LLM-Chat-Model': settings.customLlmModel
  }

  if (settings.customLlmBaseUrl) {
    headers['X-XueTa-LLM-Base-URL'] = settings.customLlmBaseUrl
  }

  if (settings.customLlmEmbeddingModel) {
    headers['X-XueTa-LLM-Embedding-Model'] = settings.customLlmEmbeddingModel
  }

  if (settings.customLlmVisionModel) {
    headers['X-XueTa-LLM-Vision-Model'] = settings.customLlmVisionModel
  }

  if (settings.customLlmTimeoutSeconds) {
    headers['X-XueTa-LLM-Timeout-Seconds'] = String(settings.customLlmTimeoutSeconds)
  }

  if (settings.customLlmTemperature !== '' && settings.customLlmTemperature != null) {
    headers['X-XueTa-LLM-Temperature'] = String(settings.customLlmTemperature)
  }

  if (settings.customLlmMaxTokens !== '' && settings.customLlmMaxTokens != null) {
    headers['X-XueTa-LLM-Max-Tokens'] = String(settings.customLlmMaxTokens)
  }

  return headers
}

export const resolveTheme = (theme) => {
  if (theme === 'dark') return 'dark'
  if (theme === 'light') return 'light'

  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  return 'light'
}

export const applyThemePreference = (theme) => {
  const preferredTheme = theme || getStoredSettings().theme
  const resolvedTheme = resolveTheme(preferredTheme)
  const root = document.documentElement

  root.dataset.xuetaTheme = preferredTheme
  root.dataset.xuetaResolvedTheme = resolvedTheme
  root.classList.toggle('dark', resolvedTheme === 'dark')
  root.style.colorScheme = resolvedTheme
}

export const initThemePreference = () => {
  const settings = getStoredSettings()
  applyThemePreference(settings.theme)

  if (!window.matchMedia) return

  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQueryHandler = () => {
    if (getStoredSettings().theme === 'system') {
      applyThemePreference('system')
    }
  }

  mediaQuery.addEventListener('change', mediaQueryHandler)
}

export const disposeThemePreference = () => {
  if (mediaQuery && mediaQueryHandler) {
    mediaQuery.removeEventListener('change', mediaQueryHandler)
  }
  mediaQuery = null
  mediaQueryHandler = null
}
