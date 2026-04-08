<script setup>
import { ref, computed } from 'vue'
import Button from '@/components/ui/button.vue'
import IconTranslate from '@/components/icons/IconTranslate.vue'
import IconQA from '@/components/icons/IconQA.vue'
import IconNotes from '@/components/icons/IconNotes.vue'
import IconDesktop from '@/components/icons/IconDesktop.vue'
import IconPlanning from '@/components/icons/IconPlanning.vue'
import IconData from '@/components/icons/IconData.vue'
import IconLeft from '@/components/icons/IconLeft.vue'
import IconRight from '@/components/icons/IconRight.vue'
import Start from '@/components/main/start.vue'
const heroFeatures = [
  { id: 1, label: '翻译', to: '/translate', icon: IconTranslate ,class: 'text-[#3A86FF]'},
  { id: 2, label: '答疑', to: '/qa', icon: IconQA ,class: 'text-[#6C5CE7]'},
  { id: 3, label: '笔记', to: '/note', icon: IconNotes ,class: 'text-[#9333EA]'},
  { id: 4, label: '学习桌面', to: '/desktop', icon: IconDesktop ,class: 'text-[#0EA5E9]'},
  { id: 5, label: '学习规划', to: '/planning', icon: IconPlanning ,class: 'text-[#F472B6]'},
]

const experienceCards = [
  {
    id: 1,
    title: '智能翻译',
    desc: '一键翻译论文、文档，AI 自动总结要点，支持多语言互译，助力跨语言高效学习。',
    icon: IconTranslate,
    color: 'text-[#3A86FF]',
  },
  {
    id: 2,
    title: 'AI 答疑',
    desc: '智能解答学习疑问，提供深度解析和拓展资料，让学习过程更加顺畅。',
    icon: IconQA,
    color: 'text-[#6C5CE7]',
  },
  {
    id: 3,
    title: '笔记整理',
    desc: 'AI 自动整理笔记格式，生成思维导图和知识图谱，系统化您的学习内容。',
    icon: IconNotes,
    color: 'text-[#9333EA]',
  },
  {
    id: 4,
    title: '学习桌面',
    desc: '多任务学习工作区，集成翻译、笔记、答疑于一体，打造沉浸式学习环境。',
    icon: IconDesktop,
    color: 'text-[#0EA5E9]',
  },
  {
    id: 5,
    title: '学习规划',
    desc: 'AI 根据学习目标智能规划任务，可视化进度追踪，提高学习效率。',
    icon: IconPlanning,
    color: 'text-[#F472B6]',
  },
  {
    id: 6,
    title: '数据分析',
    desc: '学习数据可视化，掌握知识点掌握情况和时间投入，为个性化学习提供依据。',
    icon: IconData,
    color: 'text-[#0EA5E9]',
  },
]

const highlightSlides = [
  {
    id: 1,
    title: '一键翻译论文',
    desc: '上传英文论文，AI 自动翻译并提取关键要点，帮助您快速理解核心内容。',
    cta: '前往翻译',
    to: '/translate',
  },
  {
    id: 2,
    title: '智能学习桌面',
    desc: '在同一界面中完成翻译、记笔记和查资料，让学习过程井井有条。',
    cta: '体验学习桌面',
    to: '/desktop',
  },
  {
    id: 3,
    title: '学习规划与进度追踪',
    desc: '基于目标自动拆解任务，生成学习日程表，实时查看学习进度和完成情况。',
    cta: '查看学习规划',
    to: '/planning',
  },
]

const currentSlideIndex = ref(0)
const totalSlides = computed(() => highlightSlides.length)

const prevSlide = () => {
  currentSlideIndex.value =
    (currentSlideIndex.value - 1 + totalSlides.value) % totalSlides.value
}

const nextSlide = () => {
  currentSlideIndex.value = (currentSlideIndex.value + 1) % totalSlides.value
}

const currentSlide = computed(
  () => highlightSlides[currentSlideIndex.value],
)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main class="container mx-auto px-4 md:px-12 py-12 md:py-16 space-y-20 md:space-y-24">
      <!-- 顶部 Hero 区 -->
      <section class="grid lg:grid-cols-2 gap-10 md:gap-14 items-center">
        <div class="space-y-6 md:space-y-8">
          <div class="inline-flex items-center gap-2 rounded-full bg-white/80 px-4 py-1 text-xs md:text-sm text-slate-500 shadow-sm border border-slate-200/70">
            <span class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white text-[10px]">
              AI
            </span>
            <span>AI 驱动的智能学习平台</span>
          </div>

          <h1
            class="text-3xl md:text-5xl lg:text-6xl font-bold leading-tight bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent"
          >
            让学习更高效、<br class="hidden md:block" />
            更智能
          </h1>

          <p class="text-base md:text-lg text-slate-600 max-w-xl">
            学塔深度融合 AI 推理生成能力，为您提供翻译、答疑、笔记整理、学习桌面和学习规划等多种功能，
            提高学习效率，解决学习难题。
          </p>

          <div class="flex  flex-row gap-3">
            <router-link to="/desktop" class="w-full sm:w-auto">
              <Button
                size="lg"
                type="normal"
                class="w-full sm:w-auto bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white shadow-md hover:shadow-lg py-2 px-5"
              >
                立即开始
              </Button>
            </router-link>
            <router-link to="/about" class="w-full sm:w-auto ">
              <Button
                size="lg"
                variant="outline"
                class="w-full sm:w-auto border-slate-300 bg-white/80 hover:bg-white py-2 px-5"
              >
                了解更多
              </Button>
            </router-link>
          </div>

          <div
            class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 md:gap-4 pt-4 md:pt-6"
          >
            <router-link
              v-for="item in heroFeatures"
              :key="item.id"
              :to="item.to"
              class="group flex flex-col items-center justify-center gap-1 rounded-xl bg-white/80 px-3 py-3 md:py-4 shadow-sm border border-slate-200/70 hover:border-[#3A86FF]/60 hover:-translate-y-0.5 hover:shadow-md transition-all text-center"
            >
              <div class="text-lg md:text-xl text-[#3A86FF]" :class="item.class">
                <component
                  :is="item.icon"
                  class="h-5 w-5 md:h-6 md:w-6"
                />
              </div>
              <div class="text-xs md:text-sm font-medium text-slate-700">
                {{ item.label }}
              </div>
            </router-link>
          </div>
        </div>

        <div
          class="relative hidden lg:flex items-center justify-center"
          aria-hidden="true"
        >
          <div
            class="h-80 w-full max-w-md rounded-[32px] bg-gradient-to-br from-white to-slate-100 shadow-[0_24px_80px_rgba(15,23,42,0.12)] border border-slate-100 overflow-hidden flex items-center justify-center"
          >
            <div
              class="h-40 w-40 rounded-full border border-dashed border-slate-200 flex items-center justify-center"
            >
              <div
                class="h-24 w-24 rounded-full bg-slate-100 flex items-center justify-center"
              >
                <span class="text-4xl">📚</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- AI 驱动的学习体验 -->
      <section>
        <div class="text-center mb-10 md:mb-12">
          <h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-3">
            AI 驱动的学习体验
          </h2>
          <p class="text-sm md:text-base text-slate-600 max-w-2xl mx-auto">
            学塔将多种 AI 学习工具整合到一个平台中，为您提供高效、智能化的学习体验，
            解决学习过程中遇到的各类挑战。
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="card in experienceCards"
            :key="card.id"
            class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between hover:-translate-y-1 hover:shadow-md transition-all"
          >
            <div class="flex items-start gap-3 mb-4">
              <component
                :is="card.icon"
                class="h-5 w-5 md:h-6 md:w-6" :class="card.color"
              />
              <h3 class="text-lg font-semibold text-slate-900" >
                {{ card.title }}
              </h3>
            </div>
            <p class="text-sm md:text-[15px] text-slate-600">
              {{ card.desc }}
            </p>
          </div>
        </div>
      </section>

      <!-- 智能学习桌面 -->
      <section class="grid lg:grid-cols-2 gap-10 md:gap-14 items-center">
        <div class="space-y-5 md:space-y-6">
          <h2 class="text-2xl md:text-3xl font-bold text-slate-900">
            智能学习桌面
          </h2>
          <p class="text-sm md:text-base text-slate-600">
            集成翻译、笔记编辑和学习规划于一体的多任务学习工作区，让您的学习过程更加高效和有序。
            AI 助手实时提供支持，解决疑问，整理笔记，优化学习计划。
          </p>
          <ul class="space-y-3 text-sm md:text-base text-slate-700">
            <li class="flex items-start gap-2">
              <span class="mt-1 h-5 w-5 rounded-full bg-[#3A86FF]/10 flex items-center justify-center text-[10px] text-[#3A86FF]">
                ●
              </span>
              <div>
                实时翻译窗口，支持论文、网页和划词翻译，AI 自动总结要点。
              </div>
            </li>
            <li class="flex items-start gap-2">
              <span class="mt-1 h-5 w-5 rounded-full bg-[#6C5CE7]/10 flex items-center justify-center text-[10px] text-[#6C5CE7]">
                ●
              </span>
              <div>
                笔记编辑区，支持 Markdown 和富文本，AI 自动整理格式并生成思维导图。
              </div>
            </li>
            <li class="flex items-start gap-2">
              <span class="mt-1 h-5 w-5 rounded-full bg-sky-100 flex items-center justify-center text-[10px] text-sky-500">
                ●
              </span>
              <div>
                学习规划看板，可视化安排任务，AI 根据学习目标推荐任务分配。
              </div>
            </li>
          </ul>
          <router-link to="/desktop" >
            <Button
              size="lg"
              class="mt-4 bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white shadow-md hover:shadow-lg max-w-40 "
            >
              体验学习桌面
            </Button>
          </router-link>
        </div>

        <div
          class="relative h-72 md:h-80 rounded-[32px] bg-slate-100 border border-slate-200 shadow-[0_18px_60px_rgba(15,23,42,0.12)] overflow-hidden flex flex-col"
        >
          <div
            class="h-10 px-4 flex items-center justify-between border-b border-slate-200 bg-slate-50"
          >
            <div class="flex items-center gap-2">
              <span class="h-2.5 w-2.5 rounded-full bg-red-400" />
              <span class="h-2.5 w-2.5 rounded-full bg-amber-300" />
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-400" />
            </div>
            <span class="text-xs text-slate-500">学塔 - 智能学习桌面</span>
            <span class="w-10" />
          </div>
          <div class="flex-1 grid grid-cols-3 gap-4 p-5 text-xs text-slate-400">
            <div class="rounded-xl bg-white/80 border border-slate-200/80" />
            <div class="rounded-xl bg-white/80 border border-slate-200/80" />
            <div class="rounded-xl bg-white/80 border border-slate-200/80" />
          </div>
        </div>
      </section>

      <!-- 功能亮点展示（简易轮播） -->
      <section class="space-y-8 md:space-y-10">
        <div class="text-center">
          <h2 class="text-2xl md:text-3xl font-bold text-slate-900 mb-3">
            功能亮点展示
          </h2>
          <p class="text-sm md:text-base text-slate-600 max-w-2xl mx-auto">
            从翻译到规划，学塔为您的每一个学习场景提供专业支持。
          </p>
        </div>

        <div
          class="grid lg:grid-cols-2 gap-8 md:gap-10 items-center bg-white rounded-2xl md:rounded-3xl border border-slate-200 shadow-sm p-5 md:p-8"
        >
          <div
            class="relative h-52 md:h-64 rounded-2xl bg-slate-100 border border-dashed border-slate-200 flex items-center justify-center"
          >
            <div
              class="h-28 w-28 md:h-32 md:w-32 rounded-full bg-slate-50 border border-slate-200 flex items-center justify-center"
            >
              <span class="text-4xl md:text-5xl text-slate-300">📝</span>
            </div>
          </div>

          <div class="space-y-4 md:space-y-6">
            <div class="space-y-2">
              <h3 class="text-xl md:text-2xl font-bold text-slate-900">
                {{ currentSlide.title }}
              </h3>
              <p class="text-sm md:text-base text-slate-600">
                {{ currentSlide.desc }}
              </p>
            </div>

            <router-link :to="currentSlide.to" class="flex justify-center">
              <Button
                size="lg"
                class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white max-w-40"
              >
                {{ currentSlide.cta }}
              </Button>
            </router-link>

            <div class="flex items-center justify-between pt-2">
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="h-8 w-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50"
                  @click="prevSlide"
                >
                  <IconLeft />
                </button>
                <button
                  type="button"
                  class="h-8 w-8 rounded-full border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50"
                  @click="nextSlide"
                >
                  <IconRight />
                </button>
              </div>
              <div class="flex items-center gap-1">
                <span
                  v-for="(slide, index) in highlightSlides"
                  :key="slide.id"
                  class="h-1.5 rounded-full transition-all"
                  :class="
                    index === currentSlideIndex
                      ? 'w-5 bg-[#3A86FF]'
                      : 'w-2 bg-slate-300'
                  "
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 学习数据分析 -->
      <section class="grid lg:grid-cols-2 gap-10 md:gap-14 items-center">
        <div
          class="order-2 lg:order-1 space-y-5 md:space-y-6"
        >
          <h2 class="text-2xl md:text-3xl font-bold text-slate-900">
            学习数据分析
          </h2>
          <p class="text-sm md:text-base text-slate-600">
            可视化学习数据报告，帮助您了解学习投入、进度和效果，知识点掌握热力图直观展示学习情况，
            AI 根据数据提供个性化学习建议。
          </p>
          <ul class="space-y-3 text-sm md:text-base text-slate-700">
            <li class="flex items-start gap-2">
              <span class="mt-1 h-5 w-5 rounded-full bg-sky-100 flex items-center justify-center text-[10px] text-sky-500">
                ●
              </span>
              <div>时间投入统计，追踪每日学习时长，分析学习节奏和效率。</div>
            </li>
            <li class="flex items-start gap-2">
              <span class="mt-1 h-5 w-5 rounded-full bg-violet-100 flex items-center justify-center text-[10px] text-violet-500">
                ●
              </span>
              <div>知识点掌握热力图，直观展示各知识点掌握度，发现薄弱环节。</div>
            </li>
            <li class="flex items-start gap-2">
              <span class="mt-1 h-5 w-5 rounded-full bg-emerald-100 flex items-center justify-center text-[10px] text-emerald-500">
                ●
              </span>
              <div>成就系统，解锁学习勋章，激励持续学习与复盘。</div>
            </li>
          </ul>
          <router-link to="/desktop">
            <Button
              size="lg"
              variant="outline"
              class="border-[#3A86FF] text-[#3A86FF] hover:bg-[#3A86FF]/5 max-w-40 mt-4"
            >
              查看学习报告
            </Button>
          </router-link>
        </div>

        <div
          class="order-1 lg:order-2 h-72 md:h-80 rounded-[32px] bg-slate-100 border border-slate-200 shadow-[0_18px_60px_rgba(15,23,42,0.12)] overflow-hidden flex items-center justify-center"
        >
          <div class="w-3/4 h-3/4 rounded-2xl bg-white/90 border border-slate-200 p-4">
            <div class="h-6 rounded-md bg-slate-100 mb-4" />
            <div class="grid grid-cols-4 gap-3 mb-4">
              <div class="h-16 rounded-md bg-[#3A86FF]/15" />
              <div class="h-20 rounded-md bg-[#3A86FF]/25" />
              <div class="h-12 rounded-md bg-[#3A86FF]/10" />
              <div class="h-24 rounded-md bg-[#3A86FF]/35" />
            </div>
            <div class="h-20 rounded-md bg-slate-100" />
          </div>
        </div>
      </section>

      <section>
        <Start />
      </section>
    </main>
  </div>
</template>

<style scoped></style>