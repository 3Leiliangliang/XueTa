<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import IconQA from '@/components/icons/IconQA.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import IconSparkles from '@/components/icons/IconSparkles.vue'
import { apiRequest, streamSseRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const router = useRouter()

const composer = ref('')
const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const sessions = ref([])
const currentSessionId = ref('')
const chatMessages = ref([])
const isLoadingSessions = ref(false)
const isCreatingSession = ref(false)
const deletingSessionId = ref('')
const isAsking = ref(false)
const totalQuestionCount = ref(0)
const isReading = ref(false)
const isCollecting = ref(false)
const speechUtterance = ref(null)
const suppressSpeechError = ref(false)
const messageViewport = ref(null)
const composerTextarea = ref(null)
const isSidebarOpen = ref(false)
const isDesktopSidebarCollapsed = ref(false)
const isSessionSearchOpen = ref(false)
const sessionSearchQuery = ref('')
const showScrollToBottom = ref(false)
const sessionSearchInput = ref(null)
const SIDEBAR_COLLAPSE_KEY = 'qa_sidebar_collapsed'
const suggestedQuestions = [
  '如何高效预习一门新课程？',
  '帮我讲解一下链表和数组的区别。',
  '英语阅读理解有什么解题技巧？',
  '如何规划一周的学习时间？',
  '微积分中的极限应该怎么理解？',
  '请帮我分析这道概率题的解题思路。'
]

const FAVORITE_NOTEBOOK_NAME = 'AI问答收藏'

const normalizeCitations = (citations) =>
  Array.isArray(citations)
    ? citations.filter((item) => item && item.document_title)
    : []

const toSessionTime = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const displaySessionTitle = (session) => {
  const title = typeof session?.title === 'string' ? session.title.trim() : ''
  return title || '未命名会话'
}

const formattedQuestionCount = computed(() => totalQuestionCount.value.toLocaleString('zh-CN'))
const visibleMessages = computed(() =>
  chatMessages.value.filter((item) => item.role === 'user' || item.role === 'assistant')
)
const currentSession = computed(
  () => sessions.value.find((session) => session.id === currentSessionId.value) || null
)
const currentSessionTitle = computed(() => displaySessionTitle(currentSession.value))
const hasMessages = computed(() => visibleMessages.value.length > 0)
const isSidebarVisibleDesktop = computed(() => !isDesktopSidebarCollapsed.value)

const buildSessionGroups = (allSessions) => {
  const groups = [
    { key: 'today', label: '今天', items: [] },
    { key: 'yesterday', label: '昨天', items: [] },
    { key: 'within7', label: '7 天内', items: [] },
    { key: 'within30', label: '30 天内', items: [] },
    { key: 'earlier', label: '更早', items: [] }
  ]

  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const oneDay = 24 * 60 * 60 * 1000

  for (const session of allSessions) {
    const rawTime = session.updated_at || session.created_at
    const timestamp = rawTime ? new Date(rawTime).getTime() : Number.NaN

    if (Number.isNaN(timestamp)) {
      groups[4].items.push(session)
      continue
    }

    const diffDays = Math.floor((todayStart - timestamp) / oneDay)
    if (diffDays <= 0) {
      groups[0].items.push(session)
    } else if (diffDays === 1) {
      groups[1].items.push(session)
    } else if (diffDays <= 7) {
      groups[2].items.push(session)
    } else if (diffDays <= 30) {
      groups[3].items.push(session)
    } else {
      groups[4].items.push(session)
    }
  }

  return groups.filter((group) => group.items.length)
}

const filteredSessions = computed(() => {
  const keyword = sessionSearchQuery.value.trim().toLowerCase()
  if (!keyword) return sessions.value
  return sessions.value.filter((session) =>
    displaySessionTitle(session).toLowerCase().includes(keyword)
  )
})
const groupedFilteredSessions = computed(() => buildSessionGroups(filteredSessions.value))

const latestAssistantMessage = computed(() => {
  for (let index = visibleMessages.value.length - 1; index >= 0; index -= 1) {
    const message = visibleMessages.value[index]
    if (message.role === 'assistant' && message.content.trim() && !message.pending) {
      return message
    }
  }
  return null
})

const currentSourceCount = computed(() => latestAssistantMessage.value?.citations?.length || 0)

const canCollectLatestAnswer = computed(() => {
  const message = latestAssistantMessage.value
  if (!message?.id) return false
  return typeof message.id === 'string' && !message.id.startsWith('local-')
})

const isNearBottom = (target) => {
  if (!target) return true
  return target.scrollHeight - target.scrollTop - target.clientHeight < 120
}

const scrollMessagesToBottom = async (smooth = false) => {
  await nextTick()
  const target = messageViewport.value
  if (!target) return
  target.scrollTo({
    top: target.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  })
  showScrollToBottom.value = false
}

const handleMessageScroll = () => {
  const target = messageViewport.value
  if (!target) return
  showScrollToBottom.value = !isNearBottom(target)
}

const autoResizeComposer = () => {
  const target = composerTextarea.value
  if (!target) return
  target.style.height = 'auto'
  target.style.height = `${Math.min(target.scrollHeight, 180)}px`
}

const loadQuestionStats = async () => {
  if (!hasAccessToken()) {
    totalQuestionCount.value = 0
    return
  }

  try {
    const overview = await apiRequest('/progress/overview')
    totalQuestionCount.value = Number(overview?.stats?.total_chat_questions || 0)
  } catch {
    // Ignore stats refresh failure.
  }
}

const resetConversationView = () => {
  chatMessages.value = []
}

const loadSessionMessages = async (sessionId) => {
  if (!sessionId) {
    resetConversationView()
    return
  }

  if (isReading.value) {
    stopReading()
  }

  const messages = await apiRequest(`/chat/sessions/${sessionId}/messages`)
  chatMessages.value = messages
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .map((item) => ({
      id: item.id,
      role: item.role,
      content: item.content || '',
      citations: normalizeCitations(item.citations_json),
      pending: false
    }))

  await scrollMessagesToBottom()
}

const loadSessions = async (
  { targetSessionId = '', fallbackToLatest = false, keepMessages = false } = {}
) => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 答疑中心。'
    sessions.value = []
    currentSessionId.value = ''
    resetConversationView()
    return
  }

  isLoadingSessions.value = true
  try {
    authMessage.value = ''
    errorMessage.value = ''
    const payload = await apiRequest('/chat/sessions')
    sessions.value = [...payload].sort((left, right) => {
      const leftTime = new Date(left.updated_at || left.created_at || 0).getTime()
      const rightTime = new Date(right.updated_at || right.created_at || 0).getTime()
      return rightTime - leftTime
    })

    if (!sessions.value.length) {
      currentSessionId.value = ''
      if (!keepMessages) {
        resetConversationView()
      }
      return
    }

    const previousSessionId = currentSessionId.value
    const preferredSessionId =
      targetSessionId ||
      (sessions.value.some((session) => session.id === currentSessionId.value)
        ? currentSessionId.value
        : '')

    const nextSessionId =
      preferredSessionId ||
      (fallbackToLatest ? sessions.value[0].id : currentSessionId.value) ||
      sessions.value[0].id

    currentSessionId.value = nextSessionId

    const shouldReloadMessages =
      !keepMessages || previousSessionId !== nextSessionId || !visibleMessages.value.length
    if (shouldReloadMessages) {
      await loadSessionMessages(nextSessionId)
    }
  } catch (error) {
    errorMessage.value = error.message || '加载答疑历史失败，请稍后重试。'
  } finally {
    isLoadingSessions.value = false
  }
}

const ensureSession = async () => {
  if (currentSessionId.value) return currentSessionId.value

  const session = await apiRequest('/chat/sessions', {
    method: 'POST',
    body: {
      title: null,
      subject: null
    }
  })

  currentSessionId.value = session.id
  sessions.value.unshift(session)
  return session.id
}

const selectSession = async (sessionId) => {
  if (!sessionId || sessionId === currentSessionId.value) return
  currentSessionId.value = sessionId
  isSidebarOpen.value = false
  statusMessage.value = ''
  errorMessage.value = ''
  await loadSessionMessages(sessionId)
}

const createNewSession = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 答疑中心。'
    return
  }
  if (isCreatingSession.value) return

  isCreatingSession.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const session = await apiRequest('/chat/sessions', {
      method: 'POST',
      body: {
        title: null,
        subject: null
      }
    })
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    isSidebarOpen.value = false
    resetConversationView()
    statusMessage.value = '已新建会话。'
    await scrollMessagesToBottom()
    composerTextarea.value?.focus()
  } catch (error) {
    errorMessage.value = error.message || '新建会话失败，请稍后重试。'
  } finally {
    isCreatingSession.value = false
  }
}

const deleteSession = async (sessionId) => {
  if (!sessionId || deletingSessionId.value) return
  if (!window.confirm('确定删除这个会话吗？')) return

  deletingSessionId.value = sessionId
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    await apiRequest(`/chat/sessions/${sessionId}`, {
      method: 'DELETE'
    })

    sessions.value = sessions.value.filter((session) => session.id !== sessionId)

    if (currentSessionId.value === sessionId) {
      currentSessionId.value = sessions.value[0]?.id || ''
      if (currentSessionId.value) {
        await loadSessionMessages(currentSessionId.value)
      } else {
        resetConversationView()
      }
    }

    statusMessage.value = '会话已删除。'
  } catch (error) {
    errorMessage.value = error.message || '删除会话失败，请稍后重试。'
  } finally {
    deletingSessionId.value = ''
  }
}

const setStreamingMessageContent = (messageId, updater) => {
  const index = chatMessages.value.findIndex((item) => item.id === messageId)
  if (index < 0) return
  const target = chatMessages.value[index]
  chatMessages.value[index] = {
    ...target,
    content: typeof updater === 'function' ? updater(target.content || '') : updater
  }
}

const replaceMessage = (messageId, nextMessage) => {
  const index = chatMessages.value.findIndex((item) => item.id === messageId)
  if (index < 0) return
  chatMessages.value[index] = nextMessage
}

const askQuestion = async () => {
  if (!composer.value.trim() || isAsking.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 答疑中心。'
    return
  }

  const userQuestion = composer.value.trim()
  composer.value = ''
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''
  isAsking.value = true

  if (isReading.value) {
    stopReading()
  }

  const userMessageId = `local-user-${Date.now()}`
  const assistantMessageId = `local-assistant-${Date.now()}`
  chatMessages.value.push(
    {
      id: userMessageId,
      role: 'user',
      content: userQuestion,
      citations: [],
      pending: false
    },
    {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      citations: [],
      pending: true
    }
  )

  await scrollMessagesToBottom(true)

  try {
    const sessionId = await ensureSession()

    await streamSseRequest(`/chat/sessions/${sessionId}/messages/stream`, {
      body: { content: userQuestion },
      onEvent: ({ event, data }) => {
        if (event === 'message_start') {
          setStreamingMessageContent(assistantMessageId, '')
          return
        }

        if (event === 'delta' && data?.delta) {
          setStreamingMessageContent(assistantMessageId, (prev) => `${prev}${data.delta}`)
          scrollMessagesToBottom()
          return
        }

        if (event === 'message_end' && data?.assistant_message) {
          replaceMessage(assistantMessageId, {
            id: data.assistant_message.id,
            role: 'assistant',
            content: data.assistant_message.content || '',
            citations: normalizeCitations(data.assistant_message.citations_json),
            pending: false
          })
          scrollMessagesToBottom()
        }
      }
    })

    await loadSessions({
      targetSessionId: sessionId,
      keepMessages: true
    })
    await loadQuestionStats()
  } catch (error) {
    replaceMessage(assistantMessageId, {
      id: assistantMessageId,
      role: 'assistant',
      content: '本次回答生成失败，请稍后重试。',
      citations: [],
      pending: false
    })
    errorMessage.value = error.message || '提问失败，请稍后重试。'
  } finally {
    isAsking.value = false
    await scrollMessagesToBottom()
  }
}

const useSuggested = (question) => {
  composer.value = question
  nextTick(() => {
    composerTextarea.value?.focus()
    autoResizeComposer()
  })
}

const handleComposerKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    askQuestion()
  }
}

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const toggleDesktopSidebar = () => {
  isDesktopSidebarCollapsed.value = !isDesktopSidebarCollapsed.value
}

const hideSidebar = () => {
  isSidebarOpen.value = false
  if (typeof window === 'undefined') return
  if (window.matchMedia('(min-width: 1024px)').matches) {
    isDesktopSidebarCollapsed.value = true
  }
}

const focusSessionSearch = () => {
  nextTick(() => {
    sessionSearchInput.value?.focus()
  })
}

const openSessionSearch = () => {
  isSessionSearchOpen.value = true
  isDesktopSidebarCollapsed.value = false
  isSidebarOpen.value = true
  focusSessionSearch()
}

const toggleSessionSearch = () => {
  isSessionSearchOpen.value = !isSessionSearchOpen.value
  if (isSessionSearchOpen.value) {
    focusSessionSearch()
  } else {
    sessionSearchQuery.value = ''
  }
}

const loadSidebarPreference = () => {
  if (typeof window === 'undefined') return
  isDesktopSidebarCollapsed.value = window.localStorage.getItem(SIDEBAR_COLLAPSE_KEY) === '1'
}

const stopReading = ({ showStatus = false } = {}) => {
  if (typeof window === 'undefined' || !window.speechSynthesis) return
  suppressSpeechError.value = true
  window.speechSynthesis.cancel()
  isReading.value = false
  speechUtterance.value = null
  if (showStatus) {
    errorMessage.value = ''
    statusMessage.value = '已停止朗读。'
  }
  window.setTimeout(() => {
    suppressSpeechError.value = false
  }, 0)
}

const readAnswer = () => {
  const answerText = latestAssistantMessage.value?.content?.trim() || ''
  if (!answerText) {
    statusMessage.value = '当前没有可朗读内容。'
    return
  }

  if (typeof window === 'undefined' || !window.speechSynthesis) {
    errorMessage.value = '当前浏览器不支持朗读功能。'
    return
  }

  if (isReading.value) {
    stopReading({ showStatus: true })
    return
  }

  errorMessage.value = ''
  statusMessage.value = ''
  const utterance = new SpeechSynthesisUtterance(answerText)
  utterance.lang = 'zh-CN'
  utterance.rate = 1
  utterance.pitch = 1
  utterance.onend = () => {
    isReading.value = false
    speechUtterance.value = null
  }
  utterance.onerror = () => {
    if (suppressSpeechError.value) return
    isReading.value = false
    speechUtterance.value = null
    errorMessage.value = '朗读失败，请稍后重试。'
  }

  speechUtterance.value = utterance
  isReading.value = true
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(utterance)
}

const ensureFavoriteNotebookId = async () => {
  const notebooks = await apiRequest('/notes/notebooks')
  const existing = notebooks.find((item) => item.name === FAVORITE_NOTEBOOK_NAME)
  if (existing) return existing.id

  const created = await apiRequest('/notes/notebooks', {
    method: 'POST',
    body: {
      name: FAVORITE_NOTEBOOK_NAME,
      description: '保存 AI 答疑收藏内容'
    }
  })
  return created.id
}

const buildFavoriteMarkdown = ({ questionText, answerText, citations }) => {
  const citationText = (citations || []).length
    ? (citations || [])
        .map((item, index) => {
          const title = item?.document_title || `来源 ${index + 1}`
          const content = item?.content || ''
          return `[${index + 1}] ${title}\n${content}`
        })
        .join('\n\n')
    : '无引用来源'

  return [
    '## 问题',
    questionText || '未记录问题',
    '',
    '## 回答',
    answerText || '',
    '',
    '## 引用来源',
    citationText
  ].join('\n')
}

const findQuestionForAssistant = (assistantMessageId) => {
  let pendingQuestion = ''
  for (const message of visibleMessages.value) {
    if (message.role === 'user') {
      pendingQuestion = message.content || ''
      continue
    }
    if (message.role === 'assistant' && message.id === assistantMessageId) {
      return pendingQuestion
    }
  }
  return pendingQuestion
}

const collectAnswer = async () => {
  if (isCollecting.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再收藏回答。'
    return
  }
  if (!canCollectLatestAnswer.value || !latestAssistantMessage.value?.content?.trim()) {
    statusMessage.value = '当前回答尚未生成完成，请稍后再收藏。'
    return
  }

  isCollecting.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const notebookId = await ensureFavoriteNotebookId()
    const targetMessage = latestAssistantMessage.value
    const questionText = findQuestionForAssistant(targetMessage.id).trim()
    const titleSeed = (questionText || '未命名问题').replace(/\s+/g, ' ').slice(0, 28)

    await apiRequest('/notes', {
      method: 'POST',
      body: {
        notebook_id: notebookId,
        title: `问答收藏：${titleSeed}`,
        content_markdown: buildFavoriteMarkdown({
          questionText,
          answerText: targetMessage.content,
          citations: targetMessage.citations || []
        }),
        source_type: 'qa_favorite',
        metadata_json: {
          source: 'qa',
          session_id: currentSessionId.value || null,
          message_id: targetMessage.id || null,
          citations: targetMessage.citations || []
        }
      }
    })

    statusMessage.value = '已收藏到「AI问答收藏」笔记本。'
  } catch (error) {
    errorMessage.value = error.message || '收藏失败，请稍后重试。'
  } finally {
    isCollecting.value = false
  }
}

const jumpToKnowledgeDocument = (citation) => {
  if (!citation?.document_id) return
  router.push({
    path: '/kb',
    query: {
      documentId: citation.document_id
    }
  })
}

const jumpToKnowledgeChunk = (citation) => {
  if (!citation?.document_id || !citation?.chunk_id) return
  router.push({
    path: '/kb',
    query: {
      documentId: citation.document_id,
      chunkId: citation.chunk_id
    }
  })
}

const escapeHtml = (value) =>
  String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const sanitizeUrl = (url) => {
  const raw = String(url || '').trim()
  if (!raw) return '#'
  const lower = raw.toLowerCase()
  if (lower.startsWith('http://') || lower.startsWith('https://') || lower.startsWith('mailto:')) {
    return raw
  }
  return '#'
}

const escapeAttr = (value) =>
  String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

const renderInlineMarkdown = (source) => {
  let text = escapeHtml(source || '')
  const codeTokens = []

  text = text.replace(/`([^`\n]+)`/g, (_, code) => {
    const token = `%%CODETOKEN${codeTokens.length}%%`
    codeTokens.push(
      `<code class="rounded bg-slate-100 px-1.5 py-0.5 text-[12px] text-slate-700">${code}</code>`
    )
    return token
  })

  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
    const safeUrl = sanitizeUrl(url)
    return `<a href="${escapeHtml(
      safeUrl
    )}" target="_blank" rel="noopener noreferrer" class="text-[#3A86FF] hover:underline">${label}</a>`
  })

  text = text.replace(
    /(^|[\s(])(https?:\/\/[^\s<]+)/g,
    (_, prefix, url) =>
      `${prefix}<a href="${escapeHtml(
        sanitizeUrl(url)
      )}" target="_blank" rel="noopener noreferrer" class="text-[#3A86FF] hover:underline">${escapeHtml(
        url
      )}</a>`
  )

  text = text
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
    .replace(/_([^_\n]+)_/g, '<em>$1</em>')
    .replace(/~~([^~]+)~~/g, '<del>$1</del>')

  codeTokens.forEach((html, index) => {
    text = text.replace(`%%CODETOKEN${index}%%`, html)
  })

  return text
}

const renderMarkdown = (source) => {
  const markdown = String(source || '').replace(/\r\n/g, '\n')
  if (!markdown.trim()) return ''

  const lines = markdown.split('\n')
  const html = []
  let index = 0
  let paragraphLines = []
  let listType = ''
  let listItems = []
  let quoteLines = []
  let tableHeader = null
  let tableRows = []

  const flushParagraph = () => {
    if (!paragraphLines.length) return
    html.push(
      `<p class="mb-3 last:mb-0 leading-7">${renderInlineMarkdown(paragraphLines.join('\n')).replace(
        /\n/g,
        '<br />'
      )}</p>`
    )
    paragraphLines = []
  }

  const flushList = () => {
    if (!listItems.length) return
    const tag = listType === 'ol' ? 'ol' : 'ul'
    const className =
      listType === 'ol'
        ? 'mb-3 list-decimal pl-6 space-y-1'
        : 'mb-3 list-disc pl-6 space-y-1'
    html.push(
      `<${tag} class="${className}">${listItems
        .map((item) => {
          if (typeof item === 'object' && item?.type === 'task') {
            return `<li class="list-none -ml-6"><span class="mr-1 inline-block align-middle">${item.checked ? '☑' : '☐'}</span>${renderInlineMarkdown(item.text)}</li>`
          }
          return `<li>${renderInlineMarkdown(item)}</li>`
        })
        .join('')}</${tag}>`
    )
    listItems = []
    listType = ''
  }

  const flushQuote = () => {
    if (!quoteLines.length) return
    html.push(
      `<blockquote class="mb-3 border-l-4 border-[#3A86FF]/50 bg-slate-50 px-3 py-2 text-slate-600">${renderInlineMarkdown(
        quoteLines.join('\n')
      ).replace(/\n/g, '<br />')}</blockquote>`
    )
    quoteLines = []
  }

  const flushTable = () => {
    if (!tableHeader?.length) return
    const headerHtml = tableHeader.map((cell) => `<th>${renderInlineMarkdown(cell)}</th>`).join('')
    const bodyHtml = tableRows
      .map((row) => `<tr>${row.map((cell) => `<td>${renderInlineMarkdown(cell)}</td>`).join('')}</tr>`)
      .join('')
    html.push(
      `<div class="mb-3 overflow-x-auto"><table class="markdown-table w-full min-w-[420px] border-collapse text-left"><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`
    )
    tableHeader = null
    tableRows = []
  }

  const splitTableRow = (line) =>
    line
      .split('|')
      .map((item) => item.trim())
      .filter((item, idx, arr) => !(idx === 0 && item === '') && !(idx === arr.length - 1 && item === ''))

  const flushAll = () => {
    flushParagraph()
    flushList()
    flushQuote()
    flushTable()
  }

  while (index < lines.length) {
    const line = lines[index]
    const trimmed = line.trim()

    if (trimmed.startsWith('```')) {
      flushAll()
      const language = escapeHtml(trimmed.slice(3).trim())
      const codeLines = []
      index += 1
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        codeLines.push(lines[index])
        index += 1
      }
      const encodedCode = encodeURIComponent(codeLines.join('\n'))
      html.push(
        `<div class="group relative mb-3"><button type="button" data-code="${escapeAttr(
          encodedCode
        )}" class="copy-code-btn absolute right-2 top-2 rounded-md border border-slate-600 bg-slate-800/80 px-2 py-0.5 text-[10px] text-slate-200 opacity-0 transition-opacity hover:bg-slate-700 group-hover:opacity-100">复制</button><pre class="overflow-x-auto rounded-xl border border-slate-200 bg-slate-900/95 p-3 text-xs leading-6 text-slate-100"><code class="language-${language}">${escapeHtml(
          codeLines.join('\n')
        )}</code></pre></div>`
      )
      index += 1
      continue
    }

    if (
      line.includes('|') &&
      index + 1 < lines.length &&
      lines[index + 1].trim().match(/^(\|?\s*:?-{3,}:?\s*)+\|?$/)
    ) {
      flushAll()
      tableHeader = splitTableRow(line)
      tableRows = []
      index += 2
      while (index < lines.length && lines[index].includes('|') && lines[index].trim()) {
        tableRows.push(splitTableRow(lines[index]))
        index += 1
      }
      flushTable()
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/)
    if (headingMatch) {
      flushAll()
      const level = headingMatch[1].length
      const headingText = renderInlineMarkdown(headingMatch[2])
      const sizeClass =
        level <= 2 ? 'text-lg font-semibold' : level === 3 ? 'text-base font-semibold' : 'text-sm font-semibold'
      html.push(`<h${level} class="mb-2 ${sizeClass} text-slate-900">${headingText}</h${level}>`)
      index += 1
      continue
    }

    const quoteMatch = line.match(/^\s*>\s?(.*)$/)
    if (quoteMatch) {
      flushParagraph()
      flushList()
      flushTable()
      quoteLines.push(quoteMatch[1])
      index += 1
      continue
    }

    const unorderedMatch = line.match(/^\s*[-*+]\s+(.+)$/)
    if (unorderedMatch) {
      flushParagraph()
      flushQuote()
      flushTable()
      if (listType && listType !== 'ul') {
        flushList()
      }
      listType = 'ul'
      const taskMatch = unorderedMatch[1].match(/^\[(x|X| )\]\s+(.+)$/)
      if (taskMatch) {
        const checked = taskMatch[1].toLowerCase() === 'x'
        listItems.push({
          type: 'task',
          checked,
          text: taskMatch[2]
        })
      } else {
        listItems.push(unorderedMatch[1])
      }
      index += 1
      continue
    }

    const orderedMatch = line.match(/^\s*\d+\.\s+(.+)$/)
    if (orderedMatch) {
      flushParagraph()
      flushQuote()
      flushTable()
      if (listType && listType !== 'ol') {
        flushList()
      }
      listType = 'ol'
      listItems.push(orderedMatch[1])
      index += 1
      continue
    }

    if (trimmed.match(/^(-{3,}|\*{3,}|_{3,})$/)) {
      flushAll()
      html.push('<hr class="mb-3 border-slate-200" />')
      index += 1
      continue
    }

    if (!trimmed) {
      flushAll()
      index += 1
      continue
    }

    flushQuote()
    flushList()
    flushTable()
    paragraphLines.push(line)
    index += 1
  }

  flushAll()
  return html.join('')
}

const renderAssistantMessage = (message) => renderMarkdown(message.content || '')

const handleMarkdownClick = async (event) => {
  const target = event.target
  if (!(target instanceof HTMLElement)) return

  const copyButton = target.closest('.copy-code-btn')
  if (!copyButton) return

  const encoded = copyButton.getAttribute('data-code') || ''
  if (!encoded) return

  try {
    await navigator.clipboard.writeText(decodeURIComponent(encoded))
    statusMessage.value = '代码已复制。'
  } catch {
    errorMessage.value = '复制失败，请手动复制。'
  }
}

onMounted(() => {
  loadSidebarPreference()
  loadSessions({ fallbackToLatest: true })
  loadQuestionStats()
  nextTick(autoResizeComposer)
})

onUnmounted(() => {
  stopReading()
})

watch(composer, () => {
  nextTick(autoResizeComposer)
})

watch(hasMessages, () => {
  nextTick(autoResizeComposer)
})

watch(isDesktopSidebarCollapsed, (value) => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(SIDEBAR_COLLAPSE_KEY, value ? '1' : '0')
})
</script>

<template>
  <div class="relative bg-[#f5f6f8]">
    <div
      v-if="isSidebarOpen"
      class="absolute inset-0 z-20 bg-slate-900/30 lg:hidden"
      @click="isSidebarOpen = false"
    />

    <section class="qa-stage relative flex h-[calc(100vh-4rem)] min-h-[560px] overflow-hidden flex-col lg:flex-row">
      <aside
        :class="[
          'absolute inset-y-0 left-0 z-30 flex w-[292px] shrink-0 flex-col border-r border-slate-200 bg-[#f0f1f4] transition-all duration-300 ease-out lg:relative lg:translate-x-0',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
          isSidebarVisibleDesktop
            ? 'lg:w-[292px] lg:opacity-100'
            : 'lg:w-0 lg:min-w-0 lg:overflow-hidden lg:border-r-0 lg:opacity-0 lg:pointer-events-none'
        ]"
      >
        <div class="border-b border-slate-200 px-4 pb-4 pt-5">
          <div class="flex items-center justify-between gap-3 text-[#3A86FF]">
            <div class="flex min-w-0 items-center gap-2">
              <IconQA class="h-7 w-7 shrink-0" />
              <span class="truncate text-2xl font-semibold leading-none">XueTa</span>
            </div>
            <div class="flex shrink-0 items-center gap-1 text-slate-600">
              <button
                type="button"
                class="nav-icon-btn btn-pop"
                :class="isSessionSearchOpen ? 'text-[#3A86FF]' : ''"
                title="搜索会话"
                aria-label="搜索会话"
                @click="toggleSessionSearch"
              >
                <IconSearch class="h-5 w-5" />
              </button>
              <button
                type="button"
                class="nav-icon-btn btn-pop"
                title="隐藏侧边栏"
                aria-label="隐藏侧边栏"
                @click="hideSidebar"
              >
                <svg
                  class="h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect width="16" height="18" x="4" y="3" rx="2" />
                  <path d="M10 3v18" />
                </svg>
              </button>
            </div>
          </div>
          <div v-if="isSessionSearchOpen" class="mt-4">
            <label class="relative block">
              <IconSearch class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                ref="sessionSearchInput"
                v-model="sessionSearchQuery"
                type="search"
                class="h-10 w-full rounded-2xl border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-[#3A86FF]"
                placeholder="搜索历史会话"
              />
            </label>
          </div>
          <button
            type="button"
            class="mt-4 w-full rounded-2xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF] disabled:opacity-60"
            :disabled="isCreatingSession"
            @click="createNewSession"
          >
            {{ isCreatingSession ? '新建中...' : '⊕ 开启新对话' }}
          </button>
          <p class="mt-2 px-1 text-[11px] text-slate-400">共 {{ sessions.length }} 个会话</p>
        </div>

        <div class="min-h-0 flex-1 overflow-y-auto px-3 py-4">
          <div v-if="isLoadingSessions" class="px-2 py-2 text-xs text-slate-400">会话加载中...</div>
          <template v-for="group in groupedFilteredSessions" :key="group.key">
            <section class="mb-4">
              <p class="px-2 text-xs font-medium text-slate-400">{{ group.label }}</p>
              <div class="mt-2 space-y-1">
                <div
                  v-for="session in group.items"
                  :key="session.id"
                  role="button"
                  tabindex="0"
                  :class="[
                    'session-item group w-full cursor-pointer rounded-xl px-2.5 py-2.5 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-[#3A86FF]/40',
                    currentSessionId === session.id
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-600 hover:bg-white/80'
                  ]"
                  @click="selectSession(session.id)"
                  @keydown.enter.prevent="selectSession(session.id)"
                  @keydown.space.prevent="selectSession(session.id)"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0">
                      <p class="truncate text-[14px]">{{ displaySessionTitle(session) }}</p>
                      <p class="mt-1 text-[10px] text-slate-400">
                        {{ toSessionTime(session.updated_at || session.created_at) }}
                      </p>
                    </div>
                    <button
                      type="button"
                      class="rounded px-1 text-[12px] text-rose-500 opacity-0 transition-opacity hover:underline group-hover:opacity-100 group-focus-within:opacity-100 disabled:opacity-40"
                      :disabled="deletingSessionId === session.id"
                      @click.stop="deleteSession(session.id)"
                    >
                      {{ deletingSessionId === session.id ? '...' : '×' }}
                    </button>
                  </div>
                </div>
              </div>
            </section>
          </template>
          <p v-if="!filteredSessions.length && !isLoadingSessions" class="px-2 py-2 text-xs text-slate-400">
            {{ sessionSearchQuery.trim() ? '没有匹配的会话' : '还没有历史会话' }}
          </p>
        </div>
      </aside>

      <Transition name="float-dock">
        <div
          v-if="!isSidebarVisibleDesktop"
          class="qa-floating-dock absolute left-5 top-4 z-20 hidden items-center gap-2 rounded-full border border-slate-200 bg-white/95 px-2.5 py-2 text-slate-900 shadow-[0_10px_30px_rgba(15,23,42,0.12)] backdrop-blur lg:flex"
        >
          <IconQA class="mr-1 h-7 w-7 text-[#3A86FF]" />
          <button
            type="button"
            class="floating-icon-btn btn-pop"
            title="展开侧边栏"
            aria-label="展开侧边栏"
            @click="toggleDesktopSidebar"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect width="16" height="18" x="4" y="3" rx="2" />
              <path d="M10 3v18" />
            </svg>
          </button>
          <button
            type="button"
            class="floating-icon-btn btn-pop"
            title="搜索会话"
            aria-label="搜索会话"
            @click="openSessionSearch"
          >
            <IconSearch class="h-5 w-5" />
          </button>
          <button
            type="button"
            class="floating-icon-btn btn-pop"
            title="新对话"
            aria-label="新对话"
            :disabled="isCreatingSession"
            @click="createNewSession"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v8" />
              <path d="M8 12h8" />
            </svg>
          </button>
        </div>
      </Transition>

      <Transition name="float-dock">
        <div
          v-if="!isSidebarOpen"
          class="qa-floating-dock absolute left-4 top-4 z-20 flex items-center gap-2 rounded-full border border-slate-200 bg-white/95 px-2.5 py-2 text-slate-900 shadow-[0_10px_30px_rgba(15,23,42,0.12)] backdrop-blur lg:hidden"
        >
          <IconQA class="mr-1 h-7 w-7 text-[#3A86FF]" />
          <button
            type="button"
            class="floating-icon-btn btn-pop"
            title="展开侧边栏"
            aria-label="展开侧边栏"
            @click="toggleSidebar"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect width="16" height="18" x="4" y="3" rx="2" />
              <path d="M10 3v18" />
            </svg>
          </button>
          <button
            type="button"
            class="floating-icon-btn btn-pop"
            title="搜索会话"
            aria-label="搜索会话"
            @click="openSessionSearch"
          >
            <IconSearch class="h-5 w-5" />
          </button>
          <button
            type="button"
            class="floating-icon-btn btn-pop"
            title="新对话"
            aria-label="新对话"
            :disabled="isCreatingSession"
            @click="createNewSession"
          >
            <svg
              class="h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v8" />
              <path d="M8 12h8" />
            </svg>
          </button>
        </div>
      </Transition>

      <section class="relative flex min-w-0 flex-1 flex-col">
        <header class="flex h-14 items-center justify-between border-b border-slate-200 bg-[#f8f9fb] px-5">
          <div
            :class="[
              'flex min-w-0 items-center gap-3',
              isSidebarVisibleDesktop ? '' : 'lg:pl-[210px]'
            ]"
          >
            <p class="hidden truncate text-sm font-medium text-slate-700 sm:block">{{ currentSessionTitle }}</p>
          </div>
          <div class="flex items-center gap-2 text-[11px] text-slate-500">
            <span class="hidden md:inline">累计提问 {{ formattedQuestionCount }}</span>
            <button
              type="button"
              class="btn-pop rounded px-2 py-1 hover:bg-slate-200 disabled:opacity-50"
              :disabled="!latestAssistantMessage?.content?.trim()"
              @click="readAnswer"
            >
              {{ isReading ? '停止朗读' : '朗读' }}
            </button>
            <button
              type="button"
              class="btn-pop rounded px-2 py-1 hover:bg-slate-200 disabled:opacity-50"
              :disabled="isCollecting || !canCollectLatestAnswer"
              @click="collectAnswer"
            >
              {{ isCollecting ? '收藏中' : '收藏' }}
            </button>
          </div>
        </header>

        <div
          v-if="authMessage || errorMessage || statusMessage"
          class="border-b border-slate-200 bg-white px-5 py-3 space-y-2"
        >
          <p v-if="authMessage" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
            {{ authMessage }}
          </p>
          <p v-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">
            {{ errorMessage }}
          </p>
          <p v-if="statusMessage" class="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
            {{ statusMessage }}
          </p>
        </div>

        <div
          ref="messageViewport"
          class="flex-1 overflow-y-auto bg-[#f8f9fb]"
          @scroll="handleMessageScroll"
        >
          <div v-if="!hasMessages" class="flex h-full min-h-[480px] items-center justify-center px-5 py-10">
            <div class="empty-hero w-full max-w-2xl text-center">
              <div class="flex items-center justify-center gap-2 text-[#3A86FF]">
                <IconSparkles class="h-6 w-6" />
                <h2 class="text-3xl font-semibold leading-tight text-slate-900 md:text-[38px]">开始新的答疑对话</h2>
              </div>

              <div class="mt-8 rounded-3xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <textarea
                  ref="composerTextarea"
                  v-model="composer"
                  rows="3"
                  class="w-full max-h-[180px] resize-none overflow-y-auto border-none bg-transparent text-base leading-7 text-slate-700 outline-none placeholder:text-slate-400"
                  placeholder="给学塔 AI 发送消息"
                  @keydown="handleComposerKeydown"
                />
                <div class="mt-2 flex flex-wrap items-center justify-between gap-3">
                  <div class="flex items-center gap-2 text-xs text-slate-400">
                    <button
                      v-for="item in suggestedQuestions.slice(0, 3)"
                      :key="item"
                      type="button"
                      class="btn-pop rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] text-slate-500 transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF]"
                      @click="useSuggested(item)"
                    >
                      {{ item }}
                    </button>
                  </div>
                  <button
                    type="button"
                    class="btn-pop h-9 w-9 rounded-full bg-[#9fb7ff] text-lg text-white transition-colors hover:bg-[#88a7ff] disabled:opacity-60"
                    :disabled="isAsking || !composer.trim()"
                    @click="askQuestion"
                  >
                    ↑
                  </button>
                </div>
              </div>
            </div>
          </div>

          <TransitionGroup
            v-else
            name="msg"
            tag="div"
            class="mx-auto w-full max-w-5xl space-y-5 px-4 py-6 md:px-6"
          >
            <article
              v-for="message in visibleMessages"
              :key="message.id"
              :class="['flex', message.role === 'user' ? 'justify-end' : 'justify-start']"
            >
              <div
                :class="[
                  'rounded-2xl px-4 py-3 shadow-sm',
                  message.role === 'user'
                    ? 'max-w-[78%] bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white'
                    : 'max-w-[90%] border border-slate-200 bg-white text-slate-700 md:max-w-[84%]'
                ]"
              >
                <p v-if="message.role === 'user'" class="whitespace-pre-wrap text-sm leading-7">
                  {{ message.content }}
                </p>

                <div v-else>
                  <div v-if="message.pending" class="flex items-center gap-2 text-sm text-slate-500">
                    <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-[#3A86FF]" />
                    <span>正在思考...</span>
                  </div>
                  <div
                    v-else
                    class="markdown-body text-sm text-slate-700"
                    v-html="renderAssistantMessage(message)"
                    @click="handleMarkdownClick"
                  />

                  <div v-if="message.citations?.length" class="mt-3 space-y-2">
                    <p class="text-[11px] text-slate-400">知识来源 {{ message.citations.length }} 条</p>
                    <div
                      v-for="(citation, index) in message.citations"
                      :key="`${message.id}-${citation.chunk_id || citation.document_id}-${index}`"
                      class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2"
                    >
                      <p class="truncate text-[11px] font-medium text-slate-700">
                        [{{ index + 1 }}] {{ citation.document_title }}
                      </p>
                      <p class="mt-1 whitespace-pre-line text-[11px] text-slate-600">{{ citation.content }}</p>
                      <div class="mt-2 flex flex-wrap justify-end gap-2">
                        <button
                          type="button"
                          class="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-[10px] text-slate-700 transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF] disabled:opacity-50"
                          :disabled="!citation.chunk_id"
                          @click.stop="jumpToKnowledgeChunk(citation)"
                        >
                          跳转到知识块
                        </button>
                        <button
                          type="button"
                          class="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-[10px] text-slate-700 transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF]"
                          @click.stop="jumpToKnowledgeDocument(citation)"
                        >
                          跳转到知识库
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </TransitionGroup>
        </div>

        <Transition name="fab">
          <button
            v-if="showScrollToBottom"
            type="button"
            class="btn-pop absolute bottom-24 right-6 z-10 h-10 w-10 rounded-full border border-slate-200 bg-white text-lg text-slate-600 shadow transition-colors hover:bg-slate-100"
            @click="scrollMessagesToBottom(true)"
          >
            ↓
          </button>
        </Transition>

        <footer v-if="hasMessages" class="border-t border-slate-200 bg-[#f8f9fb] px-4 py-4">
          <div class="mx-auto w-full max-w-4xl rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <textarea
              ref="composerTextarea"
              v-model="composer"
              rows="2"
              class="w-full max-h-[180px] resize-none overflow-y-auto border-none bg-transparent text-sm leading-7 text-slate-700 outline-none placeholder:text-slate-400"
              placeholder="继续追问，Enter 发送，Shift + Enter 换行"
              @keydown="handleComposerKeydown"
            />
            <div class="mt-2 flex items-center justify-between gap-3">
              <div class="flex items-center gap-2 text-[11px] text-slate-400">
                <span>支持 Markdown 输出解析</span>
                <span class="h-1 w-1 rounded-full bg-slate-300" />
                <span>已关联 {{ currentSourceCount }} 条资料</span>
              </div>
              <button
                type="button"
                class="btn-pop h-9 w-9 rounded-full bg-[#9fb7ff] text-lg text-white transition-colors hover:bg-[#88a7ff] disabled:opacity-60"
                :disabled="isAsking || !composer.trim()"
                @click="askQuestion"
              >
                ↑
              </button>
            </div>
          </div>
        </footer>
      </section>
    </section>
  </div>
</template>

<style scoped>
.qa-stage {
  isolation: isolate;
}

.session-item {
  transform: translateZ(0);
}

.session-item:hover {
  transform: translateY(-1px);
}

.btn-pop {
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.btn-pop:active {
  transform: scale(0.96);
}

.nav-icon-btn,
.floating-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: currentColor;
  transition: color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}

.nav-icon-btn {
  height: 2rem;
  width: 2rem;
  border-radius: 9999px;
}

.floating-icon-btn {
  height: 2.25rem;
  width: 2.25rem;
  border-radius: 9999px;
}

.nav-icon-btn:hover,
.floating-icon-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.nav-icon-btn:focus-visible,
.floating-icon-btn:focus-visible {
  outline: 2px solid rgb(58 134 255 / 0.38);
  outline-offset: 2px;
}

.floating-icon-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.qa-floating-dock {
  transform: translateZ(0);
}

.empty-hero {
  animation: fade-up 0.32s ease-out;
}

.msg-move,
.msg-enter-active,
.msg-leave-active {
  transition: all 0.22s ease;
}

.msg-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.msg-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.msg-leave-active {
  position: relative;
}

.fab-enter-active,
.fab-leave-active {
  transition: all 0.2s ease;
}

.fab-enter-from,
.fab-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.92);
}

.float-dock-enter-active,
.float-dock-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.float-dock-enter-from,
.float-dock-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.96);
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.markdown-body {
  line-height: 1.8;
  color: #334155;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
  color: #0f172a;
}

.markdown-body :deep(p:last-child),
.markdown-body :deep(ul:last-child),
.markdown-body :deep(ol:last-child),
.markdown-body :deep(blockquote:last-child),
.markdown-body :deep(pre:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(p),
.markdown-body :deep(ul),
.markdown-body :deep(ol),
.markdown-body :deep(blockquote),
.markdown-body :deep(pre),
.markdown-body :deep(hr) {
  margin-bottom: 0.75rem;
}

.markdown-body :deep(blockquote) {
  color: #475569;
}

.markdown-body :deep(code) {
  word-break: break-word;
}

.markdown-body :deep(table.markdown-table th),
.markdown-body :deep(table.markdown-table td) {
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.625rem;
  vertical-align: top;
}

.markdown-body :deep(table.markdown-table th) {
  background: #f8fafc;
  font-weight: 600;
}

.markdown-body :deep(.copy-code-btn) {
  backdrop-filter: blur(2px);
}
</style>
