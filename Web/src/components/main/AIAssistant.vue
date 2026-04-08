<script setup>
import { ref, computed, nextTick } from 'vue'
import IconAssistant from '@/components/icons/IconAssistant.vue'
import IconLogo from '@/components/icons/IconLogo.vue'
import Input from '@/components/ui/input.vue'

// 控制聊天窗口显示/隐藏
const isOpen = ref(false)
const isMaximized = ref(false)

// 消息列表
const messages = ref([
  {
    id: 1,
    type: 'assistant',
    content: '你好! 我是学塔 AI 助手, 有什么我可以帮助你的吗?',
    timestamp: new Date()
  }
])

// 输入框内容
const inputText = ref('')
const isSending = ref(false)

// 切换聊天窗口
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    isMaximized.value = false
  }
}

// 关闭聊天窗口
const closeChat = () => {
  isOpen.value = false
  isMaximized.value = false
}

// 切换最大化
const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() || isSending.value) return

  const userMessage = {
    id: messages.value.length + 1,
    type: 'user',
    content: inputText.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const question = inputText.value.trim()
  inputText.value = ''
  isSending.value = true

  // 模拟AI回复（后续可以替换为真实的API调用）
  await new Promise(resolve => setTimeout(resolve, 1000))

  const assistantMessage = {
    id: messages.value.length + 1,
    type: 'assistant',
    content: generateResponse(question),
    timestamp: new Date()
  }

  messages.value.push(assistantMessage)
  isSending.value = false

  // 滚动到底部
  await nextTick()
  scrollToBottom()
}

// 简单的回复生成逻辑（后续可以替换为真实的AI API）
const generateResponse = (question) => {
  const lowerQuestion = question.toLowerCase()
  
  if (lowerQuestion.includes('你好') || lowerQuestion.includes('hello')) {
    return '你好！很高兴为你服务。我可以帮助你解答学习问题、提供学习建议等。'
  } else if (lowerQuestion.includes('翻译')) {
    return '你可以使用学塔的翻译功能来翻译文档和论文。需要我帮你打开翻译页面吗？'
  } else if (lowerQuestion.includes('笔记')) {
    return '学塔的笔记功能可以帮助你整理学习内容，生成思维导图。需要我帮你打开笔记页面吗？'
  } else if (lowerQuestion.includes('学习规划')) {
    return '学习规划功能可以帮助你制定学习计划，追踪学习进度。需要我帮你打开学习规划页面吗？'
  } else if (lowerQuestion.includes('帮助') || lowerQuestion.includes('help')) {
    return '我可以帮助你：\n1. 解答学习问题\n2. 提供学习建议\n3. 介绍学塔的各项功能\n4. 协助你使用各种学习工具\n\n有什么具体问题吗？'
  } else {
    return `关于"${question}"，这是一个很好的问题。虽然我现在只能提供简单的回复，但我会尽力帮助你。你可以尝试使用学塔的其他功能来获得更详细的帮助。`
  }
}

// 滚动到底部
const scrollToBottom = () => {
  const messagesContainer = document.getElementById('messages-container')
  if (messagesContainer) {
    messagesContainer.scrollTop = messagesContainer.scrollHeight
  }
}

// 处理回车键发送
const handleKeyPress = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="fixed bottom-6 right-6 z-50">
    <!-- 悬浮按钮 -->
    <button
      v-if="!isOpen"
      @click="toggleChat"
      class="w-14 h-14 rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-lg hover:shadow-xl transition-all hover:scale-110 flex items-center justify-center text-white"
      aria-label="打开AI助手"
    >
      <IconAssistant class="w-6 h-6 text-white stroke-white" />
    </button>

    <!-- 聊天窗口 -->
    <div
      v-if="isOpen"
      :class="[
        'bg-white rounded-2xl shadow-2xl flex flex-col transition-all duration-300',
        isMaximized 
          ? 'w-[90vw] h-[90vh] max-w-6xl max-h-[800px]' 
          : 'w-[400px] h-[600px]'
      ]"
    >
      <!-- 头部 -->
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

      <!-- 消息区域 -->
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
            <div class="whitespace-pre-wrap">{{ message.content }}</div>
          </div>
        </div>
        <div v-if="isSending" class="flex justify-start">
          <div class="bg-white text-slate-700 border border-slate-200 rounded-2xl px-4 py-2 text-sm">
            <div class="flex items-center gap-1">
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="border-t border-slate-200 p-4 bg-white rounded-b-2xl">
        <div class="flex items-end gap-2">
          <Input
            v-model="inputText"
            placeholder="输入问题..."
            :disabled="isSending"
            class="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:border-transparent text-sm"
            @keypress="handleKeyPress"
          />
          <button
            @click="sendMessage"
            :disabled="!inputText.trim() || isSending"
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

    <!-- 关闭按钮（在聊天窗口外部） -->
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
/* 自定义滚动条样式 */
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