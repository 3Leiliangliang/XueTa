<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Logo from '@/components/main/logo.vue'
import Input from '@/components/ui/input.vue'
import Label from '@/components/ui/label.vue'
import Icons from '@/components/ui/icons.vue'
import { apiRequest } from '@/lib/api'

const router = useRouter()
const route = useRoute()

const email = ref('')
const issuedResetToken = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')

const routeToken = computed(() =>
  typeof route.query.token === 'string' ? route.query.token.trim() : ''
)

const resolvedToken = computed(() => routeToken.value || issuedResetToken.value.trim())
const isResetMode = computed(() => Boolean(resolvedToken.value))

const handleRequestReset = async () => {
  if (isLoading.value) return

  isLoading.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/auth/password/forgot', {
      method: 'POST',
      auth: false,
      body: {
        email: email.value.trim()
      }
    })

    statusMessage.value = payload.message || '重置请求已提交，请查收邮箱。'
    if (payload.reset_token) {
      issuedResetToken.value = payload.reset_token
      statusMessage.value = `开发环境重置令牌：${payload.reset_token}`
    }
  } catch (error) {
    errorMessage.value = error.message || '发送重置请求失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const handleResetPassword = async () => {
  if (isLoading.value) return

  isLoading.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/auth/password/reset', {
      method: 'POST',
      auth: false,
      body: {
        token: resolvedToken.value,
        password: password.value,
        confirm_password: confirmPassword.value
      }
    })

    statusMessage.value = payload.message || '密码已重置，正在返回登录页...'
    window.setTimeout(() => {
      router.push('/auth/login')
    }, 900)
  } catch (error) {
    errorMessage.value = error.message || '重置密码失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const resetToRequestMode = () => {
  issuedResetToken.value = ''
  password.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
  statusMessage.value = ''
  if (routeToken.value) {
    router.replace({ path: '/auth/resetPassword' })
  }
}

const goBackLogin = () => {
  router.push('/auth/login')
}
</script>

<template>
  <div class="min-h-screen bg-white flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="w-full max-w-md">
      <div class="flex flex-col items-center justify-center text-center">
        <Logo />
        <h2 class="mt-6 text-3xl font-bold text-slate-900">
          {{ isResetMode ? '设置新密码' : '重置密码' }}
        </h2>
        <p class="mt-2 text-sm text-slate-600">
          {{
            isResetMode
              ? '请输入新的密码，完成后将返回登录页。'
              : '我们将向您的邮箱发送重置密码的链接。'
          }}
        </p>
      </div>

      <div v-if="errorMessage || statusMessage" class="mt-6 space-y-3">
        <p
          v-if="errorMessage"
          class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
        >
          {{ errorMessage }}
        </p>
        <p
          v-if="statusMessage"
          class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 break-all"
        >
          {{ statusMessage }}
        </p>
      </div>

      <form
        v-if="!isResetMode"
        @submit.prevent="handleRequestReset"
        class="mt-10 space-y-6"
      >
        <div class="space-y-2">
          <Label htmlFor="email">邮箱</Label>
          <div class="relative">
            <Icons name="mail" class="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <Input
              id="email"
              v-model="email"
              placeholder="请输入邮箱"
              type="email"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect="off"
              :disabled="isLoading"
              class="pl-9"
            />
          </div>
        </div>

        <button
          type="submit"
          class="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3A86FF_0%,#5f6dff_55%,#7C4DFF_100%)] text-base font-medium text-white shadow-[0_18px_36px_-18px_rgba(95,109,255,0.75)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_42px_-16px_rgba(95,109,255,0.85)] disabled:cursor-not-allowed disabled:opacity-70"
          :disabled="isLoading"
        >
          {{ isLoading ? '发送中...' : '发送重置链接' }}
        </button>
      </form>

      <form
        v-else
        @submit.prevent="handleResetPassword"
        class="mt-10 space-y-6"
      >
        <div class="space-y-2">
          <Label htmlFor="password">新密码</Label>
          <div class="relative">
            <Icons name="lock" class="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <Input
              id="password"
              v-model="password"
              placeholder="请输入新密码"
              type="password"
              autoCapitalize="none"
              autoComplete="new-password"
              autoCorrect="off"
              :disabled="isLoading"
              class="pl-9"
            />
          </div>
        </div>

        <div class="space-y-2">
          <Label htmlFor="confirm-password">确认密码</Label>
          <div class="relative">
            <Icons name="lock" class="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <Input
              id="confirm-password"
              v-model="confirmPassword"
              placeholder="请再次输入新密码"
              type="password"
              autoCapitalize="none"
              autoComplete="new-password"
              autoCorrect="off"
              :disabled="isLoading"
              class="pl-9"
            />
          </div>
        </div>

        <button
          type="submit"
          class="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3A86FF_0%,#5f6dff_55%,#7C4DFF_100%)] text-base font-medium text-white shadow-[0_18px_36px_-18px_rgba(95,109,255,0.75)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_42px_-16px_rgba(95,109,255,0.85)] disabled:cursor-not-allowed disabled:opacity-70"
          :disabled="isLoading"
        >
          {{ isLoading ? '提交中...' : '确认重置密码' }}
        </button>

        <button
          type="button"
          @click="resetToRequestMode"
          class="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-[#d8e1ff] bg-white/88 text-sm font-medium text-slate-700 transition-colors hover:bg-white"
        >
          重新申请重置链接
        </button>
      </form>

      <div class="mt-8 flex items-center justify-center text-sm text-slate-600">
        <button
          type="button"
          @click="goBackLogin"
          class="inline-flex items-center text-sm text-[#000000] hover:text-[#3A86FF]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-left-icon lucide-arrow-left">
            <path d="m12 19-7-7 7-7"/>
            <path d="M19 12H5"/>
          </svg>
          返回登录
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
