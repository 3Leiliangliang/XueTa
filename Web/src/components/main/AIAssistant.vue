<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import IconAssistant from '@/components/icons/IconAssistant.vue'
import IconLogo from '@/components/icons/IconLogo.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest, streamSseRequest } from '@/lib/api'
import { AUTH_SESSION_EVENT, hasAccessToken } from '@/lib/auth'

const router = useRouter()
const ASSISTANT_SESSION_KEY = 'xueta_global_assistant_session_id'

let localMessageSeed = 0

const buildMessage = ({ type, content, pending = false, id = null }) => ({
  id: id || `local-${Date.now()}-${(localMessageSeed += 1)}`,
  type,
  content,
  pending,
  timestamp: new Date()
})

const buildGreeting = () =>
  buildMessage({
    type: 'assistant',
    content:
      '你好，我是学塔全局 AI 助手。登录后我会调用后端真实问答能力，支持上下文连续对话。'
  })

const isOpen = ref(false)
const isMaximized = ref(false)
const isSending = ref(false)
const isHydrating = ref(false)
const inputText = ref('')
const messages = ref([buildGreeting()])
const currentSessionId = ref('')
const isAuthenticated = ref(hasAccessToken())

const canUseStorage = () => typeof window !== 'undefined' && !!window.localStorage

const getStoredSessionId = () => {
  if (!canUseStorage()) return ''
  return window.localStorage.getItem(ASSISTANT_SESSION_KEY) || ''
}

const setStoredSessionId = (sessionId) => {
  if (!canUseStorage()) return
  if (!sessionId) return
  window.localStorage.setItem(ASSISTANT_SESSION_KEY, sessionId)
}

const clearStoredSessionId = () => {
  if (!canUseStorage()) return
  window.localStorage.removeItem(ASSISTANT_SESSION_KEY)
}

const scrollToBottom = () => {
  const messagesContainer = document.getElementById('messages-container')
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight
  }
}

const appendAuthHint = async () => {
  const lastMessage = messages.value[messages.value.length - 1]
  if (
    lastMessage?.type === 'assistant' &&
    lastMessage.content.includes('请先登录后再使用全局 AI 助手')
  ) {
    return
  }

  messages.value.push(
    buildMessage({
      type: 'assistant',
      content: '请先登录后再使用全局 AI 助手。登录后可自动接入后端真实会话能力。'
    })
  )

  await nextTick()
  scrollToBottom()
}

const applyServerMessages = async (records) => {
  const nextMessages = records
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .map((item) =>
      buildMessage({
        id: item.id,
        type: item.role === 'assistant' ? 'assistant' : 'user',
        content: item.content || ''
      })
    )

  messages.value = nextMessages.length ? nextMessages : [buildGreeting()]
  await nextTick()
  scrollToBottom()
}

const loadSessionMessages = async (sessionId) => {
  const records = await apiRequest(`/chat/sessions/${sessionId}/messages`)
  await applyServerMessages(records)
}

const hydrateFromStoredSession = async () => {
  if (!isAuthenticated.value) return

  const storedSessionId = getStoredSessionId()
  if (!storedSessionId) return

  isHydrating.value = true
  try {
    currentSessionId.value = storedSessionId
    await loadSessionMessages(storedSessionId)
  } catch {
    currentSessionId.value = ''
    clearStoredSessionId()
    messages.value = [buildGreeting()]
  } finally {
    isHydrating.value = false
  }
}

const ensureSession = async () => {
  if (currentSessionId.value) return currentSessionId.value

  const storedSessionId = getStoredSessionId()
  if (storedSessionId) {
    try {
      await apiRequest(`/chat/sessions/${storedSessionId}`)
      currentSessionId.value = storedSessionId
      return storedSessionId
    } catch {
      clearStoredSessionId()
    }
  }

  const session = await apiRequest('/chat/sessions', {
    method: 'POST',
    body: {
      title: '全局 AI 助手',
      subject: '全局助手'
    }
  })

  currentSessionId.value = session.id
  setStoredSessionId(session.id)
  return session.id
}

const toggleChat = async () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    isMaximized.value = false
    if (isAuthenticated.value && !currentSessionId.value && !isHydrating.value) {
      await hydrateFromStoredSession()
    }
    await nextTick()
    scrollToBottom()
  }
}

const closeChat = () => {
  isOpen.value = false
  isMaximized.value = false
}

const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
}

const goLogin = () => {
  router.push('/auth/login')
}

const sendMessage = async () => {
  const question = inputText.value.trim()
  if (!question || isSending.value) return

  messages.value.push(
    buildMessage({
      type: 'user',
      content: question
    })
  )
  inputText.value = ''

  await nextTick()
  scrollToBottom()

  if (!isAuthenticated.value) {
    await appendAuthHint()
    return
  }

  isSending.value = true
  const draft = buildMessage({ type: 'assistant', content: '', pending: true })
  messages.value.push(draft)

  await nextTick()
  scrollToBottom()

  try {
    const sessionId = await ensureSession()
    let streamedText = ''

    await streamSseRequest(`/chat/sessions/${sessionId}/messages/stream`, {
      body: { content: question },
      onEvent: ({ event, data }) => {
        if (event === 'message_start') {
          draft.content = ''
          return
        }

        if (event === 'delta' && data?.delta) {
          streamedText += data.delta
          draft.content = streamedText
          return
        }

        if (event === 'message_end' && data?.assistant_message) {
          draft.id = data.assistant_message.id || draft.id
          draft.content = data.assistant_message.content || streamedText
        }
      }
    })

    if (!draft.content.trim()) {
      draft.content = '我暂时没有生成内容，请再试一次。'
    }
  } catch (error) {
    draft.content = error.message || '请求失败，请稍后重试。'
    if (error?.status === 404) {
      currentSessionId.value = ''
      clearStoredSessionId()
    }
  } finally {
    draft.pending = false
    isSending.value = false
    await nextTick()
    scrollToBottom()
  }
}

const handleKeyPress = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const syncAuthState = () => {
  const nextAuthState = hasAccessToken()
  if (nextAuthState === isAuthenticated.value) return

  isAuthenticated.value = nextAuthState
  if (nextAuthState) {
    hydrateFromStoredSession()
    return
  }

  currentSessionId.value = ''
  clearStoredSessionId()
  isSending.value = false
  messages.value = [buildGreeting()]
}

onMounted(() => {
  hydrateFromStoredSession()
  window.addEventListener(AUTH_SESSION_EVENT, syncAuthState)
  window.addEventListener('storage', syncAuthState)
})

onUnmounted(() => {
  window.removeEventListener(AUTH_SESSION_EVENT, syncAuthState)
  window.removeEventListener('storage', syncAuthState)
})
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50">
    <button
      v-if="!isOpen"
      @click="toggleChat"
      class="w-14 h-14 rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-lg hover:shadow-xl transition-all hover:scale-110 flex items-center justify-center text-white"
      aria-label="打开 AI 助手"
    >
      <IconAssistant class="w-6 h-6 text-white stroke-white" />
    </button>

    <div
      v-if="isOpen"
      :class="[
        'bg-white rounded-2xl shadow-2xl flex flex-col transition-all duration-300',
        isMaximized
          ? 'w-[90vw] h-[90vh] max-w-6xl max-h-[800px]'
          : 'w-[400px] h-[600px]'
      ]"
    >
      <div class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] rounded-t-2xl px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <IconLogo class="w-5 h-5 text-white" />
          <span class="text-white font-medium text-sm">学塔 AI 助手</span>
        </div>
        <button
          @click="toggleMaximize"
          class="text-white hover:bg-white/20 rounded p-1 transition-colors"
          aria-label="最大化/还原"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
          </svg>
        </button>
      </div>

      <div
        id="messages-container"
        class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50"
      >
        <div
          v-for="message in messages"
          :key="message.id"
          :class="[
            'flex',
            message.type === 'user' ? 'justify-end' : 'justify-start'
          ]"
        >
          <div
            :class="[
              'max-w-[80%] rounded-2xl px-4 py-2 text-sm',
              message.type === 'user'
                ? 'bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white'
                : 'bg-white text-slate-700 border border-slate-200'
            ]"
          >
            <div v-if="message.pending && !message.content" class="flex items-center gap-1">
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </div>
            <div v-else class="whitespace-pre-wrap">{{ message.content }}</div>
          </div>
        </div>
      </div>

      <div class="border-t border-slate-200 p-4 bg-white rounded-b-2xl space-y-2">
        <div v-if="!isAuthenticated" class="flex items-center justify-between gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          <span>登录后可使用后端真实会话能力。</span>
          <button
            type="button"
            class="rounded-md bg-amber-100 px-2 py-1 text-amber-800 hover:bg-amber-200"
            @click="goLogin"
          >
            去登录
          </button>
        </div>

        <div class="flex items-end gap-2">
          <Input
            v-model="inputText"
            :placeholder="isAuthenticated ? '输入问题...' : '请先登录后提问'"
            :disabled="isSending || !isAuthenticated"
            class="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:border-transparent text-sm"
            @keypress="handleKeyPress"
          />
          <button
            @click="sendMessage"
            :disabled="!inputText.trim() || isSending || !isAuthenticated"
            class="w-10 h-10 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white flex items-center justify-center hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            aria-label="发送消息"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m22 2-7 20-4-9-9-4Z"/>
              <path d="M22 2 11 13"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <button
      v-if="isOpen"
      @click="closeChat"
      class="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-white shadow-lg hover:bg-slate-100 flex items-center justify-center text-slate-600 transition-colors"
      aria-label="关闭"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 6 6 18"/>
        <path d="m6 6 12 12"/>
      </svg>
    </button>
  </div>
</template>

<style scoped>
#messages-container::-webkit-scrollbar {
  width: 6px;
}

#messages-container::-webkit-scrollbar-track {
  background: transparent;
}

#messages-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

#messages-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
