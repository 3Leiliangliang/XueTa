<script setup>
import { computed, onMounted, ref } from 'vue'

import IconData from '@/components/icons/IconData.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isLoading = ref(false)
const isSavingRecord = ref(false)
const isSavingReview = ref(false)

const overview = ref(null)
const masteryItems = ref([])
const reviewItems = ref([])

const recordForm = ref({
  subject: '',
  durationMinutes: '45',
  score: '',
  recordType: 'study'
})

const reviewForm = ref({
  knowledgePoint: '',
  subject: '',
  scheduledFor: new Date().toISOString().split('T')[0]
})

const stats = computed(() => overview.value?.stats || null)
const subjectBreakdown = computed(() => overview.value?.subject_breakdown || [])
const recentRecords = computed(() => overview.value?.recent_records || [])
const upcomingReviews = computed(() => overview.value?.upcoming_reviews || [])

const loadProgressData = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再查看学习进度。'
    overview.value = null
    masteryItems.value = []
    reviewItems.value = []
    return
  }

  isLoading.value = true
  authMessage.value = ''
  errorMessage.value = ''

  try {
    const [overviewPayload, masteryPayload, reviewsPayload] = await Promise.all([
      apiRequest('/progress/overview'),
      apiRequest('/progress/mastery?limit=8'),
      apiRequest('/progress/reviews?limit=12')
    ])
    overview.value = overviewPayload
    masteryItems.value = masteryPayload
    reviewItems.value = reviewsPayload
  } catch (error) {
    errorMessage.value = error.message || '加载学习进度失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const createLearningRecord = async () => {
  if (isSavingRecord.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再记录学习数据。'
    return
  }

  isSavingRecord.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    await apiRequest('/progress/records', {
      method: 'POST',
      body: {
        record_type: recordForm.value.recordType,
        subject: recordForm.value.subject.trim() || null,
        duration_minutes: recordForm.value.durationMinutes
          ? Number(recordForm.value.durationMinutes)
          : null,
        score: recordForm.value.score ? Number(recordForm.value.score) : null,
        reference_type: 'manual'
      }
    })
    statusMessage.value = '学习记录已添加。'
    recordForm.value.durationMinutes = '45'
    recordForm.value.score = ''
    await loadProgressData()
  } catch (error) {
    errorMessage.value = error.message || '创建学习记录失败，请稍后重试。'
  } finally {
    isSavingRecord.value = false
  }
}

const createReviewSchedule = async () => {
  if (isSavingReview.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再添加复习提醒。'
    return
  }

  isSavingReview.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    await apiRequest('/progress/reviews', {
      method: 'POST',
      body: {
        knowledge_point: reviewForm.value.knowledgePoint.trim(),
        subject: reviewForm.value.subject.trim() || null,
        scheduled_for: reviewForm.value.scheduledFor,
        status: 'pending',
        review_payload: { source: 'frontend' }
      }
    })
    statusMessage.value = '复习计划已添加。'
    reviewForm.value.knowledgePoint = ''
    reviewForm.value.subject = ''
    reviewForm.value.scheduledFor = new Date().toISOString().split('T')[0]
    await loadProgressData()
  } catch (error) {
    errorMessage.value = error.message || '创建复习计划失败，请稍后重试。'
  } finally {
    isSavingReview.value = false
  }
}

const updateReviewStatus = async (reviewId, status) => {
  try {
    await apiRequest(`/progress/reviews/${reviewId}`, {
      method: 'PATCH',
      body: { status }
    })
    statusMessage.value = '复习状态已更新。'
    await loadProgressData()
  } catch (error) {
    errorMessage.value = error.message || '更新复习状态失败，请稍后重试。'
  }
}

const formatDate = (value) => {
  if (!value) return '未设置'
  return new Date(value).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadProgressData()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main class="container mx-auto space-y-8 px-4 py-8 md:px-10 md:py-10 lg:px-16 lg:py-12">
      <section class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-md">
            <IconData class="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-2xl font-bold text-transparent md:text-3xl lg:text-4xl">
              学习进度中心
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              查看学习概览、掌握度和复习安排，也可以手动补录学习数据。
            </p>
          </div>
        </div>
        <button
          type="button"
          class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
          :disabled="isLoading"
          @click="loadProgressData"
        >
          {{ isLoading ? '刷新中...' : '刷新数据' }}
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
          <p class="text-sm text-slate-500">学习记录</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats?.total_learning_records ?? 0 }}</p>
          <p class="mt-1 text-xs text-slate-500">已记录的学习活动总数</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">累计学习时长</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats?.total_study_minutes ?? 0 }} min</p>
          <p class="mt-1 text-xs text-slate-500">来自学习记录与练习记录</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">平均掌握度</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ Math.round(stats?.average_mastery_score ?? 0) }}</p>
          <p class="mt-1 text-xs text-slate-500">0 - 100 的知识掌握评分</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-slate-500">待复习任务</p>
          <p class="mt-2 text-3xl font-bold text-slate-900">{{ stats?.due_review_count ?? 0 }}</p>
          <p class="mt-1 text-xs text-slate-500">今日到期的复习事项</p>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">学科分布</h2>
              <span class="text-xs text-slate-400">按学习记录聚合</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="item in subjectBreakdown"
                :key="item.subject"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="font-medium text-slate-900">{{ item.subject }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ item.record_count }} 条记录 · {{ item.total_minutes }} 分钟
                    </p>
                  </div>
                  <span class="text-sm font-semibold text-[#3A86FF]">
                    {{ item.average_score == null ? '--' : Math.round(item.average_score) }}
                  </span>
                </div>
              </div>
              <p v-if="!subjectBreakdown.length && !isLoading" class="text-sm text-slate-400">
                还没有足够的学习记录，先添加一条试试。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">快速添加学习记录</h2>
            <div class="mt-4 space-y-4">
              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">学习类型</label>
                  <select
                    v-model="recordForm.recordType"
                    class="h-10 w-full rounded-md border border-slate-200 px-3 text-sm"
                  >
                    <option value="study">学习</option>
                    <option value="practice">练习</option>
                    <option value="review">复习</option>
                    <option value="chat">答疑</option>
                    <option value="note">笔记</option>
                  </select>
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">学科</label>
                  <Input v-model="recordForm.subject" placeholder="例如：数学 / 英语" />
                </div>
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">时长（分钟）</label>
                  <Input v-model="recordForm.durationMinutes" type="number" placeholder="45" />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">得分（可选）</label>
                  <Input v-model="recordForm.score" type="number" placeholder="例如：92" />
                </div>
              </div>
              <div class="flex justify-end">
                <button
                  type="button"
                  class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                  :disabled="isSavingRecord"
                  @click="createLearningRecord"
                >
                  {{ isSavingRecord ? '提交中...' : '添加记录' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">知识掌握度</h2>
              <span class="text-xs text-slate-400">按分数从低到高排序</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="item in masteryItems"
                :key="item.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <p class="truncate font-medium text-slate-900">{{ item.knowledge_point }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ item.subject || '未分类' }} · 下次复习 {{ formatDate(item.next_review_at) }}
                    </p>
                  </div>
                  <span class="text-sm font-semibold text-[#3A86FF]">
                    {{ Math.round(item.mastery_score) }}
                  </span>
                </div>
                <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    class="h-full rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7]"
                    :style="{ width: `${Math.min(100, Math.max(0, item.mastery_score))}%` }"
                  ></div>
                </div>
              </div>
              <p v-if="!masteryItems.length && !isLoading" class="text-sm text-slate-400">
                当前还没有掌握度数据，完成一次练习后这里会逐步丰富。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">添加复习提醒</h2>
            <div class="mt-4 space-y-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">知识点</label>
                <Input v-model="reviewForm.knowledgePoint" placeholder="例如：函数极限 / 牛顿第二定律" />
              </div>
              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">学科</label>
                  <Input v-model="reviewForm.subject" placeholder="例如：数学" />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-slate-700">复习日期</label>
                  <Input v-model="reviewForm.scheduledFor" type="date" />
                </div>
              </div>
              <div class="flex justify-end">
                <button
                  type="button"
                  class="rounded-lg border border-slate-200 bg-white px-5 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-60"
                  :disabled="isSavingReview"
                  @click="createReviewSchedule"
                >
                  {{ isSavingReview ? '添加中...' : '添加提醒' }}
                </button>
              </div>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">最近学习记录</h2>
              <span class="text-xs text-slate-400">来自后端概览接口</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="record in recentRecords"
                :key="record.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <div>
                    <p class="font-medium text-slate-900">{{ record.subject || '未分类学科' }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ record.record_type }} · {{ record.duration_minutes || 0 }} 分钟 · {{ formatDate(record.created_at) }}
                    </p>
                  </div>
                  <span class="text-sm font-semibold text-slate-700">
                    {{ record.score == null ? '--' : Math.round(record.score) }}
                  </span>
                </div>
              </div>
              <p v-if="!recentRecords.length && !isLoading" class="text-sm text-slate-400">
                还没有学习记录。
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-slate-900">复习计划</h2>
              <span class="text-xs text-slate-400">可直接更新状态</span>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="review in reviewItems.length ? reviewItems : upcomingReviews"
                :key="review.id"
                class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p class="font-medium text-slate-900">{{ review.knowledge_point }}</p>
                    <p class="mt-1 text-xs text-slate-500">
                      {{ review.subject || '未分类' }} · {{ formatDate(review.scheduled_for) }} · {{ review.status }}
                    </p>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-700"
                      @click="updateReviewStatus(review.id, 'completed')"
                    >
                      完成
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700"
                      @click="updateReviewStatus(review.id, 'pending')"
                    >
                      设为待办
                    </button>
                    <button
                      type="button"
                      class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-700"
                      @click="updateReviewStatus(review.id, 'skipped')"
                    >
                      跳过
                    </button>
                  </div>
                </div>
              </div>
              <p v-if="!(reviewItems.length || upcomingReviews.length) && !isLoading" class="text-sm text-slate-400">
                当前还没有复习计划。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped></style>
