<script setup>
import { onMounted, ref } from 'vue'
import IconQA from '@/components/icons/IconQA.vue'
import IconSparkles from '@/components/icons/IconSparkles.vue'
import IconStar from '@/components/icons/IconStar.vue'
import IconVolume from '@/components/icons/IconVolume.vue'
import Input from '@/components/ui/input.vue'
import Button from '@/components/ui/button.vue'
import { apiRequest, streamSseRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

// 当前输入的问题
const question = ref('')
const currentSessionId = ref('')
const authMessage = ref('')
const errorMessage = ref('')

// 当前 AI 回答
const answer = ref('你好，我是学塔 AI 答疑助手，可以帮你解答数学、英语、编程等学习问题，并给出详细的思路说明。请输入你的问题开始提问。')

// 问答历史
const qaHistory = ref([])

// 常见问题推荐
const suggestedQuestions = [
  '如何高效预习一门新课程？',
  '帮我讲解一下链表和数组的区别。',
  '英语阅读理解有什么解题技巧？',
  '如何规划一周的学习时间？',
  '微积分中的极限应该怎么理解？',
  '请帮我分析这道概率题的解题思路。'
]

// 当前选中的学科
const subjects = ['全部', '数学', '英语', '编程', '物理', '考研']
const activeSubject = ref('全部')

// 提交问题
const isAsking = ref(false)

const buildHistoryFromMessages = (messages) => {
  const history = []
  let pendingQuestion = ''

  for (const message of messages) {
    if (message.role === 'user') {
      pendingQuestion = message.content
      continue
    }

    if (message.role === 'assistant') {
      history.unshift({
        id: message.id,
        question: pendingQuestion || '未命名问题',
        answer: message.content
      })
    }
  }

  return history
}

const loadSessionMessages = async (sessionId) => {
  const messages = await apiRequest(`/chat/sessions/${sessionId}/messages`)
  qaHistory.value = buildHistoryFromMessages(messages)
  const latestAnswer = [...messages].reverse().find((message) => message.role === 'assistant')
  if (latestAnswer) {
    answer.value = latestAnswer.content
  }
}

const loadLatestSession = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 答疑中心。'
    qaHistory.value = []
    return
  }

  try {
    authMessage.value = ''
    errorMessage.value = ''
    const sessions = await apiRequest('/chat/sessions')
    if (!sessions.length) {
      qaHistory.value = []
      return
    }

    currentSessionId.value = sessions[0].id
    await loadSessionMessages(currentSessionId.value)
  } catch (error) {
    errorMessage.value = error.message || '加载答疑历史失败，请稍后重试。'
  }
}

const ensureSession = async () => {
  if (currentSessionId.value) return currentSessionId.value

  const session = await apiRequest('/chat/sessions', {
    method: 'POST',
    body: {
      title: null,
      subject: activeSubject.value === '全部' ? null : activeSubject.value
    }
  })
  currentSessionId.value = session.id
  return session.id
}

const askQuestion = async () => {
  if (!question.value.trim() || isAsking.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 答疑中心。'
    return
  }

  const q = question.value.trim()
  isAsking.value = true
  errorMessage.value = ''
  authMessage.value = ''
  question.value = ''

  try {
    const sessionId = await ensureSession()
    let streamedAnswer = ''

    await streamSseRequest(`/chat/sessions/${sessionId}/messages/stream`, {
      body: { content: q },
      onEvent: ({ event, data }) => {
        if (event === 'message_start') {
          answer.value = ''
          return
        }

        if (event === 'delta' && data?.delta) {
          streamedAnswer += data.delta
          answer.value = streamedAnswer
          return
        }

        if (event === 'message_end' && data?.assistant_message) {
          answer.value = data.assistant_message.content
          qaHistory.value.unshift({
            id: data.assistant_message.id,
            question: q,
            answer: data.assistant_message.content
          })
        }
      }
    })
  } catch (error) {
    errorMessage.value = error.message || '提问失败，请稍后重试。'
  } finally {
    isAsking.value = false
  }
}

// 点击推荐问题
const useSuggested = (q) => {
  question.value = q
}

// 朗读回答（预留）
const readAnswer = () => {
  // TODO: 接入 TTS
  console.log('朗读回答')
}

// 收藏回答（预留）
const collectAnswer = () => {
  // TODO: 接入收藏接口
  console.log('收藏该回答')
}

onMounted(() => {
  loadLatestSession()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main
      class="container mx-auto px-4 md:px-10 lg:px-16 py-8 md:py-10 lg:py-12 space-y-8 md:space-y-10"
    >
      <!-- 顶部标题区 -->
      <section class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] flex items-center justify-center shadow-md"
          >
            <IconQA class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1
              class="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent"
            >
              AI 学习答疑中心
            </h1>
            <p class="mt-1 text-xs md:text-sm text-slate-500">
              针对题目难点、概念理解和学习规划，获得一步步的详细解析与提示。
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2 text-xs md:text-sm text-slate-500">
            <span class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-[10px] text-white">
              AI
            </span>
            <span>已为 1,204 次提问生成解析</span>
          </div>
          <Button
            type="color"
            class="px-4 md:px-5 py-1.5 md:py-2 text-xs text-white md:text-sm !w-auto"
          >
            了解解题示例
          </Button>
        </div>
      </section>

      <section v-if="authMessage || errorMessage" class="space-y-3">
        <p
          v-if="authMessage"
          class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
        >
          {{ authMessage }}
        </p>
        <p
          v-if="errorMessage"
          class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
        >
          {{ errorMessage }}
        </p>
      </section>

      <!-- 主体布局 -->
      <section class="grid lg:grid-cols-5 gap-6 lg:gap-8">
        <!-- 左侧：提问区 -->
        <div class="lg:col-span-2 space-y-5">
          <!-- 学科标签 -->
          <div class="bg-white/80 rounded-2xl border border-slate-200 shadow-sm p-4">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-sm font-semibold text-slate-800">选择学科</h2>
              <span class="text-[11px] text-slate-400">更精准的解题思路推荐</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="subject in subjects"
                :key="subject"
                type="button"
                :class="[
                  'px-3 py-1 rounded-full text-xs font-medium border transition-colors',
                  activeSubject === subject
                    ? 'bg-[#3A86FF] text-white border-[#3A86FF]'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                ]"
                @click="activeSubject = subject"
              >
                {{ subject }}
              </button>
            </div>
          </div>

          <!-- 提问输入框 -->
          <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm font-semibold text-slate-800">输入你的问题</span>
              <span class="text-[11px] text-slate-400">支持粘贴题目或直接描述</span>
            </div>
            <div class="space-y-2">
              <Input
                v-model="question"
                placeholder="例如：请帮我详细讲解一下函数极限的定义，并举一个例子。"
                class="h-11"
                @keyup.enter="askQuestion"
              />
              <div class="flex items-center justify-between text-[11px] text-slate-400">
                <div class="flex items-center gap-2">
                  <span>Shift + Enter 换行</span>
                  <span class="h-1 w-1 rounded-full bg-slate-300" />
                  <span>自动识别题目类型</span>
                </div>
                <span>剩余 1,000 字</span>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-xs text-slate-500">
                <button
                  type="button"
                  class="flex items-center gap-1 px-2 py-1 rounded-md hover:bg-slate-50"
                >
                  <IconSparkles class="w-3.5 h-3.5 text-[#3A86FF]" />
                  <span>智能润色题目</span>
                </button>
              </div>
              <Button
                type="color"
                class="!w-auto px-4 py-2 text-xs md:text-sm text-white"
                :loading-text="'思考中...'"
                :default-text="'发送问题'"
                @click="askQuestion"
              >
                {{ isAsking ? '思考中...' : '发送问题' }}
              </Button>
            </div>
          </div>

          <!-- 常见问题推荐 -->
          <div class="bg-white/80 rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-800">常见学习问题</h3>
              <span class="text-[11px] text-slate-400">点击即可快速提问</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                v-for="item in suggestedQuestions"
                :key="item"
                type="button"
                class="text-left text-xs text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl px-3 py-2 transition-colors"
                @click="useSuggested(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>
        </div>

        <!-- 右侧：答疑区 -->
        <div class="lg:col-span-3 space-y-4">
          <div
            class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[520px] md:h-[560px]"
          >
            <!-- 头部栏 -->
            <div
              class="h-12 px-4 flex items-center justify-between border-b border-slate-200 bg-gradient-to-r from-[#3A86FF]/5 to-[#6C5CE7]/5"
            >
              <div class="flex items-center gap-2">
                <div
                  class="w-8 h-8 rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] flex items-center justify-center text-white text-xs"
                >
                  <IconQA class="w-4 h-4" />
                </div>
                <div>
                  <p class="text-xs font-semibold text-slate-800">学塔 · AI 解题助手</p>
                  <p class="text-[11px] text-slate-400">提供逐步解析与知识点讲解</p>
                </div>
              </div>
              <div class="flex items-center gap-2 text-[11px] text-slate-500">
                <button
                  type="button"
                  class="flex items-center gap-1 px-2 py-1 rounded-md hover:bg-slate-100"
                  @click="readAnswer"
                >
                  <IconVolume class="w-3.5 h-3.5" />
                  <span>朗读</span>
                </button>
                <button
                  type="button"
                  class="flex items-center gap-1 px-2 py-1 rounded-md hover:bg-slate-100"
                  @click="collectAnswer"
                >
                  <IconStar class="w-3.5 h-3.5" />
                  <span>收藏</span>
                </button>
              </div>
            </div>

            <!-- 答案展示 -->
            <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
              <!-- 当前回答 -->
              <div class="bg-white rounded-2xl border border-slate-200 p-4 text-sm text-slate-700">
                <div class="flex items-center gap-2 mb-2">
                  <span class="px-2 py-0.5 rounded-full bg-[#3A86FF]/10 text-[#3A86FF] text-[11px]">
                    当前回答
                  </span>
                </div>
                <p class="leading-relaxed whitespace-pre-line">
                  {{ answer }}
                </p>
              </div>

              <!-- 历史记录 -->
              <div class="space-y-3">
                <div class="flex items-center justify-between text-[11px] text-slate-400">
                  <span>最近解答</span>
                  <span>仅当前设备可见</span>
                </div>
                <div class="space-y-2">
                  <div
                    v-for="item in qaHistory"
                    :key="item.id"
                    class="bg-white rounded-2xl border border-slate-200 p-3 text-xs text-slate-700"
                  >
                    <p class="font-medium text-slate-800 mb-1">Q：{{ item.question }}</p>
                    <p class="text-[11px] leading-relaxed text-slate-600">
                      A：{{ item.answer }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 提示信息 -->
          <div class="text-[11px] text-slate-400 flex flex-wrap gap-3 justify-between">
            <span>AI 答案仅供学习参考，请在理解思路的基础上独立完成作业与考试。</span>
            <span>如需更精确的学科支持，可以前往「学习规划」中配置课程与教材。</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.qa-scroll::-webkit-scrollbar {
  width: 6px;
}

.qa-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.qa-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.qa-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
