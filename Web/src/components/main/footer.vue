<script setup>
import Logo from './logo.vue'

const functionItems = [
  { id: 1, to: '/translate', name: '智能翻译' },
  { id: 2, to: '/qa', name: 'AI 答疑' },
  { id: 3, to: '/note', name: '笔记整理' },
  { id: 4, to: '/kb', name: '知识库' },
  { id: 5, to: '/practice', name: '练习中心' },
  { id: 6, to: '/progress', name: '学习进度' },
  { id: 7, to: '/desktop', name: '学习桌面' },
  { id: 8, to: '/planning', name: '学习规划' }
]

const resourcesItems = [
  { id: 1, to: '/about', name: '关于学塔' },
  { id: 2, to: '/profile', name: '个人中心' },
  { id: 3, to: '/auth/login', name: '登录账号' },
  { id: 4, to: '/auth/register', name: '创建账号' }
]

const contact = {
  email: 'contact@learningtower.com',
  phone: '123-1234-1234',
  address: '黑龙江省哈尔滨市'
}
</script>

<template>
  <footer class="bg-slate-900 px-6 py-12 text-slate-300 md:px-12">
    <div class="mx-auto w-full max-w-7xl">
      <div class="grid grid-cols-1 gap-8 md:grid-cols-4">
        <div>
          <Logo colorSVG="text-[#ffffff]" colorText="bg-gradient-to-r " class="mb-4" />
          <p class="text-sm text-slate-400">
            AI 驱动的智能学习平台，让学习更高效、更智能、更有趣。
          </p>
        </div>

        <div>
          <h4 class="mb-4 font-medium text-white">功能</h4>
          <ul class="space-y-2 text-sm">
            <li v-for="item in functionItems" :key="item.id">
              <router-link :to="item.to" class="transition-colors hover:text-white">
                {{ item.name }}
              </router-link>
            </li>
          </ul>
        </div>

        <div>
          <h4 class="mb-4 font-medium text-white">入口</h4>
          <ul class="space-y-2 text-sm">
            <li v-for="item in resourcesItems" :key="item.id">
              <router-link :to="item.to" class="transition-colors hover:text-white">
                {{ item.name }}
              </router-link>
            </li>
          </ul>
        </div>

        <div>
          <h4 class="mb-4 font-medium text-white">联系我们</h4>
          <ul class="space-y-2 text-sm">
            <li>邮箱：{{ contact.email }}</li>
            <li>电话：{{ contact.phone }}</li>
            <li>地址：{{ contact.address }}</li>
          </ul>
        </div>
      </div>

      <div class="mt-8 border-t border-slate-800 pt-8 text-center text-sm text-slate-500">
        <p>© 2025 学塔 AI 学习平台. 保留所有权利.</p>
      </div>
    </div>
  </footer>
</template>

<style scoped></style>
