<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import Logo from './logo.vue'
import { apiRequest } from '@/lib/api'
import {
  AUTH_SESSION_EVENT,
  clearAuthSession,
  getRefreshToken,
  getStoredUser,
  hasAccessToken
} from '@/lib/auth'

const route = useRoute()
const router = useRouter()

const navItems = [
  { id: 1, to: '/', name: '首页' },
  { id: 2, to: '/translate', name: '翻译' },
  { id: 3, to: '/qa', name: '答疑' },
  { id: 4, to: '/note', name: '笔记' },
  { id: 5, to: '/kb', name: '知识库' },
  { id: 6, to: '/practice', name: '练习' },
  { id: 7, to: '/progress', name: '进度' },
  { id: 8, to: '/desktop', name: '桌面' },
  { id: 9, to: '/planning', name: '规划' }
]

const currentUser = ref(null)
const isLoggingOut = ref(false)

const refreshAuthState = () => {
  currentUser.value = getStoredUser()
}

const displayName = computed(() =>
  currentUser.value?.profile?.display_name || currentUser.value?.username || '个人中心'
)

const userInitial = computed(() => {
  const source = displayName.value.trim()
  if (!source) return '我'
  return source.slice(0, 1).toUpperCase()
})

const isActive = (targetPath) => {
  if (targetPath === '/') return route.path === '/'
  return route.path.startsWith(targetPath)
}

const handleLogout = async () => {
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
    isLoggingOut.value = false
    router.push('/auth/login')
  }
}

onMounted(() => {
  refreshAuthState()
  window.addEventListener(AUTH_SESSION_EVENT, refreshAuthState)
  window.addEventListener('storage', refreshAuthState)
})

onUnmounted(() => {
  window.removeEventListener(AUTH_SESSION_EVENT, refreshAuthState)
  window.removeEventListener('storage', refreshAuthState)
})
</script>

<template>
  <header class="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/78 px-4 backdrop-blur-sm md:px-8 xl:px-12">
    <div class="container flex h-16 items-center justify-between gap-4">
      <div class="flex min-w-0 items-center gap-2">
        <router-link to="/">
          <Logo />
        </router-link>
        <span class="hidden text-sm text-slate-500 lg:inline-block">
          AI驱动，高效学习
        </span>
      </div>

      <nav class="hidden items-center gap-4 text-sm font-medium text-slate-600 lg:flex xl:gap-5">
        <router-link
          v-for="item in navItems"
          :key="item.id"
          :to="item.to"
          :class="[
            'transition-colors hover:text-[#3A86FF]',
            isActive(item.to) ? 'text-[#3A86FF]' : 'text-slate-600'
          ]"
        >
          {{ item.name }}
        </router-link>
      </nav>

      <div class="flex items-center gap-2 md:gap-3">
        <template v-if="currentUser">
          <router-link
            to="/profile"
            class="hidden items-center gap-3 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF] md:flex"
          >
            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-xs font-semibold text-white">
              {{ userInitial }}
            </span>
            <span class="max-w-[112px] truncate">{{ displayName }}</span>
          </router-link>
          <router-link
            to="/profile"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF] md:hidden"
          >
            我的
          </router-link>
          <button
            type="button"
            class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-3 py-1.5 text-sm text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isLoggingOut"
            @click="handleLogout"
          >
            {{ isLoggingOut ? '退出中...' : '退出' }}
          </button>
        </template>
        <template v-else>
          <router-link
            to="/auth/login"
            class="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 transition-colors hover:border-[#3A86FF] hover:text-[#3A86FF]"
          >
            登录
          </router-link>
          <router-link
            to="/auth/register"
            class="rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-3 py-1.5 text-sm text-white transition-opacity hover:opacity-90"
          >
            注册
          </router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped></style>
