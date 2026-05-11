<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import IconTranslate from '@/components/icons/IconTranslate.vue'
import IconDocument from '@/components/icons/IconDocument.vue'
import IconImage from '@/components/icons/IconImage.vue'
import IconMic from '@/components/icons/IconMic.vue'
import IconGlobe from '@/components/icons/IconGlobe.vue'
import IconStar from '@/components/icons/IconStar.vue'
import IconDownload from '@/components/icons/IconDownload.vue'
import IconSparkles from '@/components/icons/IconSparkles.vue'
import IconVolume from '@/components/icons/IconVolume.vue'
import IconUpload from '@/components/icons/IconUpload.vue'
import { apiRawRequest, apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'
import {
  buildTranslateNoteMarkdown,
  buildTranslateNoteTitle,
  getUploadedFileType
} from '@/lib/translate-utils'

const fileInput = ref(null)
const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isUploading = ref(false)
const isLoadingFiles = ref(false)
const isTranslating = ref(false)
const isPolishing = ref(false)
const isSavingNote = ref(false)
const uploadedFiles = ref([])
const currentUploadedFileId = ref('')
const selectedUploadedFile = ref(null)
const translationSourceMode = ref('text')
const fileSearchKeyword = ref('')
const fileTypeFilter = ref('all')
const showSaveNoteModal = ref(false)
const noteTitle = ref('')
const noteNotebookId = ref('')
const notebooks = ref([])
const isLoadingNotebooks = ref(false)
let searchTimer = null

const translationTypes = [
  {
    id: 'document',
    name: '文档翻译',
    icon: IconDocument,
    desc: '支持PDF、Word、TXT等格式',
    color: 'text-[#3A86FF]'
  },
  {
    id: 'image',
    name: '图片翻译',
    icon: IconImage,
    desc: 'OCR识别图片中的文字',
    color: 'text-[#6C5CE7]'
  },
  {
    id: 'voice',
    name: '语音翻译',
    icon: IconMic,
    desc: '实时语音识别与翻译',
    color: 'text-[#9333EA]'
  },
  {
    id: 'web',
    name: '网页翻译',
    icon: IconGlobe,
    desc: '输入URL自动翻译网页',
    color: 'text-[#0EA5E9]'
  }
]

const selectedType = ref('document')
const sourceLanguage = ref('英语')
const targetLanguage = ref('中文')
const translationMode = ref('academic')
const sourceText = ref(`Machine learning is a branch of artificial intelligence (AI) and computer science which focuses on the use of data and algorithms to imitate the way that humans learn, gradually improving its accuracy. IBM has a rich history with machine learning. One of its own, Arthur Samuel, is credited for coining the term, "machine learning" with his research around the game of checkers.`)
const translatedText = ref(`机器学习是人工智能(AI)和计算机科学的一个分支,它专注于使用数据和算法来模仿人类学习的方式,逐步提高其准确性。IBM在机器学习领域有着丰富的历史。其中的Arthur Samuel因其围绕跳棋游戏的研究而被认为是创造"机器学习"这一术语的人。`)

const languages = [
  '中文', '英语', '日语', '韩语', '法语', '德语', '西班牙语', '俄语', '意大利语', '葡萄牙语'
]

const selectType = (type) => {
  selectedType.value = type.id
}

const filteredUploadedFiles = computed(() => {
  if (fileTypeFilter.value === 'all') return uploadedFiles.value
  return uploadedFiles.value.filter((file) => getUploadedFileType(file) === fileTypeFilter.value)
})

const loadUploadedFiles = async (keyword = fileSearchKeyword.value.trim()) => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用文档上传与翻译工作流。'
    uploadedFiles.value = []
    return
  }

  isLoadingFiles.value = true
  authMessage.value = ''

  try {
    const query = keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''
    const files = await apiRequest(`/files${query}`)
    uploadedFiles.value = files
  } catch (error) {
    errorMessage.value = error.message || '加载已上传文件失败，请稍后重试。'
  } finally {
    isLoadingFiles.value = false
  }
}

const handleFileUpload = () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用文档上传与翻译工作流。'
    return
  }

  authMessage.value = ''
  errorMessage.value = ''
  fileInput.value?.click()
}

const readTextPreviewIfPossible = async (file) => {
  if (getUploadedFileType(file) !== 'text') return

  const raw = await file.text()
  sourceText.value = raw.slice(0, 12000)
}

const handleFileChange = async (event) => {
  const [file] = event.target.files || []
  if (!file) return

  isUploading.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    await readTextPreviewIfPossible(file)

    const formData = new FormData()
    formData.append('upload', file)

    const uploaded = await apiRequest('/files/upload', {
      method: 'POST',
      body: formData
    })

    currentUploadedFileId.value = uploaded.id
    selectedUploadedFile.value = uploaded
    translationSourceMode.value = 'file'
    statusMessage.value = `文件已上传：${uploaded.original_filename}`
    await loadUploadedFiles()
  } catch (error) {
    errorMessage.value = error.message || '文件上传失败，请稍后重试。'
  } finally {
    isUploading.value = false
    if (event.target) {
      event.target.value = ''
    }
  }
}

const fetchAuthorizedFileBlob = async (fileId) => {
  if (!hasAccessToken()) {
    throw new Error('请先登录后再下载文件。')
  }

  const response = await apiRawRequest(`/files/${fileId}/download`)
  return response.blob()
}

const openDownload = async (fileId) => {
  try {
    const blob = await fetchAuthorizedFileBlob(fileId)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = uploadedFiles.value.find((item) => item.id === fileId)?.original_filename || 'download'
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = error.message || '下载文件失败，请稍后重试。'
  }
}

const selectUploadedFile = async (file) => {
  currentUploadedFileId.value = file.id
  selectedUploadedFile.value = file
  translationSourceMode.value = 'file'
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = `已选中文件：${file.original_filename}，点击“开始翻译”将直接使用文件内容。`

  if (getUploadedFileType(file) !== 'text') return

  try {
    const blob = await fetchAuthorizedFileBlob(file.id)
    const text = await blob.text()
    sourceText.value = text.slice(0, 12000)
  } catch (error) {
    errorMessage.value = error.message || '加载文件预览失败，请稍后重试。'
  }
}

const deleteUploadedFile = async (fileId) => {
  try {
    await apiRequest(`/files/${fileId}`, {
      method: 'DELETE'
    })
    uploadedFiles.value = uploadedFiles.value.filter((item) => item.id !== fileId)
    if (currentUploadedFileId.value === fileId) {
      currentUploadedFileId.value = ''
      selectedUploadedFile.value = null
      translationSourceMode.value = 'text'
      statusMessage.value = '已删除当前选中文件，翻译来源已切回文本输入。'
    } else {
      statusMessage.value = '文件已删除。'
    }
  } catch (error) {
    errorMessage.value = error.message || '删除文件失败，请稍后重试。'
  }
}

const translateText = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用翻译接口。'
    return
  }

  if (translationSourceMode.value === 'file' && !currentUploadedFileId.value) {
    errorMessage.value = '请先选中一个已上传文件，再使用文件内容翻译。'
    return
  }

  if (translationSourceMode.value === 'text' && !sourceText.value.trim()) {
    errorMessage.value = '请先输入待翻译文本。'
    return
  }

  isTranslating.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/translate/text', {
      method: 'POST',
      body: {
        source_text: translationSourceMode.value === 'file' ? null : sourceText.value.trim() || null,
        source_language: sourceLanguage.value,
        target_language: targetLanguage.value,
        mode: translationMode.value,
        uploaded_file_id: translationSourceMode.value === 'file' ? currentUploadedFileId.value || null : null
      }
    })
    sourceText.value = payload.source_text
    translatedText.value = payload.translated_text
    statusMessage.value = payload.is_fallback
      ? '当前未配置在线翻译模型，已返回规则版翻译草稿。'
      : `翻译完成，模型：${payload.model_name}`
  } catch (error) {
    errorMessage.value = error.message || '翻译失败，请稍后重试。'
  } finally {
    isTranslating.value = false
  }
}

const readSource = () => {
  statusMessage.value = '语音朗读接口暂未接入，文件上传链路已接通。'
}

const polishTranslation = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用润色接口。'
    return
  }

  if (!translatedText.value.trim()) {
    errorMessage.value = '请先生成译文，再进行润色。'
    return
  }

  isPolishing.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/translate/polish', {
      method: 'POST',
      body: {
        text: translatedText.value,
        language: targetLanguage.value,
        mode: translationMode.value
      }
    })
    translatedText.value = payload.polished_text
    statusMessage.value = payload.is_fallback
      ? '当前未配置在线润色模型，已返回规则版润色结果。'
      : `润色完成，模型：${payload.model_name}`
  } catch (error) {
    errorMessage.value = error.message || '润色失败，请稍后重试。'
  } finally {
    isPolishing.value = false
  }
}

const collectTranslation = () => {
  openSaveToNoteModal()
}

const exportDocument = () => {
  const blob = new Blob([translatedText.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'translation-result.txt'
  anchor.click()
  URL.revokeObjectURL(url)
  statusMessage.value = '已导出当前译文。'
}

const upgradePro = () => {
  statusMessage.value = '专业版能力暂未接入购买流程。'
}

const loadNotebooks = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再保存到笔记。'
    return
  }

  isLoadingNotebooks.value = true
  try {
    const list = await apiRequest('/notes/notebooks')
    notebooks.value = list
    if (list.length && !noteNotebookId.value) {
      noteNotebookId.value = list[0].id
    }
  } catch (error) {
    errorMessage.value = error.message || '加载笔记本失败，请稍后重试。'
  } finally {
    isLoadingNotebooks.value = false
  }
}

const openSaveToNoteModal = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再保存到笔记。'
    return
  }

  if (!sourceText.value.trim() || !translatedText.value.trim()) {
    errorMessage.value = '请先完成翻译，再保存到笔记。'
    return
  }

  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''
  noteTitle.value = buildTranslateNoteTitle({
    uploadedFile: selectedUploadedFile.value,
    sourceText: sourceText.value
  })

  await loadNotebooks()
  showSaveNoteModal.value = true
}

const ensureNotebookForTranslate = async () => {
  if (noteNotebookId.value) return noteNotebookId.value
  if (notebooks.value.length) {
    noteNotebookId.value = notebooks.value[0].id
    return noteNotebookId.value
  }

  const notebook = await apiRequest('/notes/notebooks', {
    method: 'POST',
    body: {
      name: '翻译笔记本',
      description: '自动创建，用于保存翻译结果'
    }
  })
  notebooks.value = [notebook]
  noteNotebookId.value = notebook.id
  return notebook.id
}

const saveTranslationToNote = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再保存到笔记。'
    return
  }

  if (!sourceText.value.trim() || !translatedText.value.trim()) {
    errorMessage.value = '请先完成翻译，再保存到笔记。'
    return
  }

  isSavingNote.value = true
  errorMessage.value = ''

  try {
    const notebookId = await ensureNotebookForTranslate()
    await apiRequest('/notes', {
      method: 'POST',
      body: {
        notebook_id: notebookId,
        title: noteTitle.value.trim() || buildTranslateNoteTitle({
          uploadedFile: selectedUploadedFile.value,
          sourceText: sourceText.value
        }),
        content_markdown: buildTranslateNoteMarkdown({
          title: noteTitle.value.trim() || '翻译笔记',
          sourceLanguage: sourceLanguage.value,
          targetLanguage: targetLanguage.value,
          mode: translationMode.value,
          sourceText: sourceText.value,
          translatedText: translatedText.value,
          uploadedFile: selectedUploadedFile.value
        }),
        source_type: 'manual',
        metadata_json: {
          source: 'translate',
          uploaded_file_id: selectedUploadedFile.value?.id || null,
          uploaded_file_name: selectedUploadedFile.value?.original_filename || null,
          source_language: sourceLanguage.value,
          target_language: targetLanguage.value,
          mode: translationMode.value
        }
      }
    })

    showSaveNoteModal.value = false
    statusMessage.value = '已保存到笔记。'
  } catch (error) {
    errorMessage.value = error.message || '保存到笔记失败，请稍后重试。'
  } finally {
    isSavingNote.value = false
  }
}

onMounted(() => {
  loadUploadedFiles()
})

watch(fileSearchKeyword, (value) => {
  clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    loadUploadedFiles(value)
  }, 250)
})

onUnmounted(() => {
  clearTimeout(searchTimer)
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main
      class="container mx-auto px-4 md:px-10 lg:px-16 py-8 md:py-10 lg:py-12 space-y-8 md:space-y-10"
    >
      <section class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] flex items-center justify-center shadow-md"
          >
            <IconTranslate class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1
              class="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent"
            >
              AI 深度翻译工坊
            </h1>
            <p class="mt-1 text-xs md:text-sm text-slate-500">
              已接通真实文件上传链路，可上传文档并纳入后续翻译工作流。
            </p>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button
            @click="collectTranslation"
            class="flex items-center gap-2 text-slate-600 hover:text-[#3A86FF] transition-colors text-sm"
          >
            <IconStar class="w-5 h-5" />
            <span class="hidden md:inline">保存到笔记</span>
          </button>
          <button
            @click="exportDocument"
            class="flex items-center gap-2 text-slate-600 hover:text-[#3A86FF] transition-colors text-sm"
          >
            <IconDownload class="w-5 h-5" />
            <span class="hidden md:inline">导出文档</span>
          </button>
          <button
            @click="upgradePro"
            class="flex items-center gap-2 bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity text-sm font-medium"
          >
            <IconSparkles class="w-4 h-4" />
            <span>升级专业版</span>
          </button>
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

      <section>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="type in translationTypes"
            :key="type.id"
            @click="selectType(type)"
            :class="[
              'bg-white rounded-xl p-4 cursor-pointer border-2 transition-all hover:shadow-md',
              selectedType === type.id
                ? 'border-[#3A86FF] shadow-md'
                : 'border-slate-200 hover:border-slate-300'
            ]"
          >
            <div class="flex items-start gap-3">
              <div :class="['w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center', type.color]">
                <component :is="type.icon" class="w-5 h-5" />
              </div>
              <div class="flex-1">
                <h3 class="font-semibold text-slate-900 mb-1">{{ type.name }}</h3>
                <p class="text-xs text-slate-500">{{ type.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid lg:grid-cols-[1.4fr_1fr] gap-4">
        <div class="bg-white rounded-xl border-2 border-dashed border-slate-300 p-8 md:p-12">
          <div class="flex flex-col items-center justify-center text-center">
            <div class="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <IconUpload class="w-8 h-8 text-slate-400" />
            </div>
            <h3 class="text-lg font-semibold text-slate-900 mb-2">上传翻译素材</h3>
            <p class="text-sm text-slate-500 mb-6 max-w-md">
              目前已接通真实文件上传接口。上传后的文档会进入你的文件列表，为后续翻译、OCR 和知识库流程做准备。
            </p>
            <button
              @click="handleFileUpload"
              class="px-6 py-2 bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-60"
              :disabled="isUploading"
            >
              {{ isUploading ? '上传中...' : '选择文件' }}
            </button>
            <input
              ref="fileInput"
              type="file"
              class="hidden"
              @change="handleFileChange"
            />
          </div>
        </div>

        <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-slate-900">最近上传</h3>
            <span class="text-xs text-slate-400">
              {{ isLoadingFiles ? '加载中...' : `${uploadedFiles.length} 个文件` }}
            </span>
          </div>
          <div class="mb-3 space-y-3">
            <input
              v-model="fileSearchKeyword"
              type="text"
              placeholder="搜索文件名..."
              class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-[#3A86FF] focus:outline-none"
            />
            <div class="flex flex-wrap gap-2">
              <button
                v-for="filter in [
                  { value: 'all', label: '全部' },
                  { value: 'text', label: '文本' },
                  { value: 'image', label: '图片' },
                  { value: 'other', label: '其他' }
                ]"
                :key="filter.value"
                type="button"
                :class="[
                  'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                  fileTypeFilter === filter.value
                    ? 'bg-[#3A86FF] text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                ]"
                @click="fileTypeFilter = filter.value"
              >
                {{ filter.label }}
              </button>
            </div>
          </div>
          <div class="space-y-2 max-h-[260px] overflow-y-auto">
            <div
              v-for="file in filteredUploadedFiles"
              :key="file.id"
              :class="[
                'rounded-xl border px-3 py-3 text-sm',
                currentUploadedFileId === file.id
                  ? 'border-[#3A86FF] bg-blue-50'
                  : 'border-slate-200 bg-slate-50'
              ]"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate font-medium text-slate-900">{{ file.original_filename }}</p>
                  <p class="text-xs text-slate-500 mt-1">
                    {{ file.mime_type || '未知类型' }} · {{ file.size_bytes || 0 }} bytes
                  </p>
                </div>
                <div class="flex items-center gap-3">
                  <button
                    type="button"
                    class="text-xs text-slate-500 hover:text-[#3A86FF]"
                    @click="selectUploadedFile(file)"
                  >
                    选中
                  </button>
                  <button
                    type="button"
                    class="text-xs text-[#3A86FF] hover:underline whitespace-nowrap"
                    @click="openDownload(file.id)"
                  >
                    下载
                  </button>
                  <button
                    type="button"
                    class="text-xs text-rose-500 hover:underline whitespace-nowrap"
                    @click="deleteUploadedFile(file.id)"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
            <p v-if="!filteredUploadedFiles.length && !isLoadingFiles" class="text-sm text-slate-400">
              暂无上传文件，先上传一个文档试试。
            </p>
          </div>
        </div>
      </section>

      <section>
        <div class="mb-4 flex justify-end">
          <button
            type="button"
            @click="translateText"
            class="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity disabled:opacity-60"
            :disabled="isTranslating"
          >
            <IconTranslate class="w-4 h-4 text-white" />
            <span>{{ isTranslating ? '翻译中...' : '开始翻译' }}</span>
          </button>
        </div>
        <div class="grid lg:grid-cols-2 gap-4">
          <div class="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col">
            <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <select
                  v-model="sourceLanguage"
                  class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#3A86FF] bg-white"
                >
                  <option v-for="lang in languages" :key="lang" :value="lang">{{ lang }}</option>
                </select>
                <button
                  @click="readSource"
                  class="flex items-center gap-1.5 text-slate-600 hover:text-[#3A86FF] transition-colors text-sm"
                >
                  <IconVolume class="w-4 h-4" />
                  <span>朗读原文</span>
                </button>
              </div>
            </div>
            <div class="flex-1 p-4">
              <div class="mb-3 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  @click="translationSourceMode = 'text'"
                  :class="[
                    'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
                    translationSourceMode === 'text'
                      ? 'bg-[#3A86FF] text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  ]"
                >
                  使用文本
                </button>
                <button
                  type="button"
                  @click="translationSourceMode = 'file'"
                  :disabled="!currentUploadedFileId"
                  :class="[
                    'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50',
                    translationSourceMode === 'file'
                      ? 'bg-[#6C5CE7] text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  ]"
                >
                  使用已选文件
                </button>
                <span
                  v-if="translationSourceMode === 'file' && currentUploadedFileId"
                  class="text-xs text-slate-500"
                >
                  当前将直接使用选中文件内容翻译
                </span>
              </div>
              <textarea
                v-model="sourceText"
                class="w-full h-full min-h-[400px] resize-none border-none focus:outline-none text-sm text-slate-700 leading-relaxed"
                placeholder="在此输入或粘贴需要翻译的文本，或上传纯文本文件后自动预览。"
                @input="translationSourceMode = 'text'"
              ></textarea>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col">
            <div class="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <select
                  v-model="targetLanguage"
                  class="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#3A86FF] bg-white"
                >
                  <option v-for="lang in languages" :key="lang" :value="lang">{{ lang }}</option>
                </select>
                <div class="flex items-center gap-2">
                  <button
                    @click="translationMode = 'academic'"
                    :class="[
                      'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                      translationMode === 'academic'
                        ? 'bg-[#3A86FF] text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    ]"
                  >
                    学术模式
                  </button>
                  <button
                    @click="translationMode = 'colloquial'"
                    :class="[
                      'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                      translationMode === 'colloquial'
                        ? 'bg-[#3A86FF] text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    ]"
                  >
                    口语模式
                  </button>
                </div>
              </div>
            </div>
            <div class="flex-1 p-4 relative">
              <textarea
                v-model="translatedText"
                class="w-full h-full min-h-[400px] resize-none border-none focus:outline-none text-sm text-slate-700 leading-relaxed"
                placeholder="翻译结果将显示在这里。当前页面已接通上传链路，翻译能力可在下一步继续接后端。"
              ></textarea>
              <button
                @click="polishTranslation"
                class="absolute bottom-4 right-4 flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 hover:border-[#3A86FF] hover:text-[#3A86FF] transition-colors shadow-sm"
                :disabled="isPolishing"
              >
                <IconSparkles class="w-3.5 h-3.5" />
                <span>{{ isPolishing ? '润色中...' : '润色' }}</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>

  <div
    v-if="showSaveNoteModal"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm p-4"
    @click.self="showSaveNoteModal = false"
  >
    <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-slate-900">保存到笔记</h3>
        <button
          type="button"
          class="text-slate-400 hover:text-slate-600 text-xl"
          @click="showSaveNoteModal = false"
        >
          ×
        </button>
      </div>

      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">笔记本</label>
          <select
            v-model="noteNotebookId"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            :disabled="isLoadingNotebooks"
          >
            <option v-if="!notebooks.length" value="">
              {{ isLoadingNotebooks ? '加载中...' : '将自动创建默认翻译笔记本' }}
            </option>
            <option
              v-for="notebook in notebooks"
              :key="notebook.id"
              :value="notebook.id"
            >
              {{ notebook.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700">笔记标题</label>
          <input
            v-model="noteTitle"
            type="text"
            class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-[#3A86FF] focus:outline-none"
            placeholder="请输入笔记标题"
          />
        </div>

        <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-xs text-slate-600">
          <p>将保存当前源语言、目标语言、翻译模式、原文和译文。</p>
          <p v-if="selectedUploadedFile">来源文件：{{ selectedUploadedFile.original_filename }}</p>
        </div>

        <div class="flex gap-3 pt-2">
          <button
            type="button"
            class="flex-1 rounded-lg border border-slate-200 px-4 py-2 text-slate-700 hover:bg-slate-50 transition-colors"
            @click="showSaveNoteModal = false"
          >
            取消
          </button>
          <button
            type="button"
            class="flex-1 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-2 text-white hover:opacity-90 transition-opacity disabled:opacity-60"
            :disabled="isSavingNote"
            @click="saveTranslationToNote"
          >
            {{ isSavingNote ? '保存中...' : '保存到笔记' }}
          </button>
        </div>
      </div>
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
