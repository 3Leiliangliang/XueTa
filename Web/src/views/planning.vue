<script setup>
import { computed, onMounted, ref } from 'vue'
import IconPlanning from '@/components/icons/IconPlanning.vue'
import Input from '@/components/ui/input.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const currentDate = ref(new Date())
const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isLoading = ref(false)
const isGenerating = ref(false)
const taskFilter = ref('全部')

const currentWeek = computed(() => {
  const date = new Date(currentDate.value)
  const day = date.getDay()
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  const monday = new Date(date.setDate(diff))
  const week = []
  for (let i = 0; i < 7; i += 1) {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    week.push(d)
  }
  return week
})

const learningGoals = ref([])
const tasks = ref([])

const goalColorPalette = [
  'from-[#3A86FF] to-[#6C5CE7]',
  'from-[#6C5CE7] to-[#9333EA]',
  'from-[#9333EA] to-[#F472B6]',
  'from-[#F472B6] to-[#0EA5E9]'
]

const goalStatusMap = {
  active: 'in-progress',
  completed: 'completed',
  archived: 'archived'
}

const plannerTaskStatusMap = {
  pending: 'pending',
  completed: 'completed',
  skipped: 'skipped'
}

const normalizeGoal = (goal) => ({
  id: goal.id,
  title: goal.title,
  description: goal.description || '',
  subject: goal.subject || '',
  progress: goal.progress ?? 0,
  deadline: goal.deadline || '',
  status: goalStatusMap[goal.status] || goal.status,
  color: goal.color || goalColorPalette[0]
})

const normalizeTask = (task) => ({
  id: task.id,
  goalId: task.goal_id,
  title: task.title,
  description: task.description || '',
  date: task.task_date || '',
  time: task.task_time ? task.task_time.slice(0, 5) : '',
  duration: task.duration_minutes ?? 60,
  priority: task.priority || 'medium',
  status: plannerTaskStatusMap[task.status] || task.status
})

const filteredTasks = computed(() => {
  if (taskFilter.value === '待完成') {
    return tasks.value.filter((task) => task.status !== 'completed')
  }
  if (taskFilter.value === '已完成') {
    return tasks.value.filter((task) => task.status === 'completed')
  }
  return tasks.value
})

const stats = computed(() => {
  const total = tasks.value.length
  const completed = tasks.value.filter((task) => task.status === 'completed').length
  const todayTasks = tasks.value.filter((task) => {
    if (!task.date) return false
    const taskDate = new Date(task.date).toDateString()
    const today = new Date().toDateString()
    return taskDate === today
  })
  const todayCompleted = todayTasks.filter((task) => task.status === 'completed').length

  const totalDuration = tasks.value.reduce((sum, task) => sum + (task.duration || 0), 0)
  const completedDuration = tasks.value
    .filter((task) => task.status === 'completed')
    .reduce((sum, task) => sum + (task.duration || 0), 0)

  return {
    total,
    completed,
    completionRate: total > 0 ? Math.round((completed / total) * 100) : 0,
    todayTotal: todayTasks.length,
    todayCompleted,
    totalDuration,
    completedDuration,
    remainingDuration: totalDuration - completedDuration
  }
})

const getTasksByDate = (date) => {
  const dateStr = date.toISOString().split('T')[0]
  return tasks.value.filter((task) => task.date === dateStr)
}

const showAddTask = ref(false)
const newTask = ref({
  title: '',
  goalId: null,
  date: new Date().toISOString().split('T')[0],
  time: '10:00',
  duration: 60,
  priority: 'medium'
})

const resetTaskForm = () => {
  newTask.value = {
    title: '',
    goalId: null,
    date: new Date().toISOString().split('T')[0],
    time: '10:00',
    duration: 60,
    priority: 'medium'
  }
}

const showAddGoal = ref(false)
const newGoal = ref({
  title: '',
  deadline: '',
  color: goalColorPalette[0]
})

const resetGoalForm = () => {
  newGoal.value = {
    title: '',
    deadline: '',
    color: goalColorPalette[0]
  }
}

const getPriorityColor = (priority) => {
  const colors = {
    high: 'bg-red-100 text-red-700 border-red-200',
    medium: 'bg-amber-100 text-amber-700 border-amber-200',
    low: 'bg-slate-100 text-slate-700 border-slate-200'
  }
  return colors[priority] || colors.medium
}

const formatDate = (date) => date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })

const isToday = (date) => {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const changeWeek = (direction) => {
  const date = new Date(currentDate.value)
  date.setDate(date.getDate() + direction * 7)
  currentDate.value = date
}

const loadPlannerData = async () => {
  if (!hasAccessToken()) {
    authMessage.value = '请先登录后再使用 AI 学习规划。'
    learningGoals.value = []
    tasks.value = []
    return
  }

  isLoading.value = true
  authMessage.value = ''
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const [goals, plannerTasks] = await Promise.all([
      apiRequest('/planner/goals'),
      apiRequest('/planner/tasks')
    ])
    learningGoals.value = goals.map(normalizeGoal)
    tasks.value = plannerTasks.map(normalizeTask)
  } catch (error) {
    errorMessage.value = error.message || '加载学习规划失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const toggleTaskStatus = async (taskId) => {
  const task = tasks.value.find((item) => item.id === taskId)
  if (!task) return

  const previousStatus = task.status
  const nextStatus = previousStatus === 'completed' ? 'pending' : 'completed'
  task.status = nextStatus

  try {
    const updated = await apiRequest(`/planner/tasks/${taskId}/status`, {
      method: 'PATCH',
      body: { status: nextStatus }
    })
    Object.assign(task, normalizeTask(updated))
  } catch (error) {
    task.status = previousStatus
    errorMessage.value = error.message || '更新任务状态失败，请稍后重试。'
  }
}

const addTask = async () => {
  if (!newTask.value.title.trim()) return

  try {
    const created = await apiRequest('/planner/tasks', {
      method: 'POST',
      body: {
        goal_id: newTask.value.goalId || null,
        title: newTask.value.title.trim(),
        task_date: newTask.value.date || null,
        task_time: newTask.value.time || null,
        duration_minutes: Number(newTask.value.duration) || 60,
        priority: newTask.value.priority
      }
    })
    tasks.value.push(normalizeTask(created))
    resetTaskForm()
    showAddTask.value = false
    statusMessage.value = '任务已创建。'
  } catch (error) {
    errorMessage.value = error.message || '创建任务失败，请稍后重试。'
  }
}

const addGoal = async () => {
  if (!newGoal.value.title.trim() || !newGoal.value.deadline) return

  try {
    const created = await apiRequest('/planner/goals', {
      method: 'POST',
      body: {
        title: newGoal.value.title.trim(),
        deadline: newGoal.value.deadline,
        color: newGoal.value.color
      }
    })
    learningGoals.value.unshift(normalizeGoal(created))
    resetGoalForm()
    showAddGoal.value = false
    statusMessage.value = '学习目标已创建。'
  } catch (error) {
    errorMessage.value = error.message || '创建学习目标失败，请稍后重试。'
  }
}

const generatePlan = async () => {
  if (!learningGoals.value.length) {
    errorMessage.value = '请先创建至少一个学习目标，再生成 AI 计划。'
    return
  }

  isGenerating.value = true
  errorMessage.value = ''

  try {
    const snapshot = await apiRequest('/planner/generate', {
      method: 'POST',
      body: {
        goal_ids: learningGoals.value
          .filter((goal) => goal.status !== 'archived')
          .map((goal) => goal.id),
        days: 7,
        daily_minutes: 120
      }
    })
    await loadPlannerData()

    const persistedTaskCount = snapshot.plan_json?.persisted_task_count ?? 0
    const reusedTaskCount = snapshot.plan_json?.reused_existing_ai_task_count ?? 0
    const replacedTaskCount = snapshot.plan_json?.replaced_pending_ai_task_count ?? 0

    statusMessage.value = [
      `AI 计划已正式写入任务列表：新增 ${persistedTaskCount} 个任务。`,
      reusedTaskCount ? `复用 ${reusedTaskCount} 个已完成/已跳过的 AI 任务。` : '',
      replacedTaskCount ? `替换 ${replacedTaskCount} 个旧的待完成 AI 任务。` : ''
    ]
      .filter(Boolean)
      .join('')
  } catch (error) {
    errorMessage.value = error.message || 'AI 生成计划失败，请稍后重试。'
  } finally {
    isGenerating.value = false
  }
}

onMounted(() => {
  loadPlannerData()
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
    <main
      class="container mx-auto px-4 md:px-10 lg:px-16 py-8 md:py-10 lg:py-12 space-y-8 md:space-y-10"
    >
      <section class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] flex items-center justify-center shadow-md"
          >
            <IconPlanning class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1
              class="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent"
            >
              AI 学习规划
            </h1>
            <p class="text-sm text-slate-600 mt-1">
              AI 智能规划，让学习更有条理
            </p>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <button
            @click="generatePlan"
            class="px-4 py-2 rounded-lg border border-[#3A86FF] bg-white text-sm font-medium text-[#3A86FF] hover:bg-blue-50 transition-colors disabled:opacity-60"
            :disabled="isGenerating"
          >
            {{ isGenerating ? 'AI 生成中...' : 'AI 生成计划' }}
          </button>
          <button
            @click="showAddGoal = true"
            class="px-4 py-2 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors"
          >
            + 新建目标
          </button>
          <button
            @click="showAddTask = true"
            class="px-4 py-2 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white text-sm font-medium hover:opacity-90 transition-opacity"
          >
            + 添加任务
          </button>
        </div>
      </section>

      <section v-if="authMessage || errorMessage || statusMessage" class="space-y-3">
        <p
          v-if="authMessage"
          class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700"
        >
          {{ authMessage }}
        </p>
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
      </section>

      <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-600">总任务数</span>
            <div class="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
              <span class="text-blue-600 text-xs">📋</span>
            </div>
          </div>
          <p class="text-2xl font-bold text-slate-900">{{ stats.total }}</p>
          <p class="text-xs text-slate-500 mt-1">已完成 {{ stats.completed }} 个</p>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-600">完成率</span>
            <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
              <span class="text-emerald-600 text-xs">✓</span>
            </div>
          </div>
          <p class="text-2xl font-bold text-slate-900">{{ stats.completionRate }}%</p>
          <div class="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] transition-all"
              :style="{ width: `${stats.completionRate}%` }"
            ></div>
          </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-600">今日任务</span>
            <div class="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
              <span class="text-amber-600 text-xs">📅</span>
            </div>
          </div>
          <p class="text-2xl font-bold text-slate-900">
            {{ stats.todayCompleted }}/{{ stats.todayTotal }}
          </p>
          <p class="text-xs text-slate-500 mt-1">今日完成情况</p>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-600">学习时长</span>
            <div class="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
              <span class="text-purple-600 text-xs">⏱️</span>
            </div>
          </div>
          <p class="text-2xl font-bold text-slate-900">{{ Math.round(stats.completedDuration / 60) }}h</p>
          <p class="text-xs text-slate-500 mt-1">剩余 {{ Math.round(stats.remainingDuration / 60) }}h</p>
        </div>
      </section>

      <section class="grid lg:grid-cols-3 gap-6">
        <div class="lg:col-span-1 space-y-4">
          <h2 class="text-lg font-semibold text-slate-900">学习目标</h2>
          <div class="space-y-3">
            <div
              v-for="goal in learningGoals"
              :key="goal.id"
              class="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow"
            >
              <div class="flex items-start justify-between mb-3 gap-3">
                <h3 class="text-sm font-semibold text-slate-900 flex-1">{{ goal.title }}</h3>
                <span class="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                  {{ goal.deadline || '未设置' }}
                </span>
              </div>
              <div class="mb-2">
                <div class="flex items-center justify-between text-xs text-slate-600 mb-1">
                  <span>进度</span>
                  <span>{{ goal.progress }}%</span>
                </div>
                <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-gradient-to-r transition-all"
                    :class="goal.color"
                    :style="{ width: `${goal.progress}%` }"
                  ></div>
                </div>
              </div>
            </div>
            <p v-if="!learningGoals.length && !isLoading" class="text-sm text-slate-400">
              当前还没有学习目标，先创建一个目标再开始规划吧。
            </p>
          </div>
        </div>

        <div class="lg:col-span-2 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-slate-900">本周计划</h2>
            <div class="flex items-center gap-2">
              <button
                @click="changeWeek(-1)"
                class="w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-600"
              >
                ←
              </button>
              <span class="text-sm text-slate-700 px-3">
                {{ formatDate(currentWeek[0]) }} - {{ formatDate(currentWeek[6]) }}
              </span>
              <button
                @click="changeWeek(1)"
                class="w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-center text-slate-600"
              >
                →
              </button>
            </div>
          </div>

          <div class="grid grid-cols-7 gap-2">
            <div
              v-for="(date, index) in currentWeek"
              :key="index"
              :class="[
                'bg-white rounded-xl border-2 p-3 min-h-[200px]',
                isToday(date) ? 'border-[#3A86FF] shadow-md' : 'border-slate-200'
              ]"
            >
              <div class="mb-2">
                <p
                  :class="[
                    'text-xs font-medium mb-1',
                    isToday(date) ? 'text-[#3A86FF]' : 'text-slate-500'
                  ]"
                >
                  {{ ['日', '一', '二', '三', '四', '五', '六'][index] }}
                </p>
                <p
                  :class="[
                    'text-lg font-semibold',
                    isToday(date) ? 'text-[#3A86FF]' : 'text-slate-900'
                  ]"
                >
                  {{ date.getDate() }}
                </p>
              </div>
              <div class="space-y-1.5">
                <div
                  v-for="task in getTasksByDate(date)"
                  :key="task.id"
                  @click="toggleTaskStatus(task.id)"
                  :class="[
                    'text-xs p-2 rounded-lg cursor-pointer transition-all border',
                    task.status === 'completed'
                      ? 'bg-slate-50 border-slate-200 line-through text-slate-400'
                      : 'bg-white border-slate-200 hover:border-[#3A86FF] hover:bg-blue-50',
                    getPriorityColor(task.priority)
                  ]"
                >
                  <div class="flex items-center gap-1 mb-0.5">
                    <input
                      type="checkbox"
                      :checked="task.status === 'completed'"
                      @click.stop
                      @change="toggleTaskStatus(task.id)"
                      class="w-3 h-3 rounded"
                    />
                    <span class="font-medium">{{ task.title }}</span>
                  </div>
                  <div class="text-[10px] text-slate-500">
                    {{ task.time || '待定' }} · {{ task.duration }}分钟
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-900">全部任务</h2>
          <div class="flex items-center gap-2">
            <button
              v-for="filter in ['全部', '待完成', '已完成']"
              :key="filter"
              :class="[
                'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
                taskFilter === filter
                  ? 'bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
              ]"
              @click="taskFilter = filter"
            >
              {{ filter }}
            </button>
          </div>
        </div>

        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="divide-y divide-slate-100">
            <div
              v-for="task in filteredTasks"
              :key="task.id"
              @click="toggleTaskStatus(task.id)"
              :class="[
                'p-4 cursor-pointer transition-colors hover:bg-slate-50',
                task.status === 'completed' ? 'bg-slate-50/50' : ''
              ]"
            >
              <div class="flex items-start gap-3">
                <input
                  type="checkbox"
                  :checked="task.status === 'completed'"
                  @click.stop
                  @change="toggleTaskStatus(task.id)"
                  class="mt-1 w-4 h-4 rounded border-slate-300"
                />
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <h3
                      :class="[
                        'text-sm font-medium',
                        task.status === 'completed'
                          ? 'text-slate-400 line-through'
                          : 'text-slate-900'
                      ]"
                    >
                      {{ task.title }}
                    </h3>
                    <span
                      :class="[
                        'text-[10px] px-2 py-0.5 rounded-full border',
                        getPriorityColor(task.priority)
                      ]"
                    >
                      {{ task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低' }}
                    </span>
                  </div>
                  <div class="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                    <span>{{ task.date || '未设置日期' }}</span>
                    <span>{{ task.time || '待定' }}</span>
                    <span>{{ task.duration }} 分钟</span>
                    <span
                      v-if="learningGoals.find((goal) => goal.id === task.goalId)"
                      class="px-2 py-0.5 rounded bg-slate-100"
                    >
                      {{ learningGoals.find((goal) => goal.id === task.goalId)?.title }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <p v-if="!filteredTasks.length" class="px-4 py-6 text-sm text-slate-400">
              当前筛选条件下还没有任务。
            </p>
          </div>
        </div>
      </section>
    </main>

    <div
      v-if="showAddTask"
      @click.self="showAddTask = false"
      class="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full border border-slate-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-900">添加任务</h3>
          <button
            @click="showAddTask = false"
            class="text-slate-400 hover:text-slate-600 text-xl"
          >
            ×
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium text-slate-700 mb-1 block">任务名称</label>
            <Input v-model="newTask.title" placeholder="输入任务名称" class="w-full" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-slate-700 mb-1 block">日期</label>
              <Input v-model="newTask.date" type="date" class="w-full" />
            </div>
            <div>
              <label class="text-sm font-medium text-slate-700 mb-1 block">时间</label>
              <Input v-model="newTask.time" type="time" class="w-full" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-slate-700 mb-1 block">预计时长（分钟）</label>
              <Input v-model.number="newTask.duration" type="number" class="w-full" />
            </div>
            <div>
              <label class="text-sm font-medium text-slate-700 mb-1 block">优先级</label>
              <select
                v-model="newTask.priority"
                class="w-full h-10 rounded-md border border-slate-200 px-3 text-sm"
              >
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
              </select>
            </div>
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700 mb-1 block">关联目标</label>
            <select
              v-model="newTask.goalId"
              class="w-full h-10 rounded-md border border-slate-200 px-3 text-sm"
            >
              <option :value="null">无</option>
              <option
                v-for="goal in learningGoals"
                :key="goal.id"
                :value="goal.id"
              >
                {{ goal.title }}
              </option>
            </select>
          </div>
          <div class="flex gap-3 pt-2">
            <button
              @click="showAddTask = false"
              class="flex-1 px-4 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              取消
            </button>
            <button
              @click="addTask"
              class="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white hover:opacity-90 transition-opacity"
            >
              添加
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="showAddGoal"
      @click.self="showAddGoal = false"
      class="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl p-6 max-w-md w-full border border-slate-200">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-900">新建学习目标</h3>
          <button
            @click="showAddGoal = false"
            class="text-slate-400 hover:text-slate-600 text-xl"
          >
            ×
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium text-slate-700 mb-1 block">目标名称</label>
            <Input v-model="newGoal.title" placeholder="输入学习目标" class="w-full" />
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700 mb-1 block">截止日期</label>
            <Input v-model="newGoal.deadline" type="date" class="w-full" />
          </div>
          <div>
            <label class="text-sm font-medium text-slate-700 mb-1 block">主题颜色</label>
            <div class="grid grid-cols-4 gap-2">
              <button
                v-for="color in goalColorPalette"
                :key="color"
                @click="newGoal.color = color"
                :class="[
                  'h-10 rounded-lg bg-gradient-to-r border-2 transition-all',
                  color,
                  newGoal.color === color
                    ? 'border-slate-900 scale-105'
                    : 'border-transparent'
                ]"
              ></button>
            </div>
          </div>
          <div class="flex gap-3 pt-2">
            <button
              @click="showAddGoal = false"
              class="flex-1 px-4 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
            >
              取消
            </button>
            <button
              @click="addGoal"
              class="flex-1 px-4 py-2 rounded-lg bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] text-white hover:opacity-90 transition-opacity"
            >
              创建
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
