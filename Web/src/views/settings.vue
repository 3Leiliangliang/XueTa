<script setup>
import { computed, onMounted, ref } from 'vue'

import IconSettings from '@/components/icons/IconSettings.vue'
import Input from '@/components/ui/input.vue'
import {
  applyThemePreference,
  defaultUserSettings,
  getStoredSettings,
  saveStoredSettings
} from '@/lib/settings'

const settings = ref({ ...defaultUserSettings })
const statusMessage = ref('')

const themeOptions = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' }
]

const densityOptions = [
  { value: 'comfortable', label: '舒展' },
  { value: 'compact', label: '紧凑' }
]

const entryOptions = [
  { value: '/desktop', label: '学习桌面' },
  { value: '/qa', label: 'AI 答疑' },
  { value: '/note', label: '学习笔记' },
  { value: '/planning', label: '学习规划' }
]

const translateTargets = [
  { value: 'zh-CN', label: '中文' },
  { value: 'en-US', label: '英文' },
  { value: 'ja-JP', label: '日文' },
  { value: 'ko-KR', label: '韩文' }
]

const llmProviderOptions = [
  {
    value: 'openai-compatible',
    label: 'OpenAI 兼容接口',
    baseUrl: '',
    chatModel: 'gpt-4o',
    embeddingModel: 'text-embedding-3-small',
    visionModel: 'gpt-4o'
  },
  {
    value: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com',
    chatModel: 'deepseek-chat',
    embeddingModel: 'text-embedding-3-small',
    visionModel: ''
  },
  {
    value: 'qwen',
    label: '通义千问',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    chatModel: 'qwen-plus',
    embeddingModel: 'text-embedding-3-small',
    visionModel: 'qwen-vl-plus'
  },
  {
    value: 'siliconflow',
    label: '硅基流动',
    baseUrl: 'https://api.siliconflow.cn/v1',
    chatModel: 'Qwen/Qwen2.5-72B-Instruct',
    embeddingModel: 'BAAI/bge-m3',
    visionModel: 'Qwen/Qwen2.5-VL-72B-Instruct'
  }
]

const selectedLlmProvider = computed(() =>
  llmProviderOptions.find((item) => item.value === settings.value.customLlmProvider) || llmProviderOptions[0]
)

const customLlmReady = computed(() =>
  Boolean(settings.value.customLlmEnabled && settings.value.customLlmApiKey && settings.value.customLlmModel)
)

const summaryItems = computed(() => [
  {
    label: '默认入口',
    value: entryOptions.find((item) => item.value === settings.value.defaultEntry)?.label || '学习桌面'
  },
  {
    label: '每日目标',
    value: `${settings.value.dailyGoalMinutes || 0} 分钟`
  },
  {
    label: '提醒时间',
    value: settings.value.reviewReminder ? settings.value.reminderTime : '已关闭'
  },
  {
    label: 'AI 模型',
    value: customLlmReady.value ? settings.value.customLlmModel : '系统默认'
  }
])

const loadSettings = () => {
  settings.value = getStoredSettings()
  applyThemePreference(settings.value.theme)
}

const saveSettings = () => {
  settings.value = saveStoredSettings(settings.value)
  applyThemePreference(settings.value.theme)
  statusMessage.value = '设置已保存。'
}

const resetSettings = () => {
  settings.value = { ...defaultUserSettings }
  saveSettings()
  statusMessage.value = '已恢复默认设置。'
}

const updateTheme = (theme) => {
  settings.value.theme = theme
  settings.value = saveStoredSettings(settings.value)
  applyThemePreference(theme)
  statusMessage.value = '主题模式已更新。'
}

const applyLlmProviderPreset = () => {
  const provider = selectedLlmProvider.value
  settings.value.customLlmBaseUrl = provider.baseUrl
  settings.value.customLlmModel = provider.chatModel
  settings.value.customLlmEmbeddingModel = provider.embeddingModel
  settings.value.customLlmVisionModel = provider.visionModel
}

const clearCustomApiKey = () => {
  settings.value.customLlmApiKey = ''
  settings.value.customLlmEnabled = false
  statusMessage.value = '已清空自定义 API Key。'
}

const toggleSetting = (key) => {
  settings.value[key] = !settings.value[key]
}

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main class="container mx-auto space-y-8 px-4 py-8 md:px-10 md:py-10 lg:px-16 lg:py-12">
      <section class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-md">
            <IconSettings class="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-2xl font-bold text-transparent md:text-3xl lg:text-4xl">
              设置
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              调整学习工作台、AI 助手、提醒和隐私偏好。
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
            @click="resetSettings"
          >
            恢复默认
          </button>
          <button
            type="button"
            class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-2 text-sm text-white transition-opacity hover:opacity-90"
            @click="saveSettings"
          >
            保存设置
          </button>
        </div>
      </section>

      <p
        v-if="statusMessage"
        class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
      >
        {{ statusMessage }}
      </p>

      <section class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="item in summaryItems"
          :key="item.label"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <p class="text-sm text-slate-500">{{ item.label }}</p>
          <p class="mt-2 text-2xl font-bold text-slate-900">{{ item.value }}</p>
        </div>
      </section>

      <section class="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">界面偏好</h2>
            <div class="mt-5 space-y-5">
              <div>
                <p class="text-sm font-medium text-slate-700">主题模式</p>
                <div class="mt-3 grid grid-cols-3 gap-2 rounded-2xl bg-slate-100 p-1">
                  <button
                    v-for="option in themeOptions"
                    :key="option.value"
                    type="button"
                    :class="[
                      'rounded-xl px-3 py-2 text-sm transition-colors',
                      settings.theme === option.value
                        ? 'bg-white text-[#3A86FF] shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    ]"
                    @click="updateTheme(option.value)"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>

              <div>
                <p class="text-sm font-medium text-slate-700">布局密度</p>
                <div class="mt-3 grid grid-cols-2 gap-2 rounded-2xl bg-slate-100 p-1">
                  <button
                    v-for="option in densityOptions"
                    :key="option.value"
                    type="button"
                    :class="[
                      'rounded-xl px-3 py-2 text-sm transition-colors',
                      settings.density === option.value
                        ? 'bg-white text-[#3A86FF] shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    ]"
                    @click="settings.density = option.value"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>

              <label class="block">
                <span class="text-sm font-medium text-slate-700">登录后默认入口</span>
                <select
                  v-model="settings.defaultEntry"
                  class="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3A86FF]"
                >
                  <option
                    v-for="option in entryOptions"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">学习默认值</h2>
            <div class="mt-5 space-y-5">
              <label class="block">
                <span class="text-sm font-medium text-slate-700">每日学习目标</span>
                <div class="mt-2 flex items-center gap-3">
                  <input
                    v-model.number="settings.dailyGoalMinutes"
                    type="range"
                    min="15"
                    max="240"
                    step="15"
                    class="w-full accent-[#3A86FF]"
                  >
                  <span class="w-20 rounded-lg bg-slate-100 px-3 py-2 text-center text-sm text-slate-700">
                    {{ settings.dailyGoalMinutes }} 分钟
                  </span>
                </div>
              </label>

              <label class="block">
                <span class="text-sm font-medium text-slate-700">默认学科</span>
                <Input v-model="settings.defaultSubject" class="mt-2" placeholder="例如：英语、数学、计算机网络" />
              </label>

              <label class="block">
                <span class="text-sm font-medium text-slate-700">翻译默认目标语言</span>
                <select
                  v-model="settings.translateTarget"
                  class="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3A86FF]"
                >
                  <option
                    v-for="option in translateTargets"
                    :key="option.value"
                    :value="option.value"
                  >
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h2 class="text-lg font-semibold text-slate-900">AI 助手</h2>
                <p class="mt-1 text-sm text-slate-500">控制全局助手和学习会话的默认行为。</p>
              </div>
              <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-[#3A86FF]">Workspace</span>
            </div>

            <div class="mt-5 divide-y divide-slate-100">
              <button
                type="button"
                class="flex w-full items-center justify-between gap-4 py-4 text-left"
                @click="toggleSetting('assistantAutoOpen')"
              >
                <span>
                  <span class="block text-sm font-medium text-slate-800">打开页面时保持助手待命</span>
                  <span class="mt-1 block text-xs text-slate-500">进入学习页面后自动恢复上次助手状态。</span>
                </span>
                <span
                  :class="[
                    'relative h-6 w-11 shrink-0 rounded-full transition-colors',
                    settings.assistantAutoOpen ? 'bg-[#3A86FF]' : 'bg-slate-200'
                  ]"
                >
                  <span
                    :class="[
                      'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                      settings.assistantAutoOpen ? 'translate-x-6' : 'translate-x-1'
                    ]"
                  />
                </span>
              </button>

              <button
                type="button"
                class="flex w-full items-center justify-between gap-4 py-4 text-left"
                @click="toggleSetting('assistantVoice')"
              >
                <span>
                  <span class="block text-sm font-medium text-slate-800">允许回答朗读</span>
                  <span class="mt-1 block text-xs text-slate-500">在答疑结果中显示语音播放能力。</span>
                </span>
                <span
                  :class="[
                    'relative h-6 w-11 shrink-0 rounded-full transition-colors',
                    settings.assistantVoice ? 'bg-[#3A86FF]' : 'bg-slate-200'
                  ]"
                >
                  <span
                    :class="[
                      'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                      settings.assistantVoice ? 'translate-x-6' : 'translate-x-1'
                    ]"
                  />
                </span>
              </button>

              <button
                type="button"
                class="flex w-full items-center justify-between gap-4 py-4 text-left"
                @click="toggleSetting('autosaveNotes')"
              >
                <span>
                  <span class="block text-sm font-medium text-slate-800">笔记自动保存</span>
                  <span class="mt-1 block text-xs text-slate-500">编辑学习笔记时保留草稿和最近修改。</span>
                </span>
                <span
                  :class="[
                    'relative h-6 w-11 shrink-0 rounded-full transition-colors',
                    settings.autosaveNotes ? 'bg-[#3A86FF]' : 'bg-slate-200'
                  ]"
                >
                  <span
                    :class="[
                      'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                      settings.autosaveNotes ? 'translate-x-6' : 'translate-x-1'
                    ]"
                  />
                </span>
              </button>
            </div>

            <div class="mt-6 border-t border-slate-100 pt-6">
              <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h3 class="text-base font-semibold text-slate-900">自定义大模型 API</h3>
                  <p class="mt-1 text-sm text-slate-500">启用后，AI 答疑、翻译、笔记总结和知识库检索会优先使用你的模型配置。</p>
                </div>
                <button
                  type="button"
                  class="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left md:min-w-48"
                  @click="toggleSetting('customLlmEnabled')"
                >
                  <span class="text-sm font-medium text-slate-800">
                    {{ settings.customLlmEnabled ? '已启用' : '使用系统默认' }}
                  </span>
                  <span
                    :class="[
                      'relative h-6 w-11 shrink-0 rounded-full transition-colors',
                      settings.customLlmEnabled ? 'bg-[#3A86FF]' : 'bg-slate-200'
                    ]"
                  >
                    <span
                      :class="[
                        'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                        settings.customLlmEnabled ? 'translate-x-6' : 'translate-x-1'
                      ]"
                    />
                  </span>
                </button>
              </div>

              <div class="mt-5 grid gap-4 md:grid-cols-2">
                <label class="block">
                  <span class="text-sm font-medium text-slate-700">服务商</span>
                  <select
                    v-model="settings.customLlmProvider"
                    class="mt-2 h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3A86FF]"
                    @change="applyLlmProviderPreset"
                  >
                    <option
                      v-for="option in llmProviderOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                </label>

                <label class="block">
                  <span class="text-sm font-medium text-slate-700">Base URL</span>
                  <Input
                    v-model="settings.customLlmBaseUrl"
                    class="mt-2"
                    placeholder="https://api.example.com/v1"
                  />
                </label>

                <label class="block">
                  <span class="text-sm font-medium text-slate-700">API Key</span>
                  <Input
                    v-model="settings.customLlmApiKey"
                    class="mt-2"
                    type="password"
                    autocomplete="off"
                    placeholder="sk-..."
                  />
                </label>

                <label class="block">
                  <span class="text-sm font-medium text-slate-700">对话模型</span>
                  <Input v-model="settings.customLlmModel" class="mt-2" placeholder="gpt-4o / deepseek-chat / qwen-plus" />
                </label>

                <label class="block md:col-span-2">
                  <span class="text-sm font-medium text-slate-700">Embedding 模型</span>
                  <Input
                    v-model="settings.customLlmEmbeddingModel"
                    class="mt-2"
                    placeholder="text-embedding-3-small / BAAI/bge-m3"
                  />
                </label>

                <label class="block md:col-span-2">
                  <span class="text-sm font-medium text-slate-700">视觉模型</span>
                  <Input
                    v-model="settings.customLlmVisionModel"
                    class="mt-2"
                    placeholder="留空则使用对话模型处理图片 OCR"
                  />
                </label>

                <label class="block">
                  <span class="text-sm font-medium text-slate-700">请求超时</span>
                  <div class="mt-2 flex items-center gap-2">
                    <Input
                      v-model.number="settings.customLlmTimeoutSeconds"
                      type="number"
                      min="5"
                      max="120"
                      step="1"
                      placeholder="20"
                    />
                    <span class="shrink-0 text-sm text-slate-500">秒</span>
                  </div>
                </label>

                <label class="block">
                  <span class="text-sm font-medium text-slate-700">温度</span>
                  <Input
                    v-model="settings.customLlmTemperature"
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    class="mt-2"
                    placeholder="留空使用功能默认值"
                  />
                </label>

                <label class="block md:col-span-2">
                  <span class="text-sm font-medium text-slate-700">最大输出 Token</span>
                  <Input
                    v-model="settings.customLlmMaxTokens"
                    type="number"
                    min="128"
                    max="8192"
                    step="128"
                    class="mt-2"
                    placeholder="留空使用功能默认值"
                  />
                </label>
              </div>

              <div class="mt-4 flex flex-col gap-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600 md:flex-row md:items-center md:justify-between">
                <span>
                  {{ customLlmReady ? '自定义模型将在下一次 AI 请求中生效。' : '填写 API Key 和对话模型后再启用自定义模型。' }}
                </span>
                <button
                  type="button"
                  class="self-start text-sm font-medium text-slate-500 transition-colors hover:text-rose-600 md:self-auto"
                  @click="clearCustomApiKey"
                >
                  清空密钥
                </button>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">提醒与隐私</h2>
            <div class="mt-5 space-y-5">
              <div class="grid gap-3 md:grid-cols-2">
                <button
                  type="button"
                  :class="[
                    'rounded-2xl border p-4 text-left transition-colors',
                    settings.reviewReminder ? 'border-[#3A86FF] bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'
                  ]"
                  @click="toggleSetting('reviewReminder')"
                >
                  <span class="block text-sm font-medium text-slate-900">复习提醒</span>
                  <span class="mt-1 block text-xs text-slate-500">到期复习任务提示</span>
                </button>
                <button
                  type="button"
                  :class="[
                    'rounded-2xl border p-4 text-left transition-colors',
                    settings.weeklyDigest ? 'border-[#3A86FF] bg-blue-50' : 'border-slate-200 bg-white hover:bg-slate-50'
                  ]"
                  @click="toggleSetting('weeklyDigest')"
                >
                  <span class="block text-sm font-medium text-slate-900">周报摘要</span>
                  <span class="mt-1 block text-xs text-slate-500">每周汇总学习表现</span>
                </button>
              </div>

              <label class="block">
                <span class="text-sm font-medium text-slate-700">提醒时间</span>
                <Input v-model="settings.reminderTime" class="mt-2" type="time" :disabled="!settings.reviewReminder" />
              </label>

              <button
                type="button"
                class="flex w-full items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left"
                @click="toggleSetting('privacyAnalytics')"
              >
                <span>
                  <span class="block text-sm font-medium text-slate-800">允许匿名体验数据</span>
                  <span class="mt-1 block text-xs text-slate-500">用于统计页面性能与功能使用情况。</span>
                </span>
                <span
                  :class="[
                    'relative h-6 w-11 shrink-0 rounded-full transition-colors',
                    settings.privacyAnalytics ? 'bg-[#3A86FF]' : 'bg-slate-200'
                  ]"
                >
                  <span
                    :class="[
                      'absolute top-1 h-4 w-4 rounded-full bg-white transition-transform',
                      settings.privacyAnalytics ? 'translate-x-6' : 'translate-x-1'
                    ]"
                  />
                </span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
