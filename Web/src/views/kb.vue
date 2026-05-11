<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import IconDocument from '@/components/icons/IconDocument.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const route = useRoute()
const router = useRouter()

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
    await loadBases()
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
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main class="container mx-auto space-y-8 px-4 py-8 md:px-10 md:py-10 lg:px-16 lg:py-12">
      <section class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-md">
            <IconDocument class="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-2xl font-bold text-transparent md:text-3xl lg:text-4xl">
              知识库中心
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              管理知识库、录入文档、查看切块，并基于关键词完成快速检索。
            </p>
          </div>
        </div>
        <button
          type="button"
          class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          :disabled="isLoading"
          @click="loadKnowledgeData"
        >
          {{ isLoading ? '刷新中...' : '刷新知识库' }}
        </button>
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

      <section class="grid gap-6 xl:grid-cols-[0.82fr_1.05fr_1.13fr]">
        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">知识库列表</h2>
              <span class="text-xs text-slate-400">{{ bases.length }} 个</span>
            </div>
            <div class="mt-4 space-y-3">
              <button
                v-for="base in bases"
                :key="base.id"
                type="button"
                :class="[
                  'w-full rounded-2xl border px-4 py-3 text-left transition-colors',
                  activeBaseId === base.id
                    ? 'border-[#3A86FF] bg-blue-50'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                ]"
                @click="selectBase(base.id)"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <p class="truncate font-medium text-slate-900">{{ base.name }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ base.subject || '未分类' }} · {{ base.document_count }} 篇文档
                    </p>
                  </div>
                  <button
                    type="button"
                    class="text-xs text-rose-500 hover:underline"
                    @click.stop="deleteBase(base.id, base.name)"
                  >
                    删除
                  </button>
                </div>
              </button>
              <p v-if="!bases.length && !isLoading" class="text-sm text-slate-400">
                当前还没有知识库，先创建一个再录入文档。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">新建知识库</h2>
            <div class="mt-4 space-y-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">名称</label>
                <Input v-model="baseForm.name" placeholder="例如：高数知识库" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">学科</label>
                <Input v-model="baseForm.subject" placeholder="例如：数学" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">描述</label>
                <textarea
                  v-model="baseForm.description"
                  class="min-h-[110px] w-full rounded-md border border-slate-200 px-3 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:ring-offset-2"
                  placeholder="补充这个知识库的用途、课程来源或适用范围。"
                ></textarea>
              </div>
              <div class="flex justify-end">
                <button
                  type="button"
                  class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                  :disabled="isCreatingBase"
                  @click="createBase"
                >
                  {{ isCreatingBase ? '创建中...' : '创建知识库' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <h2 class="text-lg font-semibold text-slate-900">文档列表</h2>
              <div class="flex items-center gap-2">
                <Input
                  v-model="documentKeyword"
                  placeholder="搜索当前知识库文档"
                  class="w-full md:w-56"
                />
                <button
                  type="button"
                  class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
                  @click="searchDocuments"
                >
                  搜索
                </button>
              </div>
            </div>
            <div class="mt-4 space-y-3">
              <button
                v-for="document in documents"
                :key="document.id"
                type="button"
                :class="[
                  'w-full rounded-2xl border px-4 py-3 text-left transition-colors',
                  activeDocumentId === document.id
                    ? 'border-[#3A86FF] bg-blue-50'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                ]"
                @click="selectDocument(document.id)"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <p class="truncate font-medium text-slate-900">{{ document.title }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ document.chunk_count }} 个切块 · {{ document.tags?.join(' / ') || '无标签' }}
                    </p>
                  </div>
                  <button
                    type="button"
                    class="text-xs text-rose-500 hover:underline"
                    @click.stop="deleteDocument(document.id, document.title)"
                  >
                    删除
                  </button>
                </div>
              </button>
              <p v-if="!documents.length && !isLoading" class="text-sm text-slate-400">
                当前知识库还没有文档，右下方可以直接手动录入一篇。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">录入文档</h2>
            <p class="mt-1 text-sm text-slate-500">
              先接通手动录入流程，后续可以继续扩展上传文件导入和 OCR。
            </p>
            <div class="mt-4 space-y-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">文档标题</label>
                <Input v-model="documentForm.title" placeholder="例如：函数极限讲义" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">标签</label>
                <Input v-model="documentForm.tagsText" placeholder="例如：极限, 连续性, 例题" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">网页地址（可选）</label>
                <Input v-model="documentForm.sourceUrl" placeholder="https://example.com/article" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">文档正文</label>
                <textarea
                  v-model="documentForm.contentText"
                  class="min-h-[240px] w-full rounded-md border border-slate-200 px-3 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:ring-offset-2"
                  placeholder="粘贴课程讲义、知识点总结或例题解析；如果填写了网页地址，也可以留空让系统自动抓取正文。"
                ></textarea>
              </div>
              <div class="flex justify-end">
                <button
                  type="button"
                  class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                  :disabled="isCreatingDocument"
                  @click="createDocument"
                >
                  {{ isCreatingDocument ? '录入中...' : '录入文档' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center gap-2">
              <IconSearch class="h-4 w-4 text-[#3A86FF]" />
              <h2 class="text-lg font-semibold text-slate-900">知识检索</h2>
            </div>
            <div class="mt-4 flex gap-2">
              <Input
                v-model="retrieveQuery"
                placeholder="例如：极限的定义和求法"
                class="flex-1"
              />
              <button
                type="button"
                class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                :disabled="isSearching"
                @click="retrieveKnowledge"
              >
                {{ isSearching ? '检索中...' : '检索' }}
              </button>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="hit in hits"
                :key="hit.chunk_id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <p class="truncate font-medium text-slate-900">{{ hit.document_title }}</p>
                  <span class="text-xs font-semibold text-[#3A86FF]">{{ hit.score }}</span>
                </div>
                <p class="mt-2 text-xs text-slate-500">
                  chunk #{{ hit.chunk_index }} · {{ hit.tags?.join(' / ') || '无标签' }}
                </p>
                <p class="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-700">
                  {{ hit.content }}
                </p>
              </div>
              <p v-if="!hits.length && !isSearching" class="text-sm text-slate-400">
                检索结果会显示在这里。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">切块预览</h2>
              <span class="text-xs text-slate-400">
                {{ isLoadingChunks ? '加载中...' : `${chunks.length} 段` }}
              </span>
            </div>
            <div class="mt-4 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              <p class="font-medium text-slate-900">
                {{ selectedDocument?.title || '尚未选择文档' }}
              </p>
              <p class="mt-2 text-xs text-slate-500">
                {{ selectedDocument?.content_text?.slice(0, 120) || '点击左侧文档即可查看正文分块情况。' }}
              </p>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="chunk in chunks"
                :key="chunk.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <p class="text-xs font-semibold text-[#3A86FF]">Chunk {{ chunk.chunk_index }}</p>
                <p class="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-700">
                  {{ chunk.content }}
                </p>
              </div>
              <p v-if="!chunks.length && !isLoadingChunks" class="text-sm text-slate-400">
                当前文档还没有切块内容。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped></style>
