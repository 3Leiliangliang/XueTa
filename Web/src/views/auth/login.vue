<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import LoginMascotScene from '@/components/auth/LoginMascotScene.vue'
import Logo from '@/components/main/logo.vue'
import Tabs from '@/components/ui/tabs.vue'
import TabsContent from '@/components/ui/tabs-content.vue'
import TabsList from '@/components/ui/tabs-list.vue'
import TabsTrigger from '@/components/ui/tabs-trigger.vue'
import Input from '@/components/ui/input.vue'
import Label from '@/components/ui/label.vue'
import Checkbox from '@/components/ui/checkbox.vue'
import Icons from '@/components/ui/icons.vue'
import { useAuthMascot } from '@/useAuthMascot'
import { apiRequest } from '@/lib/api'
import { saveAuthSession } from '@/lib/auth'

const router = useRouter()
const authMode = ref('password')
const email = ref('')
const password = ref('')
const phone = ref('')
const code = ref('')
const remember = ref(true)
const isLoading = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')

const submitText = computed(() => {
  if (isLoading.value) {
    return '登录中...'
  }

  return authMode.value === 'password' ? '登录' : '验证码登录'
})

const {
  hasPasswordValue,
  isPasswordVisible,
  isTypingActive,
  passwordVisible,
  setTypingFocus,
  togglePasswordVisibility,
  typingPulse
} = useAuthMascot({
  enabled: computed(() => authMode.value === 'password'),
  passwordRefs: [password],
  fieldNames: ['password'],
  typingFieldNames: ['email']
})

const handlePasswordSubmit = async () => {
  if (isLoading.value) return

  isLoading.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/auth/login/password', {
      method: 'POST',
      auth: false,
      body: {
        identifier: email.value.trim(),
        password: password.value
      }
    })

    saveAuthSession({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      user: payload.user
    })
    statusMessage.value = '登录成功，正在进入学习桌面...'
    router.push('/desktop')
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const handleCodeSubmit = async () => {
  if (isLoading.value) return

  isLoading.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/auth/login/code', {
      method: 'POST',
      auth: false,
      body: {
        target: phone.value.trim(),
        code: code.value.trim(),
        channel: 'sms'
      }
    })

    saveAuthSession({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      user: payload.user
    })
    statusMessage.value = '登录成功，正在进入学习桌面...'
    router.push('/desktop')
  } catch (error) {
    errorMessage.value = error.message || '验证码登录失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const handleGetCode = async () => {
  if (isLoading.value) return

  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/auth/code/send', {
      method: 'POST',
      auth: false,
      body: {
        target: phone.value.trim(),
        channel: 'sms',
        purpose: 'login'
      }
    })
    statusMessage.value = payload.debug_code
      ? `验证码已发送，开发环境验证码：${payload.debug_code}`
      : '验证码已发送，请查收。'
  } catch (error) {
    errorMessage.value = error.message || '验证码发送失败，请稍后重试。'
  }
}
</script>

<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,#eef5ff_0%,#f5f3ff_52%,#fcfcff_100%)] text-slate-900">
    <div class="grid min-h-screen lg:grid-cols-[1.08fr_0.92fr]">
      <section
        class="relative hidden flex-col justify-between overflow-hidden bg-[linear-gradient(135deg,#3A86FF_0%,#5f6dff_48%,#7C4DFF_100%)] p-12 text-white lg:flex"
      >
        <div class="relative z-20">
          <router-link to="/" class="inline-flex rounded-2xl border border-white/20 bg-white/10 px-4 py-3 backdrop-blur-sm transition hover:bg-white/15">
            <Logo colorSVG="text-white" colorText="text-white"  />
          </router-link>
        </div>

        <div class="relative z-20 flex items-end justify-center">
          <LoginMascotScene
            :typing-active="isTypingActive"
            :typing-pulse="typingPulse"
            :has-password-value="hasPasswordValue"
            :password-visible="isPasswordVisible"
          />
        </div>

        <div class="relative z-20 flex items-center gap-8 text-sm text-white/70">
          <a href="javascript:void(0)" class="transition-colors hover:text-white">
            Privacy Policy
          </a>
          <a href="javascript:void(0)" class="transition-colors hover:text-white">
            Terms of Service
          </a>
          <a href="javascript:void(0)" class="transition-colors hover:text-white">
            Contact
          </a>
        </div>

        <div class="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[size:20px_20px]"></div>
        <div class="absolute left-[8%] top-[14%] size-72 rounded-full bg-white/10 blur-3xl"></div>
        <div class="absolute right-[10%] top-[10%] size-64 rounded-full bg-[#b8cbff]/20 blur-3xl"></div>
        <div class="absolute bottom-[8%] left-[18%] size-80 rounded-full bg-[#d7c9ff]/20 blur-3xl"></div>
      </section>

      <section class="relative flex items-center justify-center overflow-hidden p-8">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(58,134,255,0.18),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(124,77,255,0.18),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0.84)_0%,rgba(245,247,255,0.98)_100%)]"></div>

        <div class="relative z-10 w-full max-w-[460px] rounded-[32px] border border-white/70 bg-white/78 p-8 shadow-[0_28px_90px_-34px_rgba(79,102,228,0.38)] backdrop-blur-xl sm:p-10">
          <div class="mb-10 flex items-center justify-center lg:hidden">
            <router-link to="/" class="inline-flex rounded-2xl border border-[#cad7ff] bg-white/80 px-4 py-3 shadow-sm transition hover:border-[#aebfff] hover:bg-white">
              <Logo colorSVG="text-[#4f67ff]" colorText="bg-gradient-to-r from-[#3A86FF] to-[#7C4DFF] bg-clip-text text-transparent" text="XueTa" />
            </router-link>
          </div>

          <div class="mb-10 text-center">
            <p class="mb-3 text-xs font-semibold uppercase tracking-[0.36em] text-[#5f6dff]">
              Welcome Back
            </p>
            <h1 class="mb-2 bg-[linear-gradient(135deg,#2759d8_0%,#5f6dff_55%,#7C4DFF_100%)] bg-clip-text text-3xl font-bold tracking-tight text-transparent">
              欢迎回来
            </h1>
            <p class="text-sm text-slate-500">请输入你的账号信息，继续使用学塔。</p>
          </div>

          <div v-if="errorMessage || statusMessage" class="mb-6 space-y-2">
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
          </div>

          <Tabs v-model="authMode" defaultValue="password" class="w-full">
            <TabsList class="grid h-12 w-full grid-cols-2 rounded-full bg-[linear-gradient(135deg,rgba(58,134,255,0.14),rgba(124,77,255,0.14))] p-1">
              <TabsTrigger value="password" class="rounded-full text-sm font-medium">
                密码登录
              </TabsTrigger>
              <TabsTrigger value="code" class="rounded-full text-sm font-medium">
                验证码登录
              </TabsTrigger>
            </TabsList>

            <TabsContent value="password" class="mt-6">
              <form class="space-y-5" @submit.prevent="handlePasswordSubmit">
                <div class="space-y-2">
                  <Label htmlFor="email" class="text-sm font-medium text-slate-700">邮箱</Label>
                  <div class="relative">
                    <Icons
                      name="mail"
                      class="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-[#6c77aa]"
                    />
                    <Input
                      id="email"
                      v-model="email"
                      type="email"
                      placeholder="anna@gmail.com"
                      autoCapitalize="none"
                      autoComplete="email"
                      autoCorrect="off"
                      :disabled="isLoading"
                      class="h-12 rounded-2xl border-[#d8e1ff] bg-white/92 pl-11 pr-4 focus-visible:border-[#7C4DFF]/30 focus-visible:ring-[#7C4DFF]/20"
                      @focus="setTypingFocus('email', true)"
                      @blur="setTypingFocus('email', false)"
                    />
                  </div>
                </div>

                <div class="space-y-2">
                  <Label htmlFor="password" class="text-sm font-medium text-slate-700">密码</Label>
                  <div class="relative">
                    <Input
                      id="password"
                      v-model="password"
                      :type="passwordVisible.password ? 'text' : 'password'"
                      placeholder="请输入密码"
                      autoCapitalize="none"
                      autoComplete="current-password"
                      autoCorrect="off"
                      :disabled="isLoading"
                      class="h-12 rounded-2xl border-[#d8e1ff] bg-white/92 pr-11 focus-visible:border-[#7C4DFF]/30 focus-visible:ring-[#7C4DFF]/20"
                    />
                    <button
                      type="button"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-[#5f6dff]"
                      :aria-label="passwordVisible.password ? '隐藏密码' : '显示密码'"
                      :aria-pressed="passwordVisible.password"
                      @mousedown.prevent
                      @click="togglePasswordVisibility('password')"
                    >
                      <Icons :name="passwordVisible.password ? 'eye-off' : 'eye'" class="size-5" />
                    </button>
                  </div>
                </div>

                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <Checkbox id="remember" v-model="remember" />
                    <Label htmlFor="remember" class="cursor-pointer text-sm font-normal text-slate-600">
                      30 天内记住我
                    </Label>
                  </div>
                  <router-link
                    to="/auth/resetPassword"
                    class="text-sm font-medium text-[#5f6dff] transition-colors hover:text-[#7C4DFF]"
                  >
                    忘记密码？
                  </router-link>
                </div>

                <button
                  type="submit"
                  class="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3A86FF_0%,#5f6dff_55%,#7C4DFF_100%)] text-base font-medium text-white shadow-[0_18px_36px_-18px_rgba(95,109,255,0.75)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_42px_-16px_rgba(95,109,255,0.85)] disabled:cursor-not-allowed disabled:opacity-70"
                  :disabled="isLoading"
                >
                  {{ submitText }}
                </button>
              </form>
            </TabsContent>

            <TabsContent value="code" class="mt-6">
              <form class="space-y-5" @submit.prevent="handleCodeSubmit">
                <div class="space-y-2">
                  <Label htmlFor="phone" class="text-sm font-medium text-slate-700">手机号</Label>
                  <div class="relative">
                    <Icons
                      name="phone"
                      class="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-[#6c77aa]"
                    />
                    <Input
                      id="phone"
                      v-model="phone"
                      type="tel"
                      placeholder="请输入手机号"
                      autoCapitalize="none"
                      autoComplete="tel"
                      autoCorrect="off"
                      :disabled="isLoading"
                      class="h-12 rounded-2xl border-[#d8e1ff] bg-white/92 pl-11 pr-4 focus-visible:border-[#7C4DFF]/30 focus-visible:ring-[#7C4DFF]/20"
                    />
                  </div>
                </div>

                <div class="space-y-2">
                  <Label htmlFor="code" class="text-sm font-medium text-slate-700">验证码</Label>
                  <div class="flex gap-3">
                    <div class="relative flex-1">
                      <Icons
                        name="lock"
                        class="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-[#6c77aa]"
                      />
                      <Input
                        id="code"
                        v-model="code"
                        type="text"
                        placeholder="请输入验证码"
                        autoCapitalize="none"
                        autoComplete="one-time-code"
                        autoCorrect="off"
                        :disabled="isLoading"
                        class="h-12 rounded-2xl border-[#d8e1ff] bg-white/92 pl-11 pr-4 focus-visible:border-[#7C4DFF]/30 focus-visible:ring-[#7C4DFF]/20"
                      />
                    </div>
                    <button
                      type="button"
                      class="rounded-2xl border border-[#d6dfff] bg-[linear-gradient(135deg,rgba(58,134,255,0.1),rgba(124,77,255,0.1))] px-4 text-sm font-medium text-[#4f67ff] transition-colors hover:border-[#b8c7ff] hover:bg-[linear-gradient(135deg,rgba(58,134,255,0.16),rgba(124,77,255,0.16))] disabled:cursor-not-allowed disabled:opacity-70"
                      :disabled="isLoading"
                      @click="handleGetCode"
                    >
                      获取验证码
                    </button>
                  </div>
                </div>

                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <Checkbox id="remember-code" v-model="remember" />
                    <Label htmlFor="remember-code" class="cursor-pointer text-sm font-normal text-slate-600">
                      30 天内记住我
                    </Label>
                  </div>
                  <router-link
                    to="/auth/resetPassword"
                    class="text-sm font-medium text-[#5f6dff] transition-colors hover:text-[#7C4DFF]"
                  >
                    忘记密码？
                  </router-link>
                </div>

                <button
                  type="submit"
                  class="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3A86FF_0%,#5f6dff_55%,#7C4DFF_100%)] text-base font-medium text-white shadow-[0_18px_36px_-18px_rgba(95,109,255,0.75)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_42px_-16px_rgba(95,109,255,0.85)] disabled:cursor-not-allowed disabled:opacity-70"
                  :disabled="isLoading"
                >
                  {{ submitText }}
                </button>
              </form>
            </TabsContent>
          </Tabs>

          <div class="mt-6">
            <button
              type="button"
              class="inline-flex h-12 w-full items-center justify-center rounded-2xl border border-[#d8e1ff] bg-white/88 text-sm font-medium text-slate-700 transition-colors hover:bg-white"
            >
              <Icons name="mail" class="mr-2 size-5 text-[#5f6dff]" />
              使用邮箱验证码继续
            </button>
          </div>

          <div class="mt-8 text-center text-sm text-slate-500">
            还没有账号？
            <router-link
              to="/auth/register"
              class="font-medium text-[#4f67ff] transition-colors hover:text-[#7C4DFF]"
            >
              立即注册
            </router-link>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
