<script setup>
import Logo from './logo.vue';
import { ref } from 'vue'

const functionItems = ref([
    { id: 1, to: '/translate', name: '智能翻译'},
    { id: 2, to: '/qa', name: 'AI 答疑' },
    { id: 3, to: '/note', name: '笔记整理' },
    { id: 4, to: '/desktop', name: '学习桌面' },
    { id: 5, to: '/planning', name: '学习规划' }
])
const resourcesItems = ref([
    { id: 1, to: '/blog', name: '学习博客'},
    { id: 2, to: '/userGuide', name: '使用教程' },
    { id: 3, to: '/faq', name: '常见问题' },
    { id: 4, to: '/helpCenter', name: '帮助中心' }
])
const contact = ref({
    email: 'contact@learningtower.com',
    phone: '123-1234-1234',
    address: '黑龙江省哈尔滨市'
})

</script>

<template>
    <footer class="bg-slate-900 text-slate-300 py-12 px-12">
        <div class="container">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
                <Logo colorSVG="text-[#ffffff]" colorText="bg-gradient-to-r " class="mb-4"/>
                <p class="text-sm text-slate-400">AI 驱动的智能学习平台，让学习更高效、更智能、更有趣。</p>
            </div>

            <div>
                <h4 class="font-medium text-white mb-4">功能</h4>
                <ul class="space-y-2 text-sm">
                    <li v-for="item in functionItems" :key="item.id">
                        <router-link :to="item.to" class="hover:text-white transition-colors">
                        {{ item.name }}
                        </router-link>
                    </li>
                </ul>
            </div>

            <div>
                <h4 class="font-medium text-white mb-4">资源</h4>
                <ul class="space-y-2 text-sm">
                    <li v-for="item in resourcesItems" :key="item.id">
                        <router-link :to="item.to" class="hover:text-white transition-colors">
                        {{ item.name }}
                        </router-link>
                    </li>
                </ul>
            </div>

            <div>
                <h4 class="font-medium text-white mb-4">联系我们</h4>
                <ul class="space-y-2 text-sm">
                <li>邮箱： {{ contact.email }}</li>
                <li>电话： {{ contact.phone }}</li>
                <li>地址:  {{ contact.address }}</li>
                </ul>
            </div>
            </div>
            
            <div class="border-t border-slate-800 mt-8 pt-8 text-center text-sm text-slate-500">
            <p>© 2025 学塔 AI 学习平台. 保留所有权利.</p>
            </div>
        </div>
    </footer>
    
</template>

<style scoped></style>