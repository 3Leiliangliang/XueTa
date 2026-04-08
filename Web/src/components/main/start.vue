<script setup>
import Button from '../ui/button.vue'
</script>
<template>
    <div class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] rounded-2xl p-8 md:p-12 text-white text-center">
        <h2 class="text-3xl font-bold mb-4">准备好开始智能学习之旅了吗？</h2>
        <p class="max-w-2xl mx-auto mb-8 opacity-90">
            加入学塔，体验AI驱动的高效学习方式，提升学习效率，解决学习难题。现在注册即可获得7天免费试用。
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <router-link to="/auth/register">
            <Button 
            size="lg" 
            type="normal"
            class="bg-white text-[#3A86FF] hover:bg-white/90 border rounded py-2 px-5" >
                免费注册
            </Button>
            </router-link>
            <router-link to="/desktop">
            <Button size="lg" variant="outline" class="bg-white text-[#3A86FF] border-white hover:bg-white/90 border rounded py-2 px-5">
                体验学习桌面
            </Button>
            </router-link>
        </div>
    </div>
</template>
<style scoped></style>