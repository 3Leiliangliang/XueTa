<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import IconSparkles from '@/components/icons/IconSparkles.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import IconRight from '@/components/icons/IconRight.vue'
import Input from '@/components/ui/input.vue'
import Button from '@/components/ui/button.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

defineOptions({
  name: 'NoteView'
})

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
const contentEditor = ref(null)
let saveTimer = null

const noteTitle = ref('')
const noteContent = ref('')
const searchQuery = ref('')
const emptySummaryText = '选择或创建一条笔记后，可以在右侧生成笔记总结。'
const aiSummary = ref(emptySummaryText)
const isCreateCardOpen = ref(false)
const createCardMode = ref('notebook')
const isCreatingNotebook = ref(false)
const isCreatingNote = ref(false)
const notebookForm = ref({
  name: '',
  description: '',
  color: '#3A86FF'
})
const noteForm = ref({
  notebook_id: '',
  title: '',
  content_markdown: ''
})

const notebookColorOptions = ['#3A86FF', '#6C5CE7', '#10B981', '#F97316']
const defaultNotebookColor = notebookColorOptions[0]

const getNotebookColor = (book) => {
  const color = String(book?.color || '').trim()
  return notebookColorOptions.includes(color) ? color : defaultNotebookColor
}

const toolbarActions = [
  { id: 'heading', label: '标题' },
  { id: 'bold', label: '加粗' },
  { id: 'list', label: '列表' },
  { id: 'quote', label: '引用' },
  { id: 'formula', label: '公式' }
]

const activeNotebook = computed(() =>
  notebooks.value.find((item) => item.id === activeNotebookId.value)
)

const createCardTitle = computed(() =>
  createCardMode.value === 'notebook' ? '新建笔记本' : '新建笔记'
)

const totalNoteCount = computed(() =>
  notebooks.value.reduce((total, item) => total + Number(item.note_count || 0), 0)
)

const filteredNotes = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return notes.value
  return notes.value.filter((item) =>
    String(item.title || '').toLowerCase().includes(keyword)
  )
})

const currentNote = computed(() =>
  notes.value.find((item) => item.id === activeNoteId.value)
)

const formatDateTime = (value) => {
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

const saveStateText = computed(() => {
  if (isSaving.value) return '自动保存中...'
  if (activeNoteId.value) {
    const updatedAt = formatDateTime(currentNote.value?.updated_at)
    return updatedAt ? `已同步 · ${updatedAt}` : '自动保存 · 云端同步'
  }
  return '选择或创建笔记后开始编辑'
})

const structureItems = computed(() => {
  if (!activeNoteId.value) return []

  const lines = noteContent.value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  const items = []
  for (const line of lines) {
    const heading = line.match(/^(#{1,6})\s+(.+)$/)
    const ordered = line.match(/^(\d+)\.\s+(.+)$/)
    const unordered = line.match(/^[-*]\s+(.+)$/)
    const task = line.match(/^[-*]\s+\[[ xX]\]\s+(.+)$/)

    if (heading) {
      items.push({
        id: `${items.length}-${heading[2]}`,
        level: heading[1].length,
        text: heading[2]
      })
    } else if (task) {
      items.push({
        id: `${items.length}-${task[1]}`,
        level: 3,
        text: task[1]
      })
    } else if (ordered || unordered) {
      const text = ordered?.[2] || unordered?.[1]
      items.push({
        id: `${items.length}-${text}`,
        level: 3,
        text
      })
    }

    if (items.length >= 10) break
  }

  return items
})

const structureEmptyText = computed(() => {
  if (!activeNoteId.value) return '选择左侧笔记后显示正文结构。'
  if (!noteContent.value.trim()) return '正文为空，输入标题或列表后会自动生成结构。'
  return '添加 Markdown 标题或列表后会自动生成结构。'
})

const noteMetaText = computed(() => {
  if (!activeNoteId.value) return '未选择笔记'
  const updatedAt = formatDateTime(currentNote.value?.updated_at || currentNote.value?.created_at)
  return updatedAt ? `更新于 ${updatedAt}` : '已载入笔记'
})

const resetEditor = () => {
  activeNoteId.value = ''
  noteTitle.value = ''
  noteContent.value = ''
  aiSummary.value = emptySummaryText
}

const loadNote = async (noteId) => {
  if (!noteId) {
    resetEditor()
    return
  }

  isHydrating.value = true
  try {
    const note = await apiRequest(`/notes/${noteId}`)
    activeNoteId.value = note.id
    noteTitle.value = note.title
    noteContent.value = String(note.content_markdown || '').trim() ? note.content_markdown : ''
    aiSummary.value = note.summary || '这条笔记还没有总结，点击右侧按钮即可生成。'
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
      statusMessage.value = '当前还没有笔记本，可以先新建笔记本，也可以直接新建笔记并自动使用默认笔记本。'
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

const openCreateNotebookCard = () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 学习笔记。'
    return
  }

  createCardMode.value = 'notebook'
  notebookForm.value = {
    name: '',
    description: '',
    color: defaultNotebookColor
  }
  errorMessage.value = ''
  statusMessage.value = ''
  isCreateCardOpen.value = true
}

const openCreateNoteCard = () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 学习笔记。'
    return
  }

  createCardMode.value = 'note'
  noteForm.value = {
    notebook_id: activeNotebookId.value || '',
    title: '',
    content_markdown: ''
  }
  errorMessage.value = ''
  statusMessage.value = ''
  isCreateCardOpen.value = true
}

const closeCreateCard = () => {
  if (isCreatingNotebook.value || isCreatingNote.value) return
  isCreateCardOpen.value = false
}

const createNotebookFromCard = async () => {
  if (isCreatingNotebook.value) return
  isCreatingNotebook.value = true

  try {
    const fallbackName = `新建笔记本 ${notebooks.value.length + 1}`
    const notebook = await apiRequest('/notes/notebooks', {
      method: 'POST',
      body: {
        name: notebookForm.value.name.trim() || fallbackName,
        description: notebookForm.value.description.trim(),
        color: notebookForm.value.color || defaultNotebookColor
      }
    })

    await loadNotebooks()
    activeNotebookId.value = notebook.id
    await loadNotes(notebook.id)
    statusMessage.value = '已创建新笔记本。'
    isCreateCardOpen.value = false
  } catch (error) {
    errorMessage.value = error.message || '创建笔记本失败，请稍后重试。'
  } finally {
    isCreatingNotebook.value = false
  }
}

const ensureNotebookForNewNote = async () => {
  if (noteForm.value.notebook_id) return noteForm.value.notebook_id
  if (activeNotebookId.value) return activeNotebookId.value

  const existingDefault = notebooks.value.find((item) => item.name === '默认笔记本')
  if (existingDefault) return existingDefault.id

  const notebook = await apiRequest('/notes/notebooks', {
    method: 'POST',
    body: {
      name: '默认笔记本',
      description: '自动创建的默认笔记本',
      color: defaultNotebookColor
    }
  })
  notebooks.value.unshift(notebook)
  activeNotebookId.value = notebook.id
  return notebook.id
}

const createNoteFromCard = async () => {
  if (isCreatingNote.value) return
  isCreatingNote.value = true

  try {
    const notebookId = await ensureNotebookForNewNote()
    const content = noteForm.value.content_markdown
    const note = await apiRequest('/notes', {
      method: 'POST',
      body: {
        notebook_id: notebookId,
        title: noteForm.value.title.trim() || `未命名笔记 ${notes.value.length + 1}`,
        content_markdown: content.trim() ? content : ' ',
        source_type: 'manual'
      }
    })

    await loadNotebooks()
    if (note.notebook_id) {
      activeNotebookId.value = note.notebook_id
      await loadNotes(note.notebook_id, { preserveSelection: true })
    }
    await loadNote(note.id)
    statusMessage.value = '已创建新笔记。'
    isCreateCardOpen.value = false
  } catch (error) {
    errorMessage.value = error.message || '创建笔记失败，请稍后重试。'
  } finally {
    isCreatingNote.value = false
  }
}

const insertAtCursor = async (before, after = '', fallback = '') => {
  if (!activeNoteId.value) return

  const textarea = contentEditor.value
  if (!textarea) {
    noteContent.value += `${noteContent.value ? '\n' : ''}${fallback || before}${after}`
    return
  }

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selected = noteContent.value.slice(start, end)
  const insertion = selected ? `${before}${selected}${after}` : (fallback || `${before}${after}`)
  noteContent.value = `${noteContent.value.slice(0, start)}${insertion}${noteContent.value.slice(end)}`

  await nextTick()
  textarea.focus()
  const cursor = start + insertion.length
  textarea.setSelectionRange(cursor, cursor)
}

const applyToolbarAction = async (actionId) => {
  const templates = {
    heading: ['## ', '', '## 新标题'],
    bold: ['**', '**', '**重点内容**'],
    list: ['- ', '', '- 待整理要点'],
    quote: ['> ', '', '> 关键结论'],
    formula: ['$$\n', '\n$$', '$$\n公式\n$$']
  }
  const [before, after, fallback] = templates[actionId] || templates.heading
  await insertAtCursor(before, after, fallback)
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
    errorMessage.value = error.message || '生成笔记总结失败，请稍后重试。'
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
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-white">
    <main class="mx-auto max-w-[1800px] px-4 py-6 lg:px-6">
      <section v-if="authMessage || errorMessage || statusMessage" class="mb-4 space-y-2">
        <p
          v-if="authMessage"
          class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
        >
          {{ authMessage }}
        </p>
        <p
          v-if="errorMessage"
          class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
        >
          {{ errorMessage }}
        </p>
        <p
          v-if="statusMessage"
          class="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
        >
          {{ statusMessage }}
        </p>
      </section>

      <section
        class="grid min-h-[calc(100vh-132px)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:grid-cols-[320px_minmax(0,1fr)_340px]"
      >
        <aside class="flex min-h-[720px] flex-col border-b border-slate-200 lg:border-b-0 lg:border-r">
          <div class="border-b border-slate-200 p-4">
            <label class="relative block">
              <IconSearch class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                v-model="searchQuery"
                type="search"
                placeholder="搜索笔记..."
                class="h-11 w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-3 text-sm text-slate-800 outline-none transition focus:border-[#3A86FF] focus:bg-white focus:ring-2 focus:ring-[#3A86FF]/15"
              />
            </label>
          </div>

          <div class="border-b border-slate-200 p-4">
            <div class="mb-3 flex items-center justify-between">
              <div>
                <h2 class="text-sm font-semibold text-slate-900">笔记本</h2>
                <p class="mt-0.5 text-xs text-slate-400">共 {{ totalNoteCount }} 条笔记</p>
              </div>
              <button
                type="button"
                class="inline-flex h-8 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-600 transition hover:border-[#3A86FF] hover:text-[#3A86FF]"
                title="新建笔记本"
                @click="openCreateNotebookCard"
              >
                <span class="text-base leading-none">+</span>
                <span>笔记本</span>
              </button>
            </div>

            <div class="max-h-64 space-y-1.5 overflow-y-auto pr-1">
              <button
                v-for="book in notebooks"
                :key="book.id"
                type="button"
                :class="[
                  'flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left text-sm transition',
                  activeNotebookId === book.id
                    ? 'border-[#3A86FF]/30 bg-[#3A86FF]/10 text-[#1f5fd6]'
                    : 'border-transparent bg-white text-slate-700 hover:bg-slate-50'
                ]"
                @click="setActiveNotebook(book.id)"
              >
                <span
                  class="h-2.5 w-2.5 shrink-0 rounded-full"
                  :style="{ backgroundColor: getNotebookColor(book) }"
                ></span>
                <span class="min-w-0 flex-1 truncate font-medium">{{ book.name }}</span>
                <span class="text-xs text-slate-400">{{ book.note_count || 0 }}</span>
              </button>

              <p v-if="!notebooks.length && !isLoading" class="rounded-xl bg-slate-50 px-3 py-4 text-xs text-slate-500">
                还没有笔记本。点击上方按钮创建第一个笔记本。
              </p>
            </div>
          </div>

          <div class="flex min-h-0 flex-1 flex-col p-4">
            <div class="mb-3 flex items-center justify-between">
              <div>
                <h2 class="text-sm font-semibold text-slate-900">笔记</h2>
                <p class="mt-0.5 text-xs text-slate-400">
                  {{ activeNotebook ? activeNotebook.name : '选择笔记本' }}
                </p>
              </div>
              <div class="flex items-center gap-2">
                <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">
                  {{ filteredNotes.length }}
                </span>
                <button
                  type="button"
                  class="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#3A86FF] px-2.5 text-xs font-medium text-white transition hover:bg-[#2f74df]"
                  title="新建笔记"
                  @click="openCreateNoteCard"
                >
                  <span class="text-base leading-none">+</span>
                  <span>笔记</span>
                </button>
              </div>
            </div>

            <div class="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
              <button
                v-for="item in filteredNotes"
                :key="item.id"
                type="button"
                :class="[
                  'group w-full rounded-xl border p-3 text-left transition',
                  activeNoteId === item.id
                    ? 'border-[#3A86FF]/40 bg-[#3A86FF]/10 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-[#3A86FF]/30 hover:bg-slate-50'
                ]"
                @click="selectNote(item.id)"
              >
                <div class="flex items-start gap-3">
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-semibold text-slate-900">{{ item.title }}</p>
                    <p class="mt-1 text-xs text-slate-400">
                      {{ formatDateTime(item.updated_at || item.created_at) || '未记录时间' }}
                    </p>
                  </div>
                  <IconRight class="mt-0.5 h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-[#3A86FF]" />
                </div>
              </button>

              <p v-if="notes.length && !filteredNotes.length" class="rounded-xl bg-slate-50 px-3 py-4 text-xs text-slate-500">
                没有匹配的笔记。
              </p>
              <p v-if="!notes.length" class="rounded-xl bg-slate-50 px-3 py-4 text-xs text-slate-500">
                当前笔记本还没有笔记，点击上方按钮创建第一条。
              </p>
            </div>
          </div>
        </aside>

        <section class="flex min-h-[720px] min-w-0 flex-col">
          <div class="border-b border-slate-200 px-5 py-4">
            <div class="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
              <div class="min-w-0 flex-1">
                <Input
                  v-model="noteTitle"
                  placeholder="请输入笔记标题"
                  class="h-11 border-transparent px-0 text-xl font-semibold text-slate-950 shadow-none placeholder:text-slate-400 focus-visible:ring-0 focus-visible:ring-offset-0"
                  :disabled="!activeNoteId"
                />
                <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                  <span>{{ noteMetaText }}</span>
                  <span v-if="activeNotebook">/</span>
                  <span v-if="activeNotebook">{{ activeNotebook.name }}</span>
                  <span>/</span>
                  <span>{{ saveStateText }}</span>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <button
                  v-for="tool in toolbarActions"
                  :key="tool.id"
                  type="button"
                  :class="[
                    'rounded-lg border px-3 py-2 text-xs font-medium transition',
                    activeNoteId
                      ? 'border-slate-200 bg-white text-slate-600 hover:border-[#3A86FF]/40 hover:text-[#3A86FF]'
                      : 'border-slate-200 bg-slate-50 text-slate-300'
                  ]"
                  :disabled="!activeNoteId"
                  @click="applyToolbarAction(tool.id)"
                >
                  {{ tool.label }}
                </button>
              </div>
            </div>
          </div>

          <div class="flex min-h-0 flex-1 flex-col">
            <textarea
              ref="contentEditor"
              v-model="noteContent"
              class="min-h-[520px] flex-1 resize-none border-none bg-white px-5 py-6 text-base leading-8 text-slate-800 outline-none placeholder:text-slate-400 disabled:bg-white disabled:text-slate-400"
              placeholder="在这里记录课堂知识点、例题、解题思路和复习结论。"
              :disabled="!activeNoteId"
            ></textarea>
          </div>
        </section>

        <aside class="flex min-h-[720px] flex-col border-t border-slate-200 bg-slate-50/50 lg:border-l lg:border-t-0">
          <section class="flex min-h-0 flex-1 flex-col p-5">
            <div class="mb-5">
              <div class="mb-3 flex items-center gap-2">
                <IconSparkles class="h-4 w-4 text-[#3A86FF]" />
                <h2 class="text-sm font-semibold text-slate-900">生成笔记总结</h2>
              </div>
              <p class="text-sm leading-6 text-slate-500">
                根据当前笔记的标题与正文生成学习总结，便于课后复盘和快速回顾。
              </p>
            </div>

            <Button
              type="color"
              class="!w-full px-4 py-2 text-sm text-white"
              :loading-text="'生成中...'"
              :default-text="'生成笔记总结'"
              @click="summarizeNote"
            >
              {{ isSummarizing ? '生成中...' : '生成笔记总结' }}
            </Button>

            <div class="mt-5 flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white">
              <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                <span class="text-xs font-semibold text-slate-700">笔记总结</span>
                <span class="text-[11px] text-slate-400">
                  {{ activeNoteId ? '当前笔记' : '未选择笔记' }}
                </span>
              </div>
              <div class="min-h-0 flex-1 overflow-y-auto p-4 text-sm leading-7 text-slate-700 whitespace-pre-line">
                {{ aiSummary }}
              </div>
            </div>

            <div class="mt-4 rounded-xl border border-slate-200 bg-white p-3">
              <div class="mb-2 flex items-center justify-between">
                <span class="text-xs font-semibold text-slate-700">总结依据</span>
                <span class="text-[11px] text-slate-400">{{ structureItems.length }} 项结构</span>
              </div>
              <div class="max-h-36 space-y-1 overflow-y-auto text-xs text-slate-500">
                <p
                  v-for="item in structureItems"
                  :key="item.id"
                  class="truncate"
                  :style="{ paddingLeft: `${Math.min(item.level - 1, 3) * 8}px` }"
                >
                  {{ item.level <= 2 ? '·' : '└' }} {{ item.text }}
                </p>
                <p v-if="!structureItems.length">{{ structureEmptyText }}</p>
              </div>
            </div>
          </section>
        </aside>
      </section>
    </main>

    <div
      v-if="isCreateCardOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 py-6 backdrop-blur-sm"
      @click.self="closeCreateCard"
    >
      <section class="w-full max-w-lg overflow-hidden rounded-2xl border border-white/70 bg-white shadow-2xl">
        <div class="flex items-start justify-between border-b border-slate-100 px-5 py-4">
          <div>
            <h2 class="text-base font-semibold text-slate-950">{{ createCardTitle }}</h2>
            <p class="mt-1 text-xs text-slate-500">
              {{ createCardMode === 'notebook' ? '为空名称会自动生成一个笔记本名称。' : '标题和正文都可以先留空，创建后继续编辑。' }}
            </p>
          </div>
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-xl leading-none text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
            aria-label="关闭"
            @click="closeCreateCard"
          >
            ×
          </button>
        </div>

        <form
          v-if="createCardMode === 'notebook'"
          class="space-y-4 px-5 py-5"
          @submit.prevent="createNotebookFromCard"
        >
          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700">笔记本名称</span>
            <Input v-model="notebookForm.name" placeholder="例如：高数复习" class="h-11 bg-slate-50" />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700">描述</span>
            <textarea
              v-model="notebookForm.description"
              rows="3"
              class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm leading-6 text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-[#3A86FF] focus:bg-white focus:ring-2 focus:ring-[#3A86FF]/15"
              placeholder="记录这个笔记本的用途，可留空。"
            ></textarea>
          </label>

          <div>
            <span class="mb-2 block text-sm font-medium text-slate-700">颜色</span>
            <div class="flex items-center gap-2">
              <button
                v-for="color in notebookColorOptions"
                :key="color"
                type="button"
                :class="[
                  'h-8 w-8 rounded-full border-2 transition',
                  notebookForm.color === color ? 'border-slate-900 ring-2 ring-slate-200' : 'border-white ring-1 ring-slate-200'
                ]"
                :style="{ backgroundColor: color }"
                :aria-label="`选择颜色 ${color}`"
                @click="notebookForm.color = color"
              ></button>
            </div>
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
              @click="closeCreateCard"
            >
              取消
            </button>
            <button
              type="submit"
              class="rounded-lg bg-[#3A86FF] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#2f74df] disabled:cursor-wait disabled:bg-slate-300"
              :disabled="isCreatingNotebook"
            >
              {{ isCreatingNotebook ? '创建中...' : '创建笔记本' }}
            </button>
          </div>
        </form>

        <form
          v-else
          class="space-y-4 px-5 py-5"
          @submit.prevent="createNoteFromCard"
        >
          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700">保存到</span>
            <select
              v-model="noteForm.notebook_id"
              class="h-11 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none transition focus:border-[#3A86FF] focus:bg-white focus:ring-2 focus:ring-[#3A86FF]/15"
            >
              <option value="">自动选择默认笔记本</option>
              <option
                v-for="book in notebooks"
                :key="book.id"
                :value="book.id"
              >
                {{ book.name }}
              </option>
            </select>
          </label>

          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700">笔记标题</span>
            <Input v-model="noteForm.title" placeholder="例如：函数极限整理" class="h-11 bg-slate-50" />
          </label>

          <label class="block">
            <span class="mb-1.5 block text-sm font-medium text-slate-700">初始正文</span>
            <textarea
              v-model="noteForm.content_markdown"
              rows="5"
              class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm leading-6 text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-[#3A86FF] focus:bg-white focus:ring-2 focus:ring-[#3A86FF]/15"
              placeholder="可以先留空，创建后在中间编辑区继续补充。"
            ></textarea>
          </label>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              class="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
              @click="closeCreateCard"
            >
              取消
            </button>
            <button
              type="submit"
              class="rounded-lg bg-[#3A86FF] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#2f74df] disabled:cursor-wait disabled:bg-slate-300"
              :disabled="isCreatingNote"
            >
              {{ isCreatingNote ? '创建中...' : '创建笔记' }}
            </button>
          </div>
        </form>
      </section>
    </div>
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
