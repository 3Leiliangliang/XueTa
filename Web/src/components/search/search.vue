<script setup>
import { computed, ref } from 'vue'
import Input from '@/components/ui/input.vue'
import IconSearch from '@/components/icons/IconSearch.vue'
import IconGoogle from '@/components/icons/browser/IconGoogle.vue'
import IconBaidu from '@/components/icons/browser/IconBaidu.vue'
import IconBing from '@/components/icons/browser/IconBing.vue'
import IconLeft from '@/components/icons/IconLeft.vue'

const props = defineProps({
  defaultEngine: {
    type: String,
    default: 'baidu'
  }
})

const engines = [
  {
    value: 'baidu',
    label: 'Baidu',
    url: 'https://www.baidu.com/s?wd=',
    icon: IconBaidu
  },
  {
    value: 'google',
    label: 'Google',
    url: 'https://www.google.com/search?q=',
    icon: IconGoogle
  },
  {
    value: 'bing',
    label: 'Bing',
    url: 'https://www.bing.com/search?q=',
    icon: IconBing
  }
]

const keyword = ref('')
const isExpanded = ref(false)
const currentEngine = ref(
  engines.find((engine) => engine.value === props.defaultEngine)?.value ?? engines[0].value
)

const currentEngineConfig = computed(
  () => engines.find((engine) => engine.value === currentEngine.value) ?? engines[0]
)

const otherEngines = computed(() =>
  engines.filter((engine) => engine.value !== currentEngine.value)
)

const handleSearch = () => {
  const q = keyword.value.trim()
  if (!q) return

  const base = currentEngineConfig.value.url
  const encoded = encodeURIComponent(q)
  window.open(`${base}${encoded}`, '_blank')
}

const handleSelectEngine = (value) => {
  currentEngine.value = value
}

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="relative w-full max-w-full flex-none">
    <div class="flex items-center gap-3 rounded-3xl bg-gradient-to-b from-white/95 to-white/80 px-4 py-3 shadow-lg backdrop-blur-md">
      <button
        type="button"
        class="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
        @click="toggleExpanded"
      >
        <IconLeft
          class="h-4 w-4 transform transition-transform duration-200"
          :class="isExpanded ? '-rotate-90' : 'rotate-90'"
        />
      </button>

      <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-50">
        <component :is="currentEngineConfig.icon" class="h-7 w-7 text-slate-800" />
      </div>

      <div class="relative flex-1">
        <Input
          v-model="keyword"
          :placeholder="`请输入搜索内容，在 ${currentEngineConfig.label} 中搜索...`"
          class="border-0 bg-transparent pr-11 shadow-none placeholder:text-slate-400"
          @keydown.enter.prevent="handleSearch"
        />

        <button
          type="button"
          class="absolute inset-y-0 right-1 my-auto flex h-8 w-8 items-center justify-center rounded-full bg-[#3A86FF] text-white shadow-sm transition hover:bg-[#2563eb] active:scale-95"
          @click="handleSearch"
        >
          <IconSearch class="h-4 w-4" />
        </button>
      </div>
    </div>

    <div
      v-if="isExpanded"
      class="absolute left-0 right-0 top-[calc(100%+12px)] z-30 rounded-3xl bg-white/95 p-4 shadow-[0_18px_50px_rgba(15,23,42,0.14)] backdrop-blur-md"
    >
      <div class="flex flex-col gap-4 md:flex-row md:items-center">
        <div class="flex items-center gap-3 rounded-2xl bg-slate-50 px-4 py-3 shadow-sm">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-white">
            <component :is="currentEngineConfig.icon" class="h-8 w-8 text-slate-900" />
          </div>
          <div class="flex flex-col">
            <span class="text-sm font-semibold text-slate-900">
              {{ currentEngineConfig.label }}
            </span>
            <span class="text-xs text-slate-400">当前搜索引擎</span>
          </div>
        </div>

        <div class="flex flex-1 flex-wrap items-center gap-3">
          <button
            v-for="engine in otherEngines"
            :key="engine.value"
            type="button"
            class="flex flex-col items-center gap-1 rounded-2xl bg-white px-3 py-2 text-xs text-slate-600 shadow-sm transition hover:-translate-y-0.5 hover:bg-white hover:text-slate-900"
            @click="handleSelectEngine(engine.value)"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-50">
              <component :is="engine.icon" class="h-6 w-6 text-slate-900" />
            </div>
            <span>{{ engine.label }}</span>
          </button>

          <button
            type="button"
            class="flex flex-col items-center gap-1 rounded-2xl border border-dashed border-slate-300/80 bg-white/60 px-3 py-2 text-xs text-slate-500 transition hover:border-[#3A86FF] hover:text-[#3A86FF]"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-2xl border border-dashed border-slate-300/80">
              <span class="text-base leading-none">+</span>
            </div>
            <span>添加</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
