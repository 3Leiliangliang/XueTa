<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from './components/main/header.vue'
import Footer from './components/main/footer.vue'
import AIAssistant from './components/main/AIAssistant.vue'
import CursorAura from './components/main/CursorAura.vue'

const route = useRoute()

const showHeader = computed(() => route.meta?.showHeader !== false)
const showFooter = computed(() => route.meta?.showFooter !== false)
</script>

<template>
  <div id="app" class="relative min-h-screen overflow-x-hidden bg-white">
    <CursorAura />
    <div class="relative z-10">
      <Header v-if="showHeader" />
      <router-view />
      <Footer v-if="showFooter" />
      <AIAssistant />
    </div>
  </div>
</template>

<style scoped></style>
