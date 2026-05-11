<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import LoginMascotScene from '@/components/auth/LoginMascotScene.vue'
import Logo from '@/components/main/logo.vue'
import Input from '@/components/ui/input.vue'
import Label from '@/components/ui/label.vue'
import Checkbox from '@/components/ui/checkbox.vue'
import Icons from '@/components/ui/icons.vue'
import { useAuthMascot } from '@/useAuthMascot'
import { apiRequest } from '@/lib/api'
import { saveAuthSession } from '@/lib/auth'

const router = useRouter()
const username = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const agreed = ref(false)
const isLoading = ref(false)
const statusMessage = ref('')
const errorMessage = ref('')

const {
  hasPasswordValue,
  isPasswordVisible,
  isTypingActive,
  passwordVisible,
  setTypingFocus,
  togglePasswordVisibility,
  typingPulse
} = useAuthMascot({
  passwordRefs: [password, confirmPassword],
  fieldNames: ['password', 'confirmPassword'],
  typingFieldNames: ['username', 'email', 'phone']
})

const handleSubmit = async () => {
  if (isLoading.value) return

  if (!agreed.value) {
    errorMessage.value = '请先同意服务条款与隐私政策。'
    return
  }

  const trimmedUsername = username.value.trim()
  const trimmedEmail = email.value.trim()
  const trimmedPhone = phone.value.trim()

  if (trimmedUsername.length < 3) {
    errorMessage.value = '用户名至少需要 3 个字符。'
    return
  }
  if (!trimmedEmail && !trimmedPhone) {
    errorMessage.value = '邮箱和手机号至少填写一个。'
    return
  }
  if (trimmedPhone && trimmedPhone.length < 6) {
    errorMessage.value = '手机号长度至少为 6 位。'
    return
  }
  if (password.value.length < 8) {
    errorMessage.value = '密码长度至少为 8 位。'
    return
  }
  if (confirmPassword.value.length < 8) {
    errorMessage.value = '确认密码长度至少为 8 位。'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致。'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const payload = await apiRequest('/auth/register', {
      method: 'POST',
      auth: false,
      body: {
        username: trimmedUsername,
        email: trimmedEmail || null,
        phone: trimmedPhone || null,
        password: password.value,
        confirm_password: confirmPassword.value
      }
    })

    saveAuthSession({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      user: payload.user
    })
    statusMessage.value = '注册成功，正在进入学习桌面...'
    router.push('/desktop')
  } catch (error) {
    errorMessage.value = error.message || '注册失败，请稍后重试。'
  } finally {
    isLoading.value = false
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

        <div class="relative z-10 w-full max-w-[480px] rounded-[32px] border border-white/70 bg-white/78 p-8 shadow-[0_28px_90px_-34px_rgba(79,102,228,0.38)] backdrop-blur-xl sm:p-10">
          <div class="mb-10 flex items-center justify-center lg:hidden">
            <router-link to="/" class="inline-flex rounded-2xl border border-[#cad7ff] bg-white/80 px-4 py-3 shadow-sm transition hover:border-[#aebfff] hover:bg-white">
              <Logo colorSVG="text-[#4f67ff]" colorText="bg-gradient-to-r from-[#3A86FF] to-[#7C4DFF] bg-clip-text text-transparent" text="XueTa" />
            </router-link>
          </div>

          <div class="mb-10 text-center">
            <p class="mb-3 text-xs font-semibold uppercase tracking-[0.36em] text-[#5f6dff]">
              Create Account
            </p>
            <h1 class="mb-2 bg-[linear-gradient(135deg,#2759d8_0%,#5f6dff_55%,#7C4DFF_100%)] bg-clip-text text-3xl font-bold tracking-tight text-transparent">
              创建账号
            </h1>
            <p class="text-sm text-slate-500">加入学塔，开启你的智能学习旅程。</p>
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

          <form class="space-y-5" @submit.prevent="handleSubmit">
            <div class="grid gap-5 sm:grid-cols-2">
              <div class="space-y-2">
                <Label htmlFor="username" class="text-sm font-medium text-slate-700">用户名</Label>
                <Input
                  id="username"
                  v-model="username"
                  type="text"
                  placeholder="请输入用户名"
                  autoCapitalize="none"
                  autoComplete="username"
                  autoCorrect="off"
                  :disabled="isLoading"
                  class="h-12 rounded-2xl border-[#d8e1ff] bg-white/92 px-4 focus-visible:border-[#7C4DFF]/30 focus-visible:ring-[#7C4DFF]/20"
                  @focus="setTypingFocus('username', true)"
                  @blur="setTypingFocus('username', false)"
                />
              </div>

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
                    @focus="setTypingFocus('phone', true)"
                    @blur="setTypingFocus('phone', false)"
                  />
                </div>
              </div>
            </div>

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
                  placeholder="you@example.com"
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

            <div class="grid gap-5 sm:grid-cols-2">
              <div class="space-y-2">
                <Label htmlFor="password" class="text-sm font-medium text-slate-700">密码</Label>
                <div class="relative">
                  <Input
                    id="password"
                    v-model="password"
                    :type="passwordVisible.password ? 'text' : 'password'"
                    placeholder="请设置密码"
                    autoCapitalize="none"
                    autoComplete="new-password"
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

              <div class="space-y-2">
                <Label htmlFor="confirm-password" class="text-sm font-medium text-slate-700">确认密码</Label>
                <div class="relative">
                  <Input
                    id="confirm-password"
                    v-model="confirmPassword"
                    :type="passwordVisible.confirmPassword ? 'text' : 'password'"
                    placeholder="请再次输入密码"
                    autoCapitalize="none"
                    autoComplete="new-password"
                    autoCorrect="off"
                    :disabled="isLoading"
                    class="h-12 rounded-2xl border-[#d8e1ff] bg-white/92 pr-11 focus-visible:border-[#7C4DFF]/30 focus-visible:ring-[#7C4DFF]/20"
                  />
                  <button
                    type="button"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-[#5f6dff]"
                    :aria-label="passwordVisible.confirmPassword ? '隐藏密码' : '显示密码'"
                    :aria-pressed="passwordVisible.confirmPassword"
                    @mousedown.prevent
                    @click="togglePasswordVisibility('confirmPassword')"
                  >
                    <Icons :name="passwordVisible.confirmPassword ? 'eye-off' : 'eye'" class="size-5" />
                  </button>
                </div>
              </div>
            </div>

            <div class="flex items-start gap-3">
              <Checkbox id="agreed" v-model="agreed" :disabled="isLoading" />
              <label for="agreed" class="pt-0.5 text-sm leading-6 text-slate-600">
                我已阅读并同意
                <a
                  href="javascript:void(0)"
                  class="font-medium text-[#4f67ff] transition-colors hover:text-[#7C4DFF]"
                >
                  《服务条款》
                </a>
                和
                <a
                  href="javascript:void(0)"
                  class="font-medium text-[#4f67ff] transition-colors hover:text-[#7C4DFF]"
                >
                  《隐私政策》
                </a>
              </label>
            </div>

            <button
              type="submit"
              class="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#3A86FF_0%,#5f6dff_55%,#7C4DFF_100%)] text-base font-medium text-white shadow-[0_18px_36px_-18px_rgba(95,109,255,0.75)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_42px_-16px_rgba(95,109,255,0.85)] disabled:cursor-not-allowed disabled:opacity-70"
              :disabled="isLoading"
            >
              {{ isLoading ? '注册中...' : '创建账号' }}
            </button>
          </form>

          <div class="mt-8 text-center text-sm text-slate-500">
            已有账号？
            <router-link
              to="/auth/login"
              class="font-medium text-[#4f67ff] transition-colors hover:text-[#7C4DFF]"
            >
              立即登录
            </router-link>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
