<script setup>

import  Button  from '@/components/ui/button.vue'
import IconTranslate from '@/components/icons/IconTranslate.vue'
import IconQA from '@/components/icons/IconQA.vue'
import IconNotes from '@/components/icons/IconNotes.vue'
import IconAssistant from '@/components/icons/IconAssistant.vue'
import IconPlanning from '@/components/icons/IconPlanning.vue'
import IconLogo from '@/components/icons/IconLogo.vue'
import Start from '@/components/main/start.vue'
</script>
<template>
    <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <main class="container mx-auto px-12 py-16">
        <section class="mb-20">
          <div class="max-w-3xl mx-auto text-center">
            <h1 class="text-4xl font-bold mb-6 bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent">
              关于学塔
            </h1>
            <p class="text-xl text-slate-600 mb-8">
              学塔是一个AI驱动的智能学习平台，致力于通过人工智能技术提升学习效率，解决学习难题。
            </p>
          </div>
        </section>

        <section class="mb-20">
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
            <h2 class="text-2xl font-bold mb-6 text-center">我们的使命</h2>
            <div class="max-w-3xl mx-auto">
              <p class="text-lg text-slate-600 mb-6">
                学塔的使命是通过AI技术革新学习方式，让每个人都能更高效、更智能地学习。我们相信，技术应该服务于教育，让学习变得更加个性化、高效和有趣。
              </p>
              <p class="text-lg text-slate-600">
                无论您是学生、研究人员还是终身学习者，学塔都能为您提供强大的学习工具和智能辅助，帮助您突破学习瓶颈，实现学习目标。
              </p>
            </div>
          </div>
        </section>

        <section class="mb-20">
          <h2 class="text-2xl font-bold mb-10 text-center">核心功能</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div class="flex items-start gap-4">
                <div class="h-12 w-12 rounded-full bg-[#3A86FF]/10 flex items-center justify-center flex-shrink-0">
                    <IconTranslate class="h-6 w-6 text-[#3A86FF]"/>
                </div>
                <div>
                  <h3 class="text-xl font-bold mb-2">智能翻译</h3>
                  <p class="text-slate-600 mb-4">
                    利用先进的AI翻译技术，提供高质量的文档、论文翻译服务，支持多语言互译，自动提取关键要点，帮助您快速理解外语资料。
                  </p>
                  <router-link to="/translate" class="inline-flex items-center gap-2  border rounded  px-2">
                    <Button variant="outline" size="sm" >
                      了解更多 
                    </Button>
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-right-icon lucide-arrow-right">
                        <path d="M5 12h14"/>
                        <path d="m12 5 7 7-7 7"/>
                    </svg>
                  </router-link>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div class="flex items-start gap-4">
                <div class="h-12 w-12 rounded-full bg-[#6C5CE7]/10 flex items-center justify-center flex-shrink-0">
                    <IconQA class="h-6 w-6 text-[#6C5CE7]"/>
                </div>
                <div>
                  <h3 class="text-xl font-bold mb-2">AI 答疑</h3>
                  <p class="text-slate-600 mb-4">
                    智能解答学习疑问，提供深度解析和拓展资料，支持多角度讨论和可视化解析，让复杂概念变得简单易懂。
                  </p>
                  <router-link to="/qa" class="inline-flex items-center gap-2  border rounded  px-2">
                    <Button variant="outline" size="sm" >
                      了解更多 
                    </Button>
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-right-icon lucide-arrow-right">
                        <path d="M5 12h14"/>
                        <path d="m12 5 7 7-7 7"/>
                    </svg>
                  </router-link>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div class="flex items-start gap-4">
                <div class="h-12 w-12 rounded-full bg-[#3A86FF]/10 flex items-center justify-center flex-shrink-0">
                    <IconNotes class="h-6 w-6 text-[#9333EA]"/>
                </div>
                <div>
                  <h3 class="text-xl font-bold mb-2">笔记整理</h3>
                  <p class="text-slate-600 mb-4">
                    AI自动整理笔记格式，生成思维导图和知识图谱，提取关键知识点，帮助您系统化学习内容，提高记忆效率。
                  </p>
                  <router-link to="/note" class="inline-flex items-center gap-2  border rounded  px-2">
                    <Button variant="outline" size="sm" >
                      了解更多 
                    </Button>
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-right-icon lucide-arrow-right">
                        <path d="M5 12h14"/>
                        <path d="m12 5 7 7-7 7"/>
                    </svg>
                  </router-link>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div class="flex items-start gap-4">
                <div class="h-12 w-12 rounded-full bg-[#6C5CE7]/10 flex items-center justify-center flex-shrink-0">
                    <IconPlanning class="h-6 w-6 text-[#F472B6]"/>
                </div>
                <div>
                  <h3 class="text-xl font-bold mb-2">学习规划</h3>
                  <p class="text-slate-600 mb-4">
                    AI根据学习目标智能规划任务，可视化进度跟踪，提供学习气象预测，帮助您合理安排时间，提高学习效率。
                  </p>
                  <router-link to="/planning" class="inline-flex items-center gap-2  border rounded  px-2">
                    <Button variant="outline" size="sm" >
                      了解更多 
                    </Button>
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-arrow-right-icon lucide-arrow-right">
                        <path d="M5 12h14"/>
                        <path d="m12 5 7 7-7 7"/>
                    </svg>
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="mb-20">
          <h2 class="text-2xl font-bold mb-10 text-center">为什么选择学塔</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
              <div class="h-16 w-16 rounded-full bg-[#3A86FF]/10 flex items-center justify-center mx-auto mb-4">
                <IconAssistant class="h-8 w-8 text-[#3A86FF] "/>
              </div>
              <h3 class="text-xl font-bold mb-2">先进的AI技术</h3>
              <p class="text-slate-600">
                采用最先进的人工智能技术，包括自然语言处理、机器学习和深度学习，为您提供智能化的学习体验。
              </p>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
              <div class="h-16 w-16 rounded-full bg-[#6C5CE7]/10 flex items-center justify-center mx-auto mb-4">
                <IconLogo class="h-8 w-8 text-[#6C5CE7]"/>
              </div>
              <h3 class="text-xl font-bold mb-2">一体化学习平台</h3>
              <p class="text-slate-600">
                集成翻译、答疑、笔记、学习规划等多种功能于一体，打造完整的学习生态系统，满足您的各种学习需求。
              </p>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
              <div class="h-16 w-16 rounded-full bg-[#3A86FF]/10 flex items-center justify-center mx-auto mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check-big-icon lucide-circle-check-big stroke-blue-500 ">
                    <path d="M21.801 10A10 10 0 1 1 17 3.335"/>
                    <path d="m9 11 3 3L22 4"/>
                </svg>
              </div>
              <h3 class="text-xl font-bold mb-2">个性化学习体验</h3>
              <p class="text-slate-600">
                根据您的学习习惯、目标和进度，提供个性化的学习建议和内容推荐，让学习更加高效和有针对性。
              </p>
            </div>
          </div>
        </section>

        <section>
          <Start/>
        </section>
      </main>
    </div>
</template>
<style scoped></style>
