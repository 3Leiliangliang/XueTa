<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import IconNotes from '@/components/icons/IconNotes.vue'
import IconSparkles from '@/components/icons/IconSparkles.vue'
import IconData from '@/components/icons/IconData.vue'
import Input from '@/components/ui/input.vue'
import Button from '@/components/ui/button.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const notebooks = ref([])
const notes = ref([])
const activeNotebookId = ref('')
const activeNoteId = ref('')
const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const isHydrating = ref(false)
let saveTimer = null

const noteTitle = ref('')
const noteContent = ref('')
const aiSummary = ref('选择一条笔记后，AI 总结会显示在这里。')
const todos = ref([])

const resetEditor = () => {
  activeNoteId.value = ''
  noteTitle.value = ''
  noteContent.value = ''
  aiSummary.value = '选择一条笔记后，AI 总结会显示在这里。'
  todos.value = []
}

const loadNote = async (noteId) => {
  if (!noteId) {
    resetEditor()
    return
  }

  isHydrating.value = true
  try {
    const [note, noteTodos] = await Promise.all([
      apiRequest(`/notes/${noteId}`),
      apiRequest(`/notes/${noteId}/todos`)
    ])
    activeNoteId.value = note.id
    noteTitle.value = note.title
    noteContent.value = note.content_markdown || ''
    aiSummary.value = note.summary || '这条笔记还没有 AI 总结，点击右侧按钮即可生成。'
    todos.value = noteTodos
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = error.message || '加载笔记详情失败，请稍后重试。'
  } finally {
    isHydrating.value = false
  }
}

const loadNotes = async (notebookId, { preserveSelection = false } = {}) => {
  if (!notebookId) {
    notes.value = []
    resetEditor()
    return
  }

  try {
    const list = await apiRequest(`/notes?notebook_id=${encodeURIComponent(notebookId)}`)
    notes.value = list
    if (!notes.value.length) {
      resetEditor()
      return
    }

    const targetNoteId = preserveSelection && notes.value.some((item) => item.id === activeNoteId.value)
      ? activeNoteId.value
      : notes.value[0].id
    await loadNote(targetNoteId)
  } catch (error) {
    errorMessage.value = error.message || '加载笔记列表失败，请稍后重试。'
  }
}

const loadNotebooks = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 学习笔记。'
    notebooks.value = []
    notes.value = []
    resetEditor()
    return
  }

  isLoading.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const list = await apiRequest('/notes/notebooks')
    notebooks.value = list
    if (!list.length) {
      resetEditor()
      statusMessage.value = '当前还没有笔记本，点击右上角“新建空白笔记”即可自动创建默认笔记本。'
      return
    }

    activeNotebookId.value = list[0].id
    await loadNotes(activeNotebookId.value)
  } catch (error) {
    errorMessage.value = error.message || '加载笔记本失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const setActiveNotebook = async (id) => {
  activeNotebookId.value = id
  await loadNotes(id)
}

const selectNote = async (noteId) => {
  await loadNote(noteId)
}

const createBlankNote = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 学习笔记。'
    return
  }

  try {
    let notebookId = activeNotebookId.value
    if (!notebookId) {
      const notebook = await apiRequest('/notes/notebooks', {
        method: 'POST',
        body: {
          name: '默认笔记本',
          description: '自动创建的默认笔记本'
        }
      })
      notebooks.value.unshift(notebook)
      notebookId = notebook.id
      activeNotebookId.value = notebook.id
    }

    const note = await apiRequest('/notes', {
      method: 'POST',
      body: {
        notebook_id: notebookId,
        title: `未命名笔记 ${notes.value.length + 1}`,
        content_markdown: '请开始记录你的学习内容。',
        source_type: 'manual'
      }
    })
    await loadNotebooks()
    await loadNote(note.id)
    statusMessage.value = '已创建新笔记。'
  } catch (error) {
    errorMessage.value = error.message || '创建笔记失败，请稍后重试。'
  }
}

// 添加待办（演示）
const newTodo = ref('')

const addTodo = async () => {
  const text = newTodo.value.trim()
  if (!text || !activeNoteId.value) return

  try {
    const todo = await apiRequest(`/notes/${activeNoteId.value}/todos`, {
      method: 'POST',
      body: {
        text,
        done: false,
        sort_order: todos.value.length
      }
    })
    todos.value.push(todo)
    newTodo.value = ''
  } catch (error) {
    errorMessage.value = error.message || '添加待办失败，请稍后重试。'
  }
}

const toggleTodo = async (item) => {
  const nextDone = !item.done
  item.done = nextDone

  try {
    const updated = await apiRequest(`/notes/todos/${item.id}`, {
      method: 'PATCH',
      body: { done: nextDone }
    })
    Object.assign(item, updated)
  } catch (error) {
    item.done = !nextDone
    errorMessage.value = error.message || '更新待办失败，请稍后重试。'
  }
}

const isSummarizing = ref(false)

const summarizeNote = async () => {
  if (isSummarizing.value || !activeNoteId.value) return
  isSummarizing.value = true

  try {
    const summary = await apiRequest(`/notes/${activeNoteId.value}/summarize`, {
      method: 'POST'
    })
    aiSummary.value = summary.summary_text
    statusMessage.value = 'AI 总结已更新。'
  } catch (error) {
    errorMessage.value = error.message || '生成 AI 总结失败，请稍后重试。'
  } finally {
    isSummarizing.value = false
  }
}

const saveCurrentNote = async () => {
  if (!activeNoteId.value || isHydrating.value) return

  isSaving.value = true
  try {
    const updated = await apiRequest(`/notes/${activeNoteId.value}`, {
      method: 'PATCH',
      body: {
        title: noteTitle.value.trim() || '未命名笔记',
        content_markdown: noteContent.value
      }
    })
    const targetNote = notes.value.find((item) => item.id === activeNoteId.value)
    if (targetNote) {
      targetNote.title = updated.title
      targetNote.updated_at = updated.updated_at
    }
    statusMessage.value = '已自动保存到云端。'
  } catch (error) {
    errorMessage.value = error.message || '自动保存失败，请稍后重试。'
  } finally {
    isSaving.value = false
  }
}

watch([noteTitle, noteContent], () => {
  if (!activeNoteId.value || isHydrating.value) return
  clearTimeout(saveTimer)
  saveTimer = window.setTimeout(() => {
    saveCurrentNote()
  }, 600)
})

onMounted(() => {
  loadNotebooks()
})

onUnmounted(() => {
  clearTimeout(saveTimer)
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
            <IconNotes class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1
              class="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent"
            >
              AI 智能学习笔记
            </h1>
            <p class="mt-1 text-xs md:text-sm text-slate-500">
              将课堂重点、习题解析与 AI 总结集中在一处，构建属于你的知识库。
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2 text-xs md:text-sm text-slate-500">
            <IconData class="w-4 h-4 text-[#3A86FF]" />
            <span>本周已记录 12 条新笔记</span>
          </div>
          <Button
            type="color"
            class="px-4 md:px-5 py-1.5 md:py-2 text-xs md:text-sm text-white !w-auto"
            @click="createBlankNote"
          >
            新建空白笔记
          </Button>
        </div>
      </section>

      <section v-if="authMessage || errorMessage || statusMessage" class="space-y-3">
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
        <p
          v-if="statusMessage"
          class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
        >
          {{ statusMessage }}
        </p>
      </section>

      <!-- 主体布局 -->
      <section class="grid lg:grid-cols-5 gap-6 lg:gap-8">
        <!-- 左侧：笔记本与 Todo -->
        <div class="lg:col-span-2 space-y-5">
          <!-- 笔记本列表 -->
          <div class="bg-white/80 rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div class="flex items-center justify-between mb-1">
              <h2 class="text-sm font-semibold text-slate-800">笔记本</h2>
              <span class="text-[11px] text-slate-400">按课程管理你的笔记</span>
            </div>
            <div class="space-y-1.5">
              <button
                v-for="book in notebooks"
                :key="book.id"
                type="button"
                :class="[
                  'w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs md:text-sm border transition-all',
                  activeNotebookId === book.id
                    ? 'bg-[#3A86FF] text-white border-[#3A86FF] shadow-sm'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                ]"
                @click="setActiveNotebook(book.id)"
              >
                <span class="truncate">{{ book.name }}</span>
                <span
                  :class="[
                    'ml-2 inline-flex items-center justify-center rounded-full px-2 py-0.5 text-[11px]',
                    activeNotebookId === book.id
                      ? 'bg-white/15 text-white'
                      : 'bg-white text-slate-600'
                  ]"
                >
                  {{ book.note_count }}
                </span>
              </button>
            </div>
          </div>

          <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-800">当前笔记</h3>
              <span class="text-[11px] text-slate-400">{{ notes.length }} 条</span>
            </div>
            <div class="space-y-1.5 max-h-44 overflow-y-auto">
              <button
                v-for="item in notes"
                :key="item.id"
                type="button"
                :class="[
                  'w-full rounded-xl border px-3 py-2 text-left text-xs md:text-sm transition-colors',
                  activeNoteId === item.id
                    ? 'border-[#3A86FF] bg-blue-50 text-slate-800'
                    : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                ]"
                @click="selectNote(item.id)"
              >
                <p class="truncate font-medium">{{ item.title }}</p>
              </button>
              <p v-if="!notes.length" class="text-xs text-slate-400">
                当前笔记本还没有笔记，点击右上角按钮创建第一条。
              </p>
            </div>
          </div>

          <!-- 学习待办 -->
          <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-slate-800">与本笔记相关的待办</h3>
              <span class="text-[11px] text-slate-400">勾选表示已完成</span>
            </div>
            <div class="space-y-2 max-h-40 overflow-y-auto">
              <label
                v-for="item in todos"
                :key="item.id"
                class="flex items-start gap-2 text-xs md:text-sm text-slate-700 cursor-pointer"
              >
                <input
                  type="checkbox"
                  class="mt-0.5 h-3.5 w-3.5 rounded border-slate-300 text-[#3A86FF] focus:ring-[#3A86FF]"
                  :checked="item.done"
                  @change="toggleTodo(item)"
                />
                <span
                  :class="[
                    'leading-snug',
                    item.done ? 'line-through text-slate-400' : 'text-slate-700'
                  ]"
                >
                  {{ item.text }}
                </span>
              </label>
            </div>
            <div class="flex items-center gap-2 pt-1">
              <Input
                v-model="newTodo"
                placeholder="添加新的复习任务..."
                class="h-9 text-xs"
                @keyup.enter="addTodo"
              />
              <button
                type="button"
                class="px-2.5 py-1 rounded-lg bg-slate-100 text-[11px] text-slate-600 hover:bg-slate-200"
                @click="addTodo"
              >
                添加
              </button>
            </div>
          </div>

          <!-- 小提示 -->
          <div
            class="bg-gradient-to-r from-[#3A86FF]/10 to-[#6C5CE7]/10 rounded-2xl border border-slate-200/80 p-4 flex items-start gap-3 text-xs text-slate-700"
          >
            <IconSparkles class="w-4 h-4 text-[#3A86FF] mt-0.5" />
            <p>
              建议按照「章节 / 知识点」来拆分笔记本，每条笔记保持一个明确主题，方便 AI
              为你生成结构化的复习提纲。
            </p>
          </div>
        </div>

        <!-- 右侧：编辑与 AI 总结 -->
        <div class="lg:col-span-3 space-y-4">
          <!-- 编辑区 -->
          <div
            class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[520px] md:h-[560px]"
          >
            <!-- 标题与工具栏 -->
            <div class="border-b border-slate-200 px-4 py-3 space-y-2">
              <Input
                v-model="noteTitle"
                placeholder="请输入笔记标题，如：第 3 讲 · 极限与连续"
                class="h-10 font-semibold text-slate-900 placeholder:text-slate-400"
              />
              <div class="flex items-center justify-between">
                <div class="flex flex-wrap gap-1.5 text-[11px] text-slate-500">
                  <button
                    v-for="tool in ['标题', '加粗', '列表', '分割线', '公式']"
                    :key="tool"
                    type="button"
                    class="px-2 py-1 rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100"
                  >
                    {{ tool }}
                  </button>
                </div>
                <div class="flex items-center gap-2 text-[11px] text-slate-400">
                  <span>{{ isSaving ? '自动保存中...' : activeNoteId ? '自动保存 · 云端同步' : '请选择一条笔记开始编辑' }}</span>
                </div>
              </div>
            </div>

            <!-- 正文编辑 -->
            <div class="flex-1 grid md:grid-cols-3">
              <!-- 左：正文 -->
              <div class="md:col-span-2 border-r border-slate-200">
                <textarea
                  v-model="noteContent"
                  class="w-full h-full min-h-[300px] resize-none border-none focus:outline-none text-sm text-slate-700 leading-relaxed p-4"
                  placeholder="在这里整理课堂知识点、例题与解题思路，可以使用 Markdown 风格进行分层。"
                ></textarea>
              </div>
              <!-- 右：结构与笔记块 -->
              <div class="hidden md:flex flex-col bg-slate-50">
                <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                  <span class="text-xs font-semibold text-slate-700">笔记结构预览</span>
                  <span class="text-[11px] text-slate-400">根据符号自动识别层级</span>
                </div>
                <div class="flex-1 p-3 space-y-1.5 text-[11px] text-slate-600 overflow-y-auto">
                  <p class="font-semibold text-slate-800">· 极限与连续 - 核心概念整理</p>
                  <p>└ 1. 极限的直观理解</p>
                  <p>└ 2. 极限存在性的条件</p>
                  <p>└ 3. 常用求极限方法</p>
                  <p class="mt-2 font-semibold text-slate-800">· 待补充</p>
                  <p>└ ε-δ 定义与几何解释</p>
                  <p>└ 典型例题 3-5 道</p>
                </div>
              </div>
            </div>
          </div>

          <!-- AI 总结区 -->
          <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <IconSparkles class="w-4 h-4 text-[#3A86FF]" />
                <span class="text-sm font-semibold text-slate-800">AI 学习小结</span>
              </div>
              <Button
                type="color"
                class="!w-auto px-3 py-1.5 text-xs md:text-sm text-white"
                :loading-text="'整理中...'"
                :default-text="'根据笔记内容重新整理'"
                @click="summarizeNote"
              >
                {{ isSummarizing ? '整理中...' : '根据笔记内容重新整理' }}
              </Button>
            </div>
            <div
              class="text-xs md:text-sm leading-relaxed text-slate-700 bg-slate-50 rounded-xl border border-dashed border-slate-200 px-3 py-3 whitespace-pre-line"
            >
              {{ aiSummary }}
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
textarea::-webkit-scrollbar {
  width: 6px;
}

textarea::-webkit-scrollbar-track {
  background: transparent;
}

textarea::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

textarea::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
