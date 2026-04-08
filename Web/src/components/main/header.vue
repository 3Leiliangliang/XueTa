<script setup>
import Logo from './logo.vue'
import { ref } from 'vue'
    
const page = ref([
    { id: 1, to: '/', name: '首页'},
    { id: 2, to: '/translate', name: '翻译'},
    { id: 3, to: '/qa', name: '答疑'},
    { id: 4, to: '/note', name: '笔记'},
    { id: 5, to: '/desktop', name: '桌面'},
    { id: 6, to: '/planning', name: '规划'},
])
</script>

<template>
    <header class="sticky top-0 z-50 w-full border-b border-slate-200/80 bg-white/75 backdrop-blur-sm px-12">
 
        <div class="container flex h-16 items-center justify-between">
            <div class="flex items-center gap-2">
                <router-link to="/">
                    <Logo/>
                </router-link>
                <span class="hidden md:inline-block text-sm text-slate-500 ml-2">AI驱动，高效学习</span>
            </div>

            <div class="middle">
                <nav class="hidden md:flex items-center gap-6">
                    <ul v-for="item in page" :key="item.id">
                        <router-link :to="item.to">{{ item.name }}</router-link>
                    </ul>
                    
                    
                </nav>
            </div>

            <div class="right">
                <button>
                    <router-link to="/auth/login">登录</router-link>
                </button>
                <button>
                    <router-link to="/auth/register">注册</router-link>
                </button>
            </div>
        </div>
        
    </header>
</template>

<style scoped></style>