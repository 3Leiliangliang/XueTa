<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import IconDocument from '@/components/icons/IconDocument.vue'
import IconRight from '@/components/icons/IconRight.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const route = useRoute()
const router = useRouter()

defineOptions({
  name: 'KnowledgeBaseView'
})

const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isLoading = ref(false)
const isCreatingBase = ref(false)
const isCreatingDocument = ref(false)
const isSearching = ref(false)
const isLoadingChunks = ref(false)

const bases = ref([])
const documents = ref([])
const chunks = ref([])
const hits = ref([])
const activeBaseId = ref('')
const activeDocumentId = ref('')
const activeChunkId = ref('')
const documentKeyword = ref('')
const retrieveQuery = ref('')
const activeContentTab = ref('documents')
const showCreateBase = ref(false)
const showCreateDocument = ref(false)

const baseForm = ref({
  name: '',
  subject: '',
  description: ''
})

const documentForm = ref({
  title: '',
  sourceUrl: '',
  contentText: '',
  tagsText: ''
})

const selectedDocument = computed(
  () => documents.value.find((item) => item.id === activeDocumentId.value) || null
)

const activeBase = computed(
  () => bases.value.find((item) => item.id === activeBaseId.value) || null
)

const totalDocumentCount = computed(() =>
  bases.value.reduce((total, item) => total + Number(item.document_count || 0), 0)
)

const syncRouteQuery = () => {
  const nextQuery = {
    ...route.query,
    baseId: activeBaseId.value || undefined,
    documentId: activeDocumentId.value || undefined,
    chunkId: activeChunkId.value || undefined
  }
  router.replace({ query: nextQuery })
}

const focusChunk = async (chunkId, { syncQuery = true } = {}) => {
  if (!chunkId) return
  activeChunkId.value = chunkId
  if (syncQuery) {
    syncRouteQuery()
  }
  await nextTick()
  const target = document.getElementById(`kb-chunk-${chunkId}`)
  target?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

const loadBases = async ({ preserveBase = false, selectedDocumentId = '' } = {}) => {
  const baseList = await apiRequest('/kb/bases')
  bases.value = baseList

  if (!baseList.length) {
    activeBaseId.value = ''
    documents.value = []
    activeDocumentId.value = ''
    activeChunkId.value = ''
    chunks.value = []
    hits.value = []
    return
  }

  if (preserveBase && baseList.some((item) => item.id === activeBaseId.value)) {
    await loadDocuments(activeBaseId.value, documentKeyword.value.trim(), { preserveDocument: true, selectedDocumentId })
    return
  }

  activeBaseId.value = baseList[0].id
  await loadDocuments(activeBaseId.value, '', { preserveDocument: false, selectedDocumentId })
}

const loadDocuments = async (baseId, keyword = '', { preserveDocument = false, selectedDocumentId = '' } = {}) => {
  if (!baseId) {
    documents.value = []
    activeDocumentId.value = ''
    activeChunkId.value = ''
    chunks.value = []
    return
  }

  const query = new URLSearchParams({ knowledge_base_id: baseId })
  if (keyword) {
    query.set('keyword', keyword)
  }
  const list = await apiRequest(`/kb/documents?${query.toString()}`)
  documents.value = list

  if (!list.length) {
    activeDocumentId.value = ''
    activeChunkId.value = ''
    chunks.value = []
    return
  }

  if (selectedDocumentId && list.some((item) => item.id === selectedDocumentId)) {
    activeDocumentId.value = selectedDocumentId
    await loadChunks(selectedDocumentId)
    return
  }

  if (preserveDocument && list.some((item) => item.id === activeDocumentId.value)) {
    await loadChunks(activeDocumentId.value)
    return
  }

  activeDocumentId.value = list[0].id
  await loadChunks(activeDocumentId.value)
}

const loadChunks = async (documentId) => {
  if (!documentId) {
    chunks.value = []
    activeChunkId.value = ''
    return
  }

  isLoadingChunks.value = true
  try {
    const chunkList = await apiRequest(`/kb/documents/${documentId}/chunks`)
    chunks.value = chunkList
  } catch (error) {
    errorMessage.value = error.message || '加载切块失败，请稍后重试。'
  } finally {
    isLoadingChunks.value = false
  }
}

const loadKnowledgeData = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用知识库功能。'
    bases.value = []
    documents.value = []
    chunks.value = []
    hits.value = []
    activeChunkId.value = ''
    return
  }

  isLoading.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    await loadBases()
  } catch (error) {
    errorMessage.value = error.message || '加载知识库数据失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const selectBase = async (baseId) => {
  activeBaseId.value = baseId
  documentKeyword.value = ''
  hits.value = []
  activeContentTab.value = 'documents'
  errorMessage.value = ''
  activeChunkId.value = ''
  await loadDocuments(baseId, '')
  syncRouteQuery()
}

const selectDocument = async (documentId) => {
  activeDocumentId.value = documentId
  hits.value = []
  activeChunkId.value = ''
  await loadChunks(documentId)
  syncRouteQuery()
}

const searchDocuments = async () => {
  try {
    activeContentTab.value = 'documents'
    await loadDocuments(activeBaseId.value, documentKeyword.value.trim(), {
      preserveDocument: true
    })
  } catch (error) {
    errorMessage.value = error.message || '搜索文档失败，请稍后重试。'
  }
}

const createBase = async () => {
  if (isCreatingBase.value) return
  if (!baseForm.value.name.trim()) {
    errorMessage.value = '请先填写知识库名称。'
    return
  }

  isCreatingBase.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const base = await apiRequest('/kb/bases', {
      method: 'POST',
      body: {
        name: baseForm.value.name.trim(),
        subject: baseForm.value.subject.trim() || null,
        description: baseForm.value.description.trim() || null,
        is_public: false
      }
    })
    baseForm.value.name = ''
    baseForm.value.subject = ''
    baseForm.value.description = ''
    statusMessage.value = `知识库“${base.name}”已创建。`
    showCreateBase.value = false
    activeBaseId.value = base.id
    await loadBases({ preserveBase: true })
  } catch (error) {
    errorMessage.value = error.message || '创建知识库失败，请稍后重试。'
  } finally {
    isCreatingBase.value = false
  }
}

const createDocument = async () => {
  if (isCreatingDocument.value) return
  if (!activeBaseId.value) {
    errorMessage.value = '请先选择一个知识库。'
    return
  }
  if (!documentForm.value.title.trim()) {
    errorMessage.value = '请填写文档标题。'
    return
  }
  if (!documentForm.value.contentText.trim() && !documentForm.value.sourceUrl.trim()) {
    errorMessage.value = '请填写文档正文，或提供网页地址用于自动解析。'
    return
  }

  isCreatingDocument.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const tags = documentForm.value.tagsText
      .split(/[，,\n]/)
      .map((item) => item.trim())
      .filter(Boolean)

    const document = await apiRequest('/kb/documents', {
      method: 'POST',
      body: {
        knowledge_base_id: activeBaseId.value,
        title: documentForm.value.title.trim(),
        source_type: documentForm.value.sourceUrl.trim() ? 'web' : 'manual',
        source_url: documentForm.value.sourceUrl.trim() || null,
        content_text: documentForm.value.contentText.trim() || null,
        tags: tags.length ? tags : null
      }
    })
    documentForm.value.title = ''
    documentForm.value.sourceUrl = ''
    documentForm.value.contentText = ''
    documentForm.value.tagsText = ''
    statusMessage.value = `文档“${document.title}”已创建并自动切块。`
    showCreateDocument.value = false
    activeContentTab.value = 'documents'
    await loadDocuments(activeBaseId.value, documentKeyword.value.trim())
    activeDocumentId.value = document.id
    await loadChunks(document.id)
    syncRouteQuery()
  } catch (error) {
    errorMessage.value = error.message || '创建文档失败，请稍后重试。'
  } finally {
    isCreatingDocument.value = false
  }
}

const deleteBase = async (baseId, name) => {
  if (!window.confirm(`确定删除知识库“${name}”吗？`)) return

  try {
    await apiRequest(`/kb/bases/${baseId}`, {
      method: 'DELETE'
    })
    statusMessage.value = '知识库已删除。'
    if (activeBaseId.value === baseId) {
      activeBaseId.value = ''
      activeDocumentId.value = ''
      activeChunkId.value = ''
      hits.value = []
      chunks.value = []
    }
    await loadBases()
  } catch (error) {
    errorMessage.value = error.message || '删除知识库失败，请稍后重试。'
  }
}

const deleteDocument = async (documentId, title) => {
  if (!window.confirm(`确定删除文档“${title}”吗？`)) return

  try {
    await apiRequest(`/kb/documents/${documentId}`, {
      method: 'DELETE'
    })
    statusMessage.value = '文档已删除。'
    if (activeDocumentId.value === documentId) {
      activeDocumentId.value = ''
      activeChunkId.value = ''
      chunks.value = []
    }
    await loadDocuments(activeBaseId.value, documentKeyword.value.trim())
  } catch (error) {
    errorMessage.value = error.message || '删除文档失败，请稍后重试。'
  }
}

const retrieveKnowledge = async () => {
  if (isSearching.value) return
  if (!retrieveQuery.value.trim()) {
    errorMessage.value = '请输入检索问题或关键词。'
    return
  }

  isSearching.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/kb/retrieve', {
      method: 'POST',
      body: {
        query: retrieveQuery.value.trim(),
        knowledge_base_id: activeBaseId.value || null,
        limit: 6
      }
    })
    hits.value = payload.hits
    activeContentTab.value = 'results'
    statusMessage.value = payload.total_hits
      ? `检索完成，共找到 ${payload.total_hits} 条命中。`
      : '没有命中结果，可以换个关键词再试。'
  } catch (error) {
    errorMessage.value = error.message || '知识检索失败，请稍后重试。'
  } finally {
    isSearching.value = false
  }
}

const openDocumentLocation = async (documentId, chunkId = '') => {
  if (!documentId) return

  try {
    const documentDetail = await apiRequest(`/kb/documents/${documentId}`)
    activeBaseId.value = documentDetail.knowledge_base_id
    documentKeyword.value = ''
    await loadDocuments(documentDetail.knowledge_base_id, '', {
      preserveDocument: false,
      selectedDocumentId: documentId
    })
    if (chunkId) {
      await focusChunk(chunkId, { syncQuery: false })
    } else {
      activeChunkId.value = ''
    }
    syncRouteQuery()
  } catch (error) {
    errorMessage.value = error.message || '定位知识库文档失败，请稍后重试。'
  }
}

const applyRouteSelection = async () => {
  const documentId = typeof route.query.documentId === 'string' ? route.query.documentId : ''
  const chunkId = typeof route.query.chunkId === 'string' ? route.query.chunkId : ''
  const baseId = typeof route.query.baseId === 'string' ? route.query.baseId : ''

  if (!hasAccessToken()) return
  if (documentId) {
    await openDocumentLocation(documentId, chunkId)
    return
  }
  if (baseId && baseId !== activeBaseId.value) {
    await selectBase(baseId)
  }
  if (chunkId && chunks.value.some((chunk) => chunk.id === chunkId)) {
    await focusChunk(chunkId, { syncQuery: false })
  }
}

onMounted(() => {
  loadKnowledgeData()
})

watch(
  () => route.query,
  () => {
    applyRouteSelection()
  }
)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-white">
    <main class="mx-auto max-w-[1840px] space-y-6 px-4 py-8 md:px-8 lg:px-12">
      <section class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-3xl font-bold tracking-normal text-transparent md:text-4xl">
            知识库中心
          </h1>
          <p class="mt-3 text-base text-slate-500">
            管理学习资料，支持知识检索和来源追溯。
          </p>
        </div>

        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
          :disabled="isCreatingBase"
          @click="showCreateBase = !showCreateBase"
        >
          <span class="text-lg leading-none">+</span>
          新建知识库
        </button>
      </section>

      <section v-if="authMessage || errorMessage || statusMessage" class="space-y-3">
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
        v-if="showCreateBase"
        class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">新建知识库</h2>
          <button
            type="button"
            class="text-sm text-slate-400 transition hover:text-slate-700"
            @click="showCreateBase = false"
          >
            收起
          </button>
        </div>
        <div class="grid gap-4 lg:grid-cols-[1fr_1fr_1.4fr_auto] lg:items-end">
          <label class="space-y-2">
            <span class="text-sm font-medium text-slate-700">名称</span>
            <Input v-model="baseForm.name" placeholder="例如：JavaScript 学习资料" />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-medium text-slate-700">学科</span>
            <Input v-model="baseForm.subject" placeholder="例如：前端 / 数学" />
          </label>
          <label class="space-y-2">
            <span class="text-sm font-medium text-slate-700">描述</span>
            <Input v-model="baseForm.description" placeholder="资料来源、课程范围或适用场景" />
          </label>
          <button
            type="button"
            class="h-10 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 text-sm text-white transition hover:opacity-90 disabled:opacity-60"
            :disabled="isCreatingBase"
            @click="createBase"
          >
            {{ isCreatingBase ? '创建中...' : '创建' }}
          </button>
        </div>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="flex flex-col gap-3 md:flex-row">
          <label class="relative min-w-0 flex-1">
            <IconSearch class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
            <input
              v-model="retrieveQuery"
              type="search"
              placeholder="输入问题或关键词检索知识库..."
              class="h-14 w-full rounded-xl border border-slate-200 bg-slate-50 pl-12 pr-4 text-base text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-[#3A86FF] focus:bg-white focus:ring-2 focus:ring-[#3A86FF]/15"
              @keyup.enter="retrieveKnowledge"
            />
          </label>
          <button
            type="button"
            class="h-14 rounded-xl bg-[#3A86FF] px-8 text-base font-medium text-white transition hover:bg-[#2f74df] disabled:opacity-60"
            :disabled="isSearching"
            @click="retrieveKnowledge"
          >
            {{ isSearching ? '检索中...' : '检索' }}
          </button>
        </div>
      </section>

      <section class="grid gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
        <aside class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div class="mb-6 flex items-center gap-3">
            <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[#3A86FF]/10 text-[#3A86FF]">
              <IconDocument class="h-5 w-5" />
            </div>
            <div>
              <h2 class="text-lg font-semibold text-slate-950">知识库</h2>
              <p class="text-xs text-slate-400">
                {{ bases.length }} 个知识库 · {{ totalDocumentCount }} 篇文档
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <div
              v-for="base in bases"
              :key="base.id"
              :class="[
                'group flex w-full items-center gap-2 rounded-xl border transition',
                activeBaseId === base.id
                  ? 'border-[#3A86FF]/30 bg-[#3A86FF]/10 text-[#1f5fd6]'
                  : 'border-transparent bg-white text-slate-700 hover:bg-slate-50'
              ]"
            >
              <button
                type="button"
                class="flex min-w-0 flex-1 items-center gap-3 px-3 py-3 text-left"
                @click="selectBase(base.id)"
              >
                <span
                  :class="[
                    'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border',
                    activeBaseId === base.id
                      ? 'border-[#3A86FF]/25 bg-white text-[#3A86FF]'
                      : 'border-slate-200 bg-slate-50 text-slate-400'
                  ]"
                >
                  <IconDocument class="h-4 w-4" />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-semibold">{{ base.name }}</span>
                  <span class="mt-0.5 block truncate text-xs text-slate-400">
                    {{ base.subject || '未分类' }}
                  </span>
                </span>
              </button>
              <span class="text-xs text-slate-400">{{ base.document_count || 0 }}</span>
              <button
                type="button"
                class="mr-2 rounded-md px-1.5 py-1 text-xs text-slate-300 opacity-0 transition hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
                @click="deleteBase(base.id, base.name)"
              >
                删除
              </button>
            </div>

            <p v-if="!bases.length && !isLoading" class="rounded-xl bg-slate-50 px-3 py-4 text-sm text-slate-500">
              当前还没有知识库，点击右上角按钮创建。
            </p>
          </div>
        </aside>

        <section class="min-w-0 space-y-5">
          <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div class="inline-flex rounded-xl bg-slate-100 p-1">
              <button
                type="button"
                :class="[
                  'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition',
                  activeContentTab === 'documents'
                    ? 'bg-white text-slate-950 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                ]"
                @click="activeContentTab = 'documents'"
              >
                <IconDocument class="h-4 w-4" />
                文档
              </button>
              <button
                type="button"
                :class="[
                  'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition',
                  activeContentTab === 'results'
                    ? 'bg-white text-slate-950 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                ]"
                @click="activeContentTab = 'results'"
              >
                <IconSearch class="h-4 w-4" />
                检索结果
              </button>
            </div>

            <div class="flex flex-col gap-2 sm:flex-row">
              <label class="relative">
                <IconSearch class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  v-model="documentKeyword"
                  type="search"
                  placeholder="搜索当前知识库文档"
                  class="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-700 outline-none transition focus:border-[#3A86FF] focus:ring-2 focus:ring-[#3A86FF]/15 sm:w-60"
                  @keyup.enter="searchDocuments"
                />
              </label>
              <button
                type="button"
                class="h-10 rounded-lg border border-slate-200 bg-white px-4 text-sm text-slate-700 transition hover:bg-slate-50"
                @click="searchDocuments"
              >
                搜文档
              </button>
              <button
                type="button"
                class="h-10 rounded-lg border border-slate-200 bg-white px-4 text-sm font-medium text-slate-800 transition hover:border-[#3A86FF]/40 hover:text-[#3A86FF]"
                @click="showCreateDocument = !showCreateDocument"
              >
                + 添加文档
              </button>
            </div>
          </div>

          <section
            v-if="showCreateDocument"
            class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div class="mb-4 flex items-center justify-between">
              <div>
                <h2 class="text-lg font-semibold text-slate-900">添加文档</h2>
                <p class="mt-1 text-sm text-slate-500">
                  {{ activeBase ? `添加到「${activeBase.name}」` : '请先选择一个知识库' }}
                </p>
              </div>
              <button
                type="button"
                class="text-sm text-slate-400 transition hover:text-slate-700"
                @click="showCreateDocument = false"
              >
                收起
              </button>
            </div>
            <div class="grid gap-4 lg:grid-cols-2">
              <label class="space-y-2">
                <span class="text-sm font-medium text-slate-700">文档标题</span>
                <Input v-model="documentForm.title" placeholder="例如：函数极限讲义" />
              </label>
              <label class="space-y-2">
                <span class="text-sm font-medium text-slate-700">标签</span>
                <Input v-model="documentForm.tagsText" placeholder="例如：极限, 连续性, 例题" />
              </label>
              <label class="space-y-2 lg:col-span-2">
                <span class="text-sm font-medium text-slate-700">网页地址（可选）</span>
                <Input v-model="documentForm.sourceUrl" placeholder="https://example.com/article" />
              </label>
              <label class="space-y-2 lg:col-span-2">
                <span class="text-sm font-medium text-slate-700">文档正文</span>
                <textarea
                  v-model="documentForm.contentText"
                  class="min-h-[180px] w-full rounded-lg border border-slate-200 px-3 py-3 text-sm leading-6 text-slate-700 outline-none transition focus:border-[#3A86FF] focus:ring-2 focus:ring-[#3A86FF]/15"
                  placeholder="粘贴课程讲义、知识点总结或例题解析；如果填写了网页地址，也可以留空让系统自动抓取正文。"
                ></textarea>
              </label>
            </div>
            <div class="mt-4 flex justify-end">
              <button
                type="button"
                class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-2 text-sm text-white transition hover:opacity-90 disabled:opacity-60"
                :disabled="isCreatingDocument"
                @click="createDocument"
              >
                {{ isCreatingDocument ? '添加中...' : '添加文档' }}
              </button>
            </div>
          </section>

          <section
            v-if="activeContentTab === 'documents'"
            class="grid gap-4 xl:grid-cols-2"
          >
            <button
              v-for="document in documents"
              :key="document.id"
              type="button"
              :class="[
                'group rounded-2xl border bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[#3A86FF]/40 hover:shadow-md',
                activeDocumentId === document.id ? 'border-[#3A86FF]/40 bg-[#3A86FF]/5' : 'border-slate-200'
              ]"
              @click="selectDocument(document.id)"
            >
              <div class="flex items-start gap-4">
                <div class="min-w-0 flex-1">
                  <p class="truncate text-lg font-semibold text-slate-950">{{ document.title }}</p>
                  <p class="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">
                    {{ document.content_text || document.source_url || '该文档已录入知识库，可查看切块并用于检索。' }}
                  </p>
                </div>
                <IconRight class="mt-1 h-5 w-5 shrink-0 text-slate-300 transition group-hover:text-[#3A86FF]" />
              </div>
              <div class="mt-4 flex items-center justify-between gap-4 text-sm text-slate-500">
                <span>{{ document.source_type === 'web' ? '网页' : '手动录入' }}</span>
                <span>{{ document.chunk_count || 0 }} 个切块</span>
              </div>
              <div class="mt-4 flex items-center justify-between gap-3">
                <div class="flex min-w-0 flex-wrap gap-2">
                  <span
                    v-for="tag in document.tags || []"
                    :key="tag"
                    class="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600"
                  >
                    {{ tag }}
                  </span>
                </div>
                <button
                  type="button"
                  class="shrink-0 text-xs text-rose-500 transition hover:text-rose-600"
                  @click.stop="deleteDocument(document.id, document.title)"
                >
                  删除
                </button>
              </div>
            </button>

            <p
              v-if="!documents.length && !isLoading"
              class="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500 xl:col-span-2"
            >
              当前知识库还没有文档，点击“添加文档”录入第一篇资料。
            </p>
          </section>

          <section v-if="activeContentTab === 'results'" class="space-y-4">
            <div
              v-for="hit in hits"
              :key="hit.chunk_id"
              class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="truncate text-lg font-semibold text-slate-950">{{ hit.document_title }}</p>
                <span class="rounded-full bg-[#3A86FF]/10 px-2.5 py-1 text-xs font-semibold text-[#3A86FF]">
                  {{ hit.score }}
                </span>
              </div>
              <p class="mt-2 text-xs text-slate-400">
                chunk #{{ hit.chunk_index }} · {{ hit.tags?.join(' / ') || '无标签' }}
              </p>
              <p class="mt-4 whitespace-pre-line text-sm leading-7 text-slate-700">
                {{ hit.content }}
              </p>
              <button
                type="button"
                class="mt-4 text-sm font-medium text-[#3A86FF] hover:underline"
                @click="openDocumentLocation(hit.document_id, hit.chunk_id)"
              >
                定位到来源
              </button>
            </div>

            <p
              v-if="!hits.length && !isSearching"
              class="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500"
            >
              检索结果会显示在这里。
            </p>
          </section>

          <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 class="text-lg font-semibold text-slate-950">
                  {{ selectedDocument?.title || '知识库内容预览' }}
                </h2>
                <p class="mt-1 text-sm text-slate-500">
                  {{ activeBase ? activeBase.name : '选择左侧知识库后查看内容' }}
                </p>
              </div>
              <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">
                {{ isLoadingChunks ? '加载中...' : `${chunks.length} 个切块` }}
              </span>
            </div>

            <div class="mt-4 grid gap-3">
              <article
                v-for="chunk in chunks"
                :id="`kb-chunk-${chunk.id}`"
                :key="chunk.id"
                :class="[
                  'rounded-xl border px-4 py-3 transition',
                  activeChunkId === chunk.id
                    ? 'border-[#3A86FF]/40 bg-[#3A86FF]/10'
                    : 'border-slate-200 bg-slate-50'
                ]"
              >
                <p class="text-xs font-semibold text-[#3A86FF]">Chunk {{ chunk.chunk_index }}</p>
                <p class="mt-2 whitespace-pre-line text-sm leading-7 text-slate-700">
                  {{ chunk.content }}
                </p>
              </article>

              <p
                v-if="!chunks.length && !isLoadingChunks"
                class="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500"
              >
                选择一篇文档后，这里会展示切块内容。
              </p>
            </div>
          </section>
        </section>
      </section>
    </main>
  </div>
</template>

<style scoped></style>
