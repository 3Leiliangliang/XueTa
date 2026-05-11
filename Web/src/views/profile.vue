<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import IconAssistant from '@/components/icons/IconAssistant.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest } from '@/lib/api'
import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  hasAccessToken,
  saveAuthSession
} from '@/lib/auth'

const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isLoading = ref(false)
const isSaving = ref(false)
const isLoggingOut = ref(false)
const currentUser = ref(null)
const router = useRouter()

const form = ref({
  displayName: '',
  avatarUrl: '',
  gradeLevel: '',
  targetExam: '',
  preferredSubjects: '',
  learningStyle: '',
  bio: ''
})

const applyUser = (user) => {
  currentUser.value = user
  form.value = {
    displayName: user?.profile?.display_name || '',
    avatarUrl: user?.profile?.avatar_url || '',
    gradeLevel: user?.profile?.grade_level || '',
    targetExam: user?.profile?.target_exam || '',
    preferredSubjects: user?.profile?.preferred_subjects || '',
    learningStyle: user?.profile?.learning_style || '',
    bio: user?.profile?.bio || ''
  }
}

const loadProfile = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再查看个人中心。'
    currentUser.value = null
    return
  }

  isLoading.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const user = await apiRequest('/users/me')
    applyUser(user)
  } catch (error) {
    errorMessage.value = error.message || '加载个人信息失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const buildProfilePayload = () => {
  const currentProfile = currentUser.value?.profile || {}
  const nextValues = {
    display_name: form.value.displayName.trim(),
    avatar_url: form.value.avatarUrl.trim(),
    grade_level: form.value.gradeLevel.trim(),
    target_exam: form.value.targetExam.trim(),
    preferred_subjects: form.value.preferredSubjects.trim(),
    learning_style: form.value.learningStyle.trim(),
    bio: form.value.bio.trim()
  }

  return Object.fromEntries(
    Object.entries(nextValues).filter(([key, value]) => {
      const currentValue = (currentProfile[key] || '').trim()
      return value !== currentValue
    })
  )
}

const saveProfile = async () => {
  if (isSaving.value) return
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再保存个人资料。'
    return
  }

  const payload = buildProfilePayload()
  if (!Object.keys(payload).length) {
    statusMessage.value = '当前没有需要保存的修改。'
    errorMessage.value = ''
    return
  }

  isSaving.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const user = await apiRequest('/users/me', {
      method: 'PATCH',
      body: payload
    })
    applyUser(user)
    saveAuthSession({
      accessToken: getAccessToken(),
      refreshToken: getRefreshToken(),
      user
    })
    statusMessage.value = '个人资料已更新。'
  } catch (error) {
    errorMessage.value = error.message || '保存个人资料失败，请稍后重试。'
  } finally {
    isSaving.value = false
  }
}

const logout = async () => {
  if (isLoggingOut.value) return

  isLoggingOut.value = true
  try {
    const refreshToken = getRefreshToken()
    if (hasAccessToken() && refreshToken) {
      await apiRequest('/auth/logout', {
        method: 'POST',
        body: { refresh_token: refreshToken }
      })
    }
  } catch {
  } finally {
    clearAuthSession()
    currentUser.value = null
    authMessage.value = '你已退出登录。'
    isLoggingOut.value = false
    router.push('/auth/login')
  }
}

onMounted(() => {
  applyUser(getStoredUser())
  loadProfile()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main class="container mx-auto space-y-8 px-4 py-8 md:px-10 md:py-10 lg:px-16 lg:py-12">
      <section class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] shadow-md">
            <IconAssistant class="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-2xl font-bold text-transparent md:text-3xl lg:text-4xl">
              个人中心
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              管理账号信息、学习画像和目标设定。
            </p>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
            :disabled="isSaving"
            @click="saveProfile"
          >
            {{ isSaving ? '保存中...' : '保存资料' }}
          </button>
          <button
            type="button"
            class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            :disabled="isLoggingOut"
            @click="logout"
          >
            {{ isLoggingOut ? '退出中...' : '退出登录' }}
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

      <section class="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div class="space-y-6">
          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center gap-4">
              <div class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-2xl font-semibold text-white">
                {{ (currentUser?.username || '我').slice(0, 1).toUpperCase() }}
              </div>
              <div class="min-w-0 flex-1">
                <h2 class="truncate text-xl font-semibold text-slate-900">
                  {{ currentUser?.profile?.display_name || currentUser?.username || '未登录用户' }}
                </h2>
                <p class="mt-1 truncate text-sm text-slate-500">
                  {{ currentUser?.email || currentUser?.phone || '暂无联系方式' }}
                </p>
                <div class="mt-3 flex flex-wrap gap-2 text-xs">
                  <span class="rounded-full bg-slate-100 px-3 py-1 text-slate-600">
                    用户名：{{ currentUser?.username || '--' }}
                  </span>
                  <span class="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700">
                    状态：{{ currentUser?.status || '--' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="text-sm text-slate-500">邮箱验证</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">
                {{ currentUser?.email_verified ? '已验证' : '未验证' }}
              </p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p class="text-sm text-slate-500">手机验证</p>
              <p class="mt-2 text-lg font-semibold text-slate-900">
                {{ currentUser?.phone_verified ? '已验证' : '未验证' }}
              </p>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 class="text-lg font-semibold text-slate-900">账号信息</h3>
            <div class="mt-4 space-y-3 text-sm text-slate-600">
              <div class="flex items-center justify-between gap-4">
                <span>邮箱</span>
                <span class="truncate text-slate-900">{{ currentUser?.email || '--' }}</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span>手机号</span>
                <span class="truncate text-slate-900">{{ currentUser?.phone || '--' }}</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span>账号 ID</span>
                <span class="truncate text-slate-900">{{ currentUser?.id || '--' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-slate-900">学习画像</h3>
          <p class="mt-1 text-sm text-slate-500">
            这些信息会帮助后续的学习规划、练习推荐和内容生成。
          </p>

          <div v-if="isLoading" class="mt-6 rounded-2xl bg-slate-50 px-4 py-6 text-sm text-slate-500">
            正在加载个人资料...
          </div>

          <div v-else class="mt-6 space-y-5">
            <div class="grid gap-5 md:grid-cols-2">
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">显示名称</label>
                <Input v-model="form.displayName" placeholder="例如：小塔同学" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">头像链接</label>
                <Input v-model="form.avatarUrl" placeholder="https://..." />
              </div>
            </div>

            <div class="grid gap-5 md:grid-cols-2">
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">当前年级</label>
                <Input v-model="form.gradeLevel" placeholder="例如：高三 / 大二" />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-slate-700">目标考试</label>
                <Input v-model="form.targetExam" placeholder="例如：考研数学 / CET-6" />
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700">偏好学科</label>
              <Input v-model="form.preferredSubjects" placeholder="例如：数学、英语、计算机基础" />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700">学习风格</label>
              <Input v-model="form.learningStyle" placeholder="例如：喜欢题海训练、偏好结构化笔记" />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-700">个人简介</label>
              <textarea
                v-model="form.bio"
                class="min-h-[160px] w-full rounded-md border border-slate-200 bg-white px-3 py-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#3A86FF] focus:ring-offset-2"
                placeholder="补充你的学习目标、时间安排或当前困惑，方便后续 AI 更贴合你的学习状态。"
              ></textarea>
            </div>

            <div class="flex justify-end">
              <button
                type="button"
                class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-5 py-2 text-sm text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                :disabled="isSaving"
                @click="saveProfile"
              >
                {{ isSaving ? '保存中...' : '保存学习画像' }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped></style>
