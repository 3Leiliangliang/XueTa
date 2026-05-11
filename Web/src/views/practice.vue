<script setup>
import { computed, onMounted, ref } from 'vue'

import IconStar from '@/components/icons/IconStar.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isLoading = ref(false)
const isGenerating = ref(false)
const isSubmitting = ref(false)

const practiceSets = ref([])
const activeSetId = ref('')
const currentSet = ref(null)
const attempts = ref([])
const wrongQuestions = ref([])
const answerDrafts = ref({})
const attemptResult = ref(null)

const generateForm = ref({
  title: '',
  subject: '',
  knowledgePointsText: '',
  itemCount: '5',
  difficulty: 'medium'
})

const selectedItemTypes = ref(['single', 'fill', 'short', 'multiple'])
const durationMinutes = ref('25')

const stats = computed(() => ({
  setCount: practiceSets.value.length,
  currentItemCount: currentSet.value?.items?.length || 0,
  wrongCount: wrongQuestions.value.length,
  latestScore:
    attemptResult.value?.score ??
    attempts.value[0]?.score ??
    null
}))

const itemResultMap = computed(() => {
  const pairs = attemptResult.value?.answers || []
  return Object.fromEntries(pairs.map((item) => [item.item_id, item]))
})

const initializeAnswerDrafts = (items) => {
  const nextDrafts = {}
  for (const item of items) {
    nextDrafts[item.id] = item.type === 'multiple' ? [] : ''
  }
  answerDrafts.value = nextDrafts
}

const loadWrongQuestions = async () => {
  wrongQuestions.value = await apiRequest('/practice/wrong-questions')
}

const loadSetDetail = async (setId) => {
  if (!setId) {
    activeSetId.value = ''
    currentSet.value = null
    attempts.value = []
    answerDrafts.value = {}
    attemptResult.value = null
    return
  }

  const [setPayload, attemptPayload] = await Promise.all([
    apiRequest(`/practice/sets/${setId}`),
    apiRequest(`/practice/sets/${setId}/attempts`)
  ])
  activeSetId.value = setId
  currentSet.value = setPayload
  attempts.value = attemptPayload
  initializeAnswerDrafts(setPayload.items || [])
  attemptResult.value = null
}

const loadPracticeData = async ({ preserveSelection = false } = {}) => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用练习中心。'
    practiceSets.value = []
    currentSet.value = null
    attempts.value = []
    wrongQuestions.value = []
    answerDrafts.value = {}
    attemptResult.value = null
    return
  }

  isLoading.value = true
  authMessage.value = ''
  errorMessage.value = ''

  try {
    const [setList] = await Promise.all([
      apiRequest('/practice/sets'),
      loadWrongQuestions()
    ])
    practiceSets.value = setList

    if (!setList.length) {
      currentSet.value = null
      attempts.value = []
      answerDrafts.value = {}
      attemptResult.value = null
      return
    }

    const targetSetId =
      preserveSelection && setList.some((item) => item.id === activeSetId.value)
        ? activeSetId.value
        : setList[0].id
    await loadSetDetail(targetSetId)
  } catch (error) {
    errorMessage.value = error.message || '加载练习数据失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const toggleItemType = (type) => {
  if (selectedItemTypes.value.includes(type)) {
    if (selectedItemTypes.value.length === 1) return
    selectedItemTypes.value = selectedItemTypes.value.filter((item) => item !== type)
    return
  }

  selectedItemTypes.value = [...selectedItemTypes.value, type]
}

const generatePractice = async () => {
  if (isGenerating.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再生成练习。'
    return
  }

  isGenerating.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const knowledgePoints = generateForm.value.knowledgePointsText
      .split(/[，,\n]/)
      .map((item) => item.trim())
      .filter(Boolean)

    const setPayload = await apiRequest('/practice/generate', {
      method: 'POST',
      body: {
        title: generateForm.value.title.trim() || null,
        subject: generateForm.value.subject.trim() || null,
        knowledge_points: knowledgePoints,
        item_count: Number(generateForm.value.itemCount) || 5,
        difficulty: generateForm.value.difficulty,
        item_types: selectedItemTypes.value
      }
    })

    statusMessage.value = `练习集“${setPayload.title}”已生成。`
    await loadPracticeData()
    await loadSetDetail(setPayload.id)
  } catch (error) {
    errorMessage.value = error.message || '生成练习失败，请稍后重试。'
  } finally {
    isGenerating.value = false
  }
}

const toggleMultipleOption = (itemId, option) => {
  const current = Array.isArray(answerDrafts.value[itemId]) ? answerDrafts.value[itemId] : []
  if (current.includes(option)) {
    answerDrafts.value[itemId] = current.filter((item) => item !== option)
    return
  }
  answerDrafts.value[itemId] = [...current, option]
}

const submitAttempt = async () => {
  if (isSubmitting.value || !currentSet.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再提交练习。'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest(`/practice/sets/${currentSet.value.id}/attempts`, {
      method: 'POST',
      body: {
        answers: currentSet.value.items.map((item) => ({
          item_id: item.id,
          answer_json: answerDrafts.value[item.id]
        })),
        duration_minutes: durationMinutes.value ? Number(durationMinutes.value) : null
      }
    })

    attemptResult.value = payload
    statusMessage.value = `提交成功，本次得分 ${Math.round(payload.score || 0)} 分。`
    await Promise.all([
      loadWrongQuestions(),
      loadSetDetail(currentSet.value.id)
    ])
    answerDrafts.value = Object.fromEntries(
      payload.answers.map((item) => [item.item_id, item.answer_json])
    )
    attemptResult.value = payload
  } catch (error) {
    errorMessage.value = error.message || '提交练习失败，请稍后重试。'
  } finally {
    isSubmitting.value = false
  }
}

const formatDate = (value) => {
  if (!value) return '未知时间'
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(() => {
  loadPracticeData()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main class="container mx-auto space-y-8 px-4 py-8 md:px-10 md:py-10 lg:px-16 lg:py-12">
      <section class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-md">
            <IconStar class="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-2xl font-bold text-transparent md:text-3xl lg:text-4xl">
              练习中心
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              生成练习、完成作答、查看评分结果和错题沉淀。
            </p>
          </div>
        </div>
        <button
          type="button"
          class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          :disabled="isLoading"
          @click="loadPracticeData({ preserveSelection: true })"
        >
          {{ isLoading ? '刷新中...' : '刷新练习' }}
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

      <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">练习集数量</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.setCount }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">当前题量</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.currentItemCount }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">错题数量</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats.wrongCount }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">最近得分</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">
            {{ stats.latestScore == null ? '--' : Math.round(stats.latestScore) }}
          </p>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">生成练习</h2>
            <div class="mt-4 space-y-4">
              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">练习标题</label>
                  <Input v-model="generateForm.title" placeholder="例如：函数极限专项" />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">学科</label>
                  <Input v-model="generateForm.subject" placeholder="例如：数学" />
                </div>
              </div>

              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">题目数量</label>
                  <Input v-model="generateForm.itemCount" type="number" placeholder="5" />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">难度</label>
                  <select
                    v-model="generateForm.difficulty"
                    class="h-10 w-full rounded-md border border-slate-200 px-3 text-sm"
                  >
                    <option value="easy">easy</option>
                    <option value="medium">medium</option>
                    <option value="hard">hard</option>
                  </select>
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">知识点</label>
                <textarea
                  v-model="generateForm.knowledgePointsText"
                  class="min-h-[120px] w-full rounded-md border border-slate-200 px-3 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:ring-offset-2"
                  placeholder="例如：函数极限，连续性，导数定义。支持逗号或换行分隔。"
                ></textarea>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">题型</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="type in ['single', 'multiple', 'fill', 'short', 'code']"
                    :key="type"
                    type="button"
                    :class="[
                      'rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
                      selectedItemTypes.includes(type)
                        ? 'bg-[#3A86FF] text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    ]"
                    @click="toggleItemType(type)"
                  >
                    {{ type }}
                  </button>
                </div>
              </div>

              <div class="flex justify-end">
                <button
                  type="button"
                  class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                  :disabled="isGenerating"
                  @click="generatePractice"
                >
                  {{ isGenerating ? '生成中...' : '生成练习集' }}
                </button>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">练习集列表</h2>
              <span class="text-xs text-slate-400">{{ practiceSets.length }} 组</span>
            </div>
            <div class="mt-4 space-y-3">
              <button
                v-for="item in practiceSets"
                :key="item.id"
                type="button"
                :class="[
                  'w-full rounded-2xl border px-4 py-3 text-left transition-colors',
                  activeSetId === item.id
                    ? 'border-[#3A86FF] bg-blue-50'
                    : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                ]"
                @click="loadSetDetail(item.id)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <p class="truncate font-medium text-slate-900">{{ item.title }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ item.subject || '未分类' }} · {{ item.item_count }} 题
                    </p>
                  </div>
                  <span class="text-xs text-slate-400">{{ item.source }}</span>
                </div>
              </button>
              <p v-if="!practiceSets.length && !isLoading" class="text-sm text-slate-400">
                当前还没有练习集，先生成一组试试。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">错题沉淀</h2>
              <span class="text-xs text-slate-400">自动汇总</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="wrong in wrongQuestions"
                :key="wrong.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <p class="line-clamp-2 flex-1 font-medium text-slate-900">{{ wrong.stem }}</p>
                  <span class="rounded-full bg-rose-50 px-3 py-1 text-xs text-rose-600">
                    {{ wrong.wrong_count }} 次
                  </span>
                </div>
                <p class="mt-2 text-xs text-slate-500">
                  {{ wrong.knowledge_points_json?.join(' / ') || '未提取知识点' }}
                </p>
                <p class="mt-2 text-sm text-slate-600">
                  {{ wrong.last_feedback || '暂无反馈' }}
                </p>
              </div>
              <p v-if="!wrongQuestions.length && !isLoading" class="text-sm text-slate-400">
                当前还没有错题记录。
              </p>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 class="text-lg font-semibold text-slate-900">
                  {{ currentSet?.title || '当前练习' }}
                </h2>
                <p class="mt-1 text-sm text-slate-500">
                  {{ currentSet?.subject || '请先选择或生成练习集' }}
                </p>
              </div>
              <div class="flex items-center gap-3">
                <Input
                  v-model="durationMinutes"
                  type="number"
                  placeholder="25"
                  class="w-24"
                />
                <button
                  type="button"
                  class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                  :disabled="isSubmitting || !currentSet"
                  @click="submitAttempt"
                >
                  {{ isSubmitting ? '提交中...' : '提交作答' }}
                </button>
              </div>
            </div>

            <div v-if="currentSet" class="mt-6 space-y-4">
              <div
                v-for="(item, index) in currentSet.items"
                :key="item.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4"
              >
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-xs font-semibold text-[#3A86FF]">
                      第 {{ index + 1 }} 题 · {{ item.type }} · {{ item.difficulty }}
                    </p>
                    <p class="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-800">
                      {{ item.stem }}
                    </p>
                  </div>
                  <span class="rounded-full bg-white px-3 py-1 text-xs text-slate-500">
                    {{ item.knowledge_points_json?.join(' / ') || '未标注知识点' }}
                  </span>
                </div>

                <div v-if="item.type === 'single'" class="mt-4 space-y-2">
                  <label
                    v-for="option in item.options_json || []"
                    :key="option"
                    class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                  >
                    <input
                      v-model="answerDrafts[item.id]"
                      :name="item.id"
                      :value="option"
                      type="radio"
                    />
                    <span>{{ option }}</span>
                  </label>
                </div>

                <div v-else-if="item.type === 'multiple'" class="mt-4 space-y-2">
                  <label
                    v-for="option in item.options_json || []"
                    :key="option"
                    class="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
                  >
                    <input
                      :checked="Array.isArray(answerDrafts[item.id]) && answerDrafts[item.id].includes(option)"
                      type="checkbox"
                      @change="toggleMultipleOption(item.id, option)"
                    />
                    <span>{{ option }}</span>
                  </label>
                </div>

                <div v-else class="mt-4">
                  <textarea
                    v-model="answerDrafts[item.id]"
                    class="min-h-[110px] w-full rounded-md border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:ring-offset-2"
                    :placeholder="item.type === 'code' ? '输入代码思路或伪代码...' : '输入你的答案...'"
                  ></textarea>
                </div>

                <div
                  v-if="itemResultMap[item.id]"
                  :class="[
                    'mt-4 rounded-2xl border px-4 py-3 text-sm',
                    itemResultMap[item.id].is_correct
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-rose-200 bg-rose-50 text-rose-700'
                  ]"
                >
                  <p class="font-medium">
                    {{ itemResultMap[item.id].is_correct ? '回答正确' : '回答有误' }}
                  </p>
                  <p class="mt-2 whitespace-pre-line leading-relaxed">
                    {{ itemResultMap[item.id].feedback_text }}
                  </p>
                </div>
              </div>
            </div>

            <div v-else class="mt-6 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-400">
              先在左侧生成一组练习，或从已有练习集中选择一组开始作答。
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">最近提交记录</h2>
              <span class="text-xs text-slate-400">{{ attempts.length }} 次</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="attempt in attempts"
                :key="attempt.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="font-medium text-slate-900">
                      {{ attempt.status }} · {{ Math.round(attempt.score || 0) }} 分
                    </p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ formatDate(attempt.created_at) }}
                    </p>
                  </div>
                  <span class="text-xs text-slate-400">
                    {{ attempt.evaluation_json?.correct_count || 0 }}/{{ attempt.evaluation_json?.total_items || 0 }}
                  </span>
                </div>
              </div>
              <p v-if="!attempts.length && !isLoading" class="text-sm text-slate-400">
                当前练习集还没有提交记录。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped></style>
