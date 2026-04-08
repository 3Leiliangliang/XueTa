<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import IconDesktop from '@/components/icons/IconDesktop.vue'
import IconTranslate from '@/components/icons/IconTranslate.vue'
import IconQA from '@/components/icons/IconQA.vue'
import IconNotes from '@/components/icons/IconNotes.vue'
import IconPlanning from '@/components/icons/IconPlanning.vue'
import Search from '@/components/search/search.vue'
import { apiRequest } from '@/lib/api'
import { hasAccessToken } from '@/lib/auth'

const router = useRouter()
const LAYOUT_NAME = 'default'
const LOCAL_LAYOUT_KEY = 'xueta_desktop_layout'

const TXT = {
  title: 'AI \u5b66\u4e60\u684c\u9762',
  subtitle: '\u6de1\u8272\u80cc\u666f\u642d\u914d\u84dd\u7d2b\u6e10\u53d8\uff0c\u8ba9\u5b66\u4e60\u684c\u9762\u66f4\u7edf\u4e00\uff0c\u4e5f\u66f4\u7ecf\u5f97\u4f4f\u957f\u65f6\u95f4\u4f7f\u7528\u3002',
  add: '\u6dfb\u52a0',
  addTitle: '\u6dfb\u52a0\u684c\u9762\u9879\u76ee',
  addHint: '\u7ee7\u7eed\u5f80\u684c\u9762\u91cc\u653e\u7f51\u7ad9\u5feb\u6377\u65b9\u5f0f\u548c\u4fe1\u606f\u7ec4\u4ef6\u3002',
  siteGroup: '\u7f51\u7ad9\u5feb\u6377\u65b9\u5f0f',
  widgetGroup: '\u684c\u9762\u7ec4\u4ef6',
  days: '\u5929'
}

const columns = ref(12)
const cellSize = ref(96)
const gapSize = ref(16)
const isDarkMode = ref(false)
const now = ref(new Date())
const authMessage = ref('')
const errorMessage = ref('')
const statusMessage = ref('')
const isHydrating = ref(true)
const showAddMenu = ref(false)
const draggedIndex = ref(null)
const dragOverIndex = ref(null)
const suppressClick = ref(false)

let clockTimer = null
let releaseClickTimer = null
let saveLayoutTimer = null

const createId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`

const siteIcon = (src) => src

const makeApp = (id, name, route, icon, surfaceClass) => ({
  id,
  type: 'app',
  name,
  route,
  icon,
  surfaceClass,
  w: 1,
  h: 1
})

const makeSite = (id, name, url, icon, surfaceClass, iconClass = '', iconType = 'text', category = '') => ({
  id,
  type: 'website',
  name,
  url,
  icon,
  iconType,
  surfaceClass,
  iconClass,
  category,
  w: 1,
  h: 1
})

const makeWidget = (id, widgetType, name, surfaceClass, data = {}, w = 2, h = 2, action = null) => ({
  id,
  type: 'widget',
  widgetType,
  name,
  surfaceClass,
  data,
  action,
  w,
  h
})

const folderApps = [
  { id: 'f-qa', icon: IconQA, color: 'from-[#5B8CFF] to-[#6C5CE7]' },
  { id: 'f-tr', icon: IconTranslate, color: 'from-[#3A86FF] to-[#7C6CF4]' },
  { id: 'f-no', icon: IconNotes, color: 'from-[#7C6CF4] to-[#8B5CF6]' },
  { id: 'f-pl', icon: IconPlanning, color: 'from-[#60A5FA] to-[#6C5CE7]' }
]

const appRegistry = {
  '/translate': {
    id: 'app-translate',
    name: '翻译工坊',
    icon: IconTranslate,
    surfaceClass: 'text-[#3A86FF]'
  },
  '/note': {
    id: 'app-note',
    name: '学习笔记',
    icon: IconNotes,
    surfaceClass: 'text-[#6C5CE7]'
  },
  '/planning': {
    id: 'app-plan',
    name: '学习规划',
    icon: IconPlanning,
    surfaceClass: 'text-[#5B8CFF]'
  },
  '/qa': {
    id: 'app-qa',
    name: '答疑中心',
    icon: IconQA,
    surfaceClass: 'text-[#7B61FF]'
  }
}

const defaultWidgets = () => [
  makeWidget(
    'widget-countdown',
    'countdown',
    '\u5012\u8ba1\u65f6',
    'bg-[linear-gradient(145deg,#ffffff,#eef4ff_58%,#f5efff)] border border-white/80 shadow-[0_18px_50px_rgba(58,134,255,0.14)]',
    {
      title: '\u8ddd\u79bb\u8003\u8bd5',
      targetDate: '2027-02-08',
      subtitle: '2027\u5e74\u6b63\u6708\u521d\u4e00'
    }
  ),
  makeWidget(
    'widget-notes',
    'quickNotes',
    '\u5feb\u6377\u8bb0\u5f55',
    'bg-[linear-gradient(180deg,#ffffff,#f8f7ff)] border border-white/80 shadow-[0_18px_50px_rgba(108,92,231,0.12)]',
    {
      title: '\u5feb\u6377\u8bb0\u5f55',
      items: ['About Movetab...', 'QQ: 1027338110']
    }
  ),
  makeWidget(
    'widget-ai',
    'aiHub',
    'Chat AI',
    'bg-[radial-gradient(circle_at_50%_18%,rgba(58,134,255,0.16),transparent_26%),linear-gradient(160deg,#ffffff,#eef4ff_52%,#f3efff)] border border-white/80 shadow-[0_18px_50px_rgba(58,134,255,0.14)]',
    {},
    2,
    2,
    { kind: 'route', value: '/qa' }
  ),
  makeWidget(
    'widget-folder',
    'appFolder',
    'AI Folder',
    'bg-[linear-gradient(145deg,#ffffff,#f3efff)] border border-white/80 shadow-[0_18px_50px_rgba(108,92,231,0.12)]'
  ),
  makeSite('web-deepseek', 'DeepSeek', 'https://www.deepseek.com', siteIcon('https://www.deepseek.com/favicon.ico'), 'bg-white border border-slate-200/80', '', 'image', 'AI'),
  makeWidget(
    'widget-weather',
    'weather',
    '\u5929\u6c14',
    'bg-[linear-gradient(145deg,#6aa7ff,#6C5CE7)] shadow-[0_18px_50px_rgba(90,110,230,0.24)]',
    { city: '\u671d\u9633', temperature: '22', description: '\u5c0f\u96e8' },
    2,
    1
  ),
  makeSite('web-speed', '\u6d4b\u901f\u7f51', 'https://www.speedtest.cn', siteIcon('https://www.speedtest.cn/favicon.ico'), 'bg-white border border-slate-200/80', '', 'image'),
  makeSite('web-bili', '\u54d4\u54e9\u54d4\u54e9', 'https://www.bilibili.com', siteIcon('https://www.bilibili.com/favicon.ico'), 'bg-[#fce7f3] border border-[#f8cfe0]', '', 'image'),
  makeSite('web-youdao', '\u6709\u9053\u7ffb\u8bd1', 'https://fanyi.youdao.com', siteIcon('https://shared-https.ydstatic.com/images/favicon.ico'), 'bg-[#fff1f2] border border-[#ffd5da]', '', 'image'),
  makeSite('web-red', '\u5c0f\u7ea2\u4e66', 'https://www.xiaohongshu.com', siteIcon('https://www.xiaohongshu.com/favicon.ico'), 'bg-[#fff1f2] border border-[#ffd5da]', '', 'image'),
  makeSite('web-zhihu', '\u77e5\u4e4e', 'https://www.zhihu.com', siteIcon('https://static.zhihu.com/heifetz/favicon.ico'), 'bg-[#eff6ff] border border-[#dbeafe]', '', 'image'),
  makeSite('web-github', 'GitHub', 'https://github.com', siteIcon('https://github.com/favicon.ico'), 'bg-white border border-slate-200/80', '', 'image', '\u4ee3\u7801'),
  makeApp('app-translate', '\u7ffb\u8bd1\u5de5\u574a', '/translate', IconTranslate, 'text-[#3A86FF]'),
  makeApp('app-note', '\u5b66\u4e60\u7b14\u8bb0', '/note', IconNotes, 'text-[#6C5CE7]'),
  makeSite('web-juejin', '\u7a00\u571f\u6398\u91d1', 'https://juejin.cn', siteIcon('https://lf-web-assets.juejin.cn/obj/juejin-web/xitu_juejin_web/static/favicons/favicon.ico'), 'bg-[#eff6ff] border border-[#dbeafe]', '', 'image'),
  makeSite('web-boss', 'BOSS\u76f4\u8058', 'https://www.zhipin.com', siteIcon('https://www.zhipin.com/favicon.ico'), 'bg-[#ecfeff] border border-[#cffafe]', '', 'image'),
  makeWidget('widget-calendar', 'calendar', '\u65e5\u5386', 'bg-[linear-gradient(180deg,#ffffff,#f7f8ff)] border border-white/80 shadow-[0_18px_50px_rgba(108,92,231,0.12)]', {}, 2, 1),
  makeApp('app-plan', '\u5b66\u4e60\u89c4\u5212', '/planning', IconPlanning, 'text-[#5B8CFF]'),
  makeApp('app-qa', '\u7b54\u7591\u4e2d\u5fc3', '/qa', IconQA, 'text-[#7B61FF]')
]

const desktopWidgets = ref(defaultWidgets())

const availableSites = [
  makeSite('site-add-gh', 'GitHub', 'https://github.com', siteIcon('https://github.com/favicon.ico'), 'bg-white border border-slate-200/80', '', 'image', '\u4ee3\u7801'),
  makeSite('site-add-ds', 'DeepSeek', 'https://www.deepseek.com', siteIcon('https://www.deepseek.com/favicon.ico'), 'bg-white border border-slate-200/80', '', 'image', 'AI'),
  makeSite('site-add-zh', '\u77e5\u4e4e', 'https://www.zhihu.com', siteIcon('https://static.zhihu.com/heifetz/favicon.ico'), 'bg-[#eff6ff] border border-[#dbeafe]', '', 'image', '\u77e5\u8bc6'),
  makeSite('site-add-db', '\u8c46\u5305', 'https://www.doubao.com', siteIcon('https://www.doubao.com/favicon.ico'), 'bg-[#eef2ff] border border-[#dbe4ff]', '', 'image', 'AI')
]

const availablePanels = [
  makeWidget('panel-cal', 'calendar', '\u65e5\u5386', 'bg-[linear-gradient(180deg,#ffffff,#f7f8ff)] border border-white/80 shadow-[0_18px_50px_rgba(108,92,231,0.12)]', {}, 2, 1),
  makeWidget('panel-weather', 'weather', '\u5929\u6c14', 'bg-[linear-gradient(145deg,#6aa7ff,#6C5CE7)] shadow-[0_18px_50px_rgba(90,110,230,0.24)]', { city: '\u671d\u9633', temperature: '22', description: '\u5c0f\u96e8' }, 2, 1),
  makeWidget('panel-countdown', 'countdown', '\u5012\u8ba1\u65f6', 'bg-[linear-gradient(145deg,#ffffff,#eef4ff_58%,#f5efff)] border border-white/80 shadow-[0_18px_50px_rgba(58,134,255,0.14)]', { title: '\u8ddd\u79bb\u8003\u8bd5', targetDate: '2027-02-08', subtitle: '2027\u5e74\u6b63\u6708\u521d\u4e00' }),
  makeWidget('panel-notes', 'quickNotes', '\u5feb\u6377\u8bb0\u5f55', 'bg-[linear-gradient(180deg,#ffffff,#f8f7ff)] border border-white/80 shadow-[0_18px_50px_rgba(108,92,231,0.12)]', { title: '\u5feb\u6377\u8bb0\u5f55', items: ['Todo list', 'New idea'] })
]

const hintClass = computed(() => (isDarkMode.value ? 'text-white/70' : 'text-slate-600'))
const panelLabelClass = computed(() => (isDarkMode.value ? 'text-white/92' : 'text-slate-800'))
const shortcutLabelClass = computed(() => (isDarkMode.value ? 'text-white/90' : 'text-slate-700'))
const desktopWidth = computed(() => `${columns.value * cellSize.value + (columns.value - 1) * gapSize.value}px`)

const getLocalLayout = () => {
  if (typeof window === 'undefined') return null
  const raw = window.localStorage.getItem(LOCAL_LAYOUT_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const saveLocalLayout = (widgets) => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(LOCAL_LAYOUT_KEY, JSON.stringify({ widgets }))
}

const hydrateDesktopItem = (item) => {
  if (item.type !== 'app') return { ...item }

  const definition = appRegistry[item.route] || {}
  return {
    ...item,
    id: item.id || definition.id,
    name: item.name || definition.name,
    icon: definition.icon,
    surfaceClass: item.surfaceClass || definition.surfaceClass
  }
}

const serializeDesktopItem = (item) => {
  if (item.type === 'app') {
    return {
      id: item.id,
      type: item.type,
      name: item.name,
      route: item.route,
      surfaceClass: item.surfaceClass,
      w: item.w,
      h: item.h
    }
  }

  if (item.type === 'website') {
    return {
      id: item.id,
      type: item.type,
      name: item.name,
      url: item.url,
      icon: item.icon,
      iconType: item.iconType,
      surfaceClass: item.surfaceClass,
      iconClass: item.iconClass,
      category: item.category,
      w: item.w,
      h: item.h
    }
  }

  return {
    id: item.id,
    type: item.type,
    widgetType: item.widgetType,
    name: item.name,
    surfaceClass: item.surfaceClass,
    data: item.data,
    action: item.action,
    w: item.w,
    h: item.h
  }
}

const applyLayout = (widgets) => {
  desktopWidgets.value = widgets.map(hydrateDesktopItem)
}

const loadDesktopLayout = async () => {
  isHydrating.value = true
  errorMessage.value = ''
  authMessage.value = ''
  statusMessage.value = ''

  try {
    if (hasAccessToken()) {
      const layout = await apiRequest(`/desktop/layout?name=${encodeURIComponent(LAYOUT_NAME)}`)
      const widgets = layout?.layout_json?.widgets
      if (Array.isArray(widgets) && widgets.length) {
        applyLayout(widgets)
        statusMessage.value = '已加载云端桌面布局。'
      } else {
        applyLayout(defaultWidgets())
        statusMessage.value = '云端布局为空，已载入默认桌面。'
      }
    } else {
      const localLayout = getLocalLayout()
      if (Array.isArray(localLayout?.widgets) && localLayout.widgets.length) {
        applyLayout(localLayout.widgets)
      } else {
        applyLayout(defaultWidgets())
      }
      authMessage.value = '当前未登录，桌面布局将保存在本地浏览器。'
    }
  } catch (error) {
    applyLayout(defaultWidgets())
    errorMessage.value = error.message || '加载桌面布局失败，已回退到默认布局。'
  } finally {
    isHydrating.value = false
  }
}

const saveDesktopLayout = async () => {
  const widgets = desktopWidgets.value.map(serializeDesktopItem)

  try {
    if (hasAccessToken()) {
      await apiRequest('/desktop/layout', {
        method: 'PUT',
        body: {
          name: LAYOUT_NAME,
          layout_json: { widgets }
        }
      })
      statusMessage.value = '桌面布局已同步到云端。'
    } else {
      saveLocalLayout(widgets)
      statusMessage.value = '桌面布局已保存到本地。'
    }
  } catch (error) {
    errorMessage.value = error.message || '保存桌面布局失败，请稍后重试。'
  }
}

const updateLayout = () => {
  const width = window.innerWidth
  if (width < 640) {
    columns.value = 4
    cellSize.value = 74
    gapSize.value = 12
    return
  }
  if (width < 1024) {
    columns.value = 8
    cellSize.value = 84
    gapSize.value = 14
    return
  }
  columns.value = 12
  cellSize.value = 96
  gapSize.value = 16
}

const getSurfaceSize = (item) => ({
  width: `${item.w * cellSize.value + (item.w - 1) * gapSize.value}px`,
  height: `${item.h * cellSize.value + (item.h - 1) * gapSize.value}px`
})

const releaseClickLock = () => {
  if (releaseClickTimer) clearTimeout(releaseClickTimer)
  releaseClickTimer = window.setTimeout(() => {
    suppressClick.value = false
  }, 140)
}

const clearDragState = () => {
  draggedIndex.value = null
  dragOverIndex.value = null
  releaseClickLock()
}

const moveWidget = (fromIndex, toIndex) => {
  if (fromIndex === null || toIndex === null || fromIndex === toIndex || fromIndex < 0 || toIndex < 0) return
  const next = [...desktopWidgets.value]
  const [moved] = next.splice(fromIndex, 1)
  next.splice(toIndex, 0, moved)
  desktopWidgets.value = next
}

const createDragPreview = (event) => {
  if (!event.currentTarget) return
  const preview = event.currentTarget.cloneNode(true)
  preview.style.position = 'fixed'
  preview.style.top = '-1000px'
  preview.style.left = '-1000px'
  preview.style.width = `${event.currentTarget.offsetWidth}px`
  preview.style.pointerEvents = 'none'
  preview.classList.add('desktop-drag-preview')
  document.body.appendChild(preview)
  event.dataTransfer.setDragImage(preview, event.currentTarget.offsetWidth / 2, Math.min(72, event.currentTarget.offsetHeight / 2))
  window.setTimeout(() => preview.remove(), 0)
}

const startDrag = (event, index) => {
  draggedIndex.value = index
  dragOverIndex.value = index
  suppressClick.value = true
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', desktopWidgets.value[index].id)
  createDragPreview(event)
}

const handleDragEnter = (index) => {
  if (draggedIndex.value === null || draggedIndex.value === index) return
  moveWidget(draggedIndex.value, index)
  draggedIndex.value = index
  dragOverIndex.value = index
}

const handleDragOver = (event, index) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  if (draggedIndex.value !== null && draggedIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDrop = (event) => {
  event.preventDefault()
  clearDragState()
}

const endDrag = () => {
  clearDragState()
}

const removeWidget = (id) => {
  desktopWidgets.value = desktopWidgets.value.filter((item) => item.id !== id)
}

const openRoute = (route) => {
  if (!suppressClick.value) router.push(route)
}

const openSite = (url) => {
  if (!suppressClick.value) window.open(url, '_blank', 'noopener,noreferrer')
}

const openWidgetAction = (item) => {
  if (!item.action || suppressClick.value) return
  if (item.action.kind === 'route') router.push(item.action.value)
}

const addSite = (item) => {
  desktopWidgets.value.push({ ...item, id: createId('web') })
  showAddMenu.value = false
}

const addPanel = (item) => {
  desktopWidgets.value.push({ ...item, id: createId('widget') })
  showAddMenu.value = false
}

const daysLeft = (targetDate) => {
  const target = new Date(targetDate)
  const current = new Date(now.value)
  target.setHours(0, 0, 0, 0)
  current.setHours(0, 0, 0, 0)
  return Math.max(0, Math.ceil((target.getTime() - current.getTime()) / 86400000))
}

const calendarInfo = computed(() => {
  const week = ['\u5468\u65e5', '\u5468\u4e00', '\u5468\u4e8c', '\u5468\u4e09', '\u5468\u56db', '\u5468\u4e94', '\u5468\u516d']
  return {
    year: now.value.getFullYear(),
    month: now.value.getMonth() + 1,
    day: now.value.getDate(),
    weekday: week[now.value.getDay()]
  }
})

onMounted(() => {
  updateLayout()
  loadDesktopLayout()
  clockTimer = window.setInterval(() => {
    now.value = new Date()
  }, 1000)
  window.addEventListener('resize', updateLayout)
})

watch(
  desktopWidgets,
  () => {
    if (isHydrating.value) return
    clearTimeout(saveLayoutTimer)
    saveLayoutTimer = window.setTimeout(() => {
      saveDesktopLayout()
    }, 600)
  },
  { deep: true }
)

onUnmounted(() => {
  window.removeEventListener('resize', updateLayout)
  if (clockTimer) clearInterval(clockTimer)
  if (releaseClickTimer) clearTimeout(releaseClickTimer)
  if (saveLayoutTimer) clearTimeout(saveLayoutTimer)
})
</script>

<template>
  <div class="desktop-scene relative min-h-screen overflow-hidden bg-gradient-to-b from-slate-50 to-slate-100 text-slate-900 transition-colors duration-500">
    <!-- <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div :class="['absolute left-1/2 top-16 h-[420px] w-[420px] -translate-x-1/2 rounded-full blur-3xl', isDarkMode ? 'bg-fuchsia-500/18' : 'bg-[#b9c8ff]/28']"></div>
      <div :class="['absolute left-[10%] top-[22%] h-[320px] w-[320px] rounded-full blur-3xl', isDarkMode ? 'bg-indigo-500/18' : 'bg-[#d9e4ff]/68']"></div>
      <div :class="['absolute right-[10%] bottom-[14%] h-[340px] w-[340px] rounded-full blur-3xl', isDarkMode ? 'bg-violet-600/14' : 'bg-[#efe7ff]/70']"></div>
      <div class="planet-ring planet-ring-one"></div>
      <div class="planet-ring planet-ring-two"></div>
      <div class="star-tracks"></div>
    </div> -->
    <main class="relative z-10 container mx-auto px-4 md:px-10 lg:px-16 py-8 md:py-10 lg:py-12 space-y-8 md:space-y-10">
      <section class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] flex items-center justify-center shadow-md">
            <IconDesktop class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent">
              {{ TXT.title }}
            </h1>
            <p class="text-sm text-slate-600 mt-1">{{ TXT.subtitle }}</p>
          </div>
        </div>

        <div class="w-full md:max-w-xl lg:max-w-2xl">
          <Search />
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

      

      <section>
        <div class="mx-auto w-full max-w-[1480px]">
          <div class="mx-auto flex flex-wrap justify-center gap-x-6 gap-y-7 md:gap-x-7 md:gap-y-8" :style="{ maxWidth: desktopWidth }">
            <div
              v-for="(item, index) in desktopWidgets"
              :key="item.id"
              draggable="true"
              @dragstart="startDrag($event, index)"
              @dragenter="handleDragEnter(index)"
              @dragover="handleDragOver($event, index)"
              @dragend="endDrag"
              @drop="handleDrop"
              :class="['desktop-tile group relative flex flex-col items-center gap-3', draggedIndex === index ? 'desktop-tile-dragging' : '', dragOverIndex === index && draggedIndex !== index ? 'desktop-tile-over' : '']"
              :style="{ width: getSurfaceSize(item).width }"
            >
              <button type="button" @click="removeWidget(item.id)" :class="['drag-delete-btn absolute right-1 top-0 z-20 flex h-6 w-6 items-center justify-center rounded-full text-xs backdrop-blur transition', isDarkMode ? 'bg-black/50 text-white hover:bg-red-500' : 'bg-white/92 text-slate-500 shadow-sm hover:bg-red-500 hover:text-white']">
                x
              </button>

              <button
                v-if="item.type === 'app'"
                type="button"
                @click="openRoute(item.route)"
                class="desktop-surface desktop-shortcut flex items-center justify-center bg-transparent"
                :style="{ width: `${cellSize}px`, height: `${cellSize}px` }"
              >
                <component :is="item.icon" :class="['h-14 w-14 drop-shadow-[0_10px_22px_rgba(108,92,231,0.16)]', item.surfaceClass]" />
              </button>

              <button
                v-else-if="item.type === 'website'"
                type="button"
                @click="openSite(item.url)"
                class="desktop-surface desktop-shortcut flex items-center justify-center bg-transparent"
                :style="{ width: `${cellSize}px`, height: `${cellSize}px` }"
              >
                <img
                  v-if="item.iconType === 'image'"
                  :src="item.icon"
                  :alt="item.name"
                  class="h-14 w-14 object-contain drop-shadow-[0_10px_18px_rgba(120,132,180,0.16)]"
                  loading="lazy"
                  referrerpolicy="no-referrer"
                />
                <component v-else-if="item.iconType === 'component'" :is="item.icon" class="h-14 w-14" />
                <span v-else :class="['leading-none uppercase', item.iconClass]">{{ item.icon }}</span>
              </button>

              <button
                v-else
                type="button"
                @click="openWidgetAction(item)"
                class="desktop-surface desktop-widget-shell relative overflow-hidden rounded-[26px] text-left"
                :class="[item.surfaceClass, item.action ? 'cursor-pointer' : 'cursor-default']"
                :style="getSurfaceSize(item)"
              >
                <template v-if="item.widgetType === 'countdown'">
                  <div class="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(108,92,231,0.16),transparent_48%)]"></div>
                  <div class="relative flex h-full flex-col justify-between p-5 text-slate-800">
                    <p class="text-[15px] font-semibold tracking-wide text-slate-700">{{ item.data.title }}</p>
                    <div class="flex items-end gap-2">
                      <span class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-[64px] font-semibold leading-none tracking-tight text-transparent">{{ daysLeft(item.data.targetDate) }}</span>
                      <span class="mb-3 rounded-full bg-gradient-to-r from-[#3A86FF]/12 to-[#6C5CE7]/14 px-3 py-1 text-lg font-semibold text-[#556fe8]">{{ TXT.days }}</span>
                    </div>
                    <p class="text-[13px] font-medium text-slate-500">{{ item.data.subtitle }}</p>
                  </div>
                </template>

                <template v-else-if="item.widgetType === 'quickNotes'">
                  <div class="flex h-full flex-col overflow-hidden rounded-[26px]">
                    <div class="flex items-center gap-3 bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] px-4 py-4 text-white">
                      <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-white/95 text-[#4d73eb] shadow-sm">[]</span>
                      <span class="text-[15px] font-semibold">{{ item.data.title }}</span>
                    </div>
                    <div class="flex flex-1 flex-col justify-center px-4 py-3 text-slate-700">
                      <div v-for="note in item.data.items" :key="note" class="flex items-center justify-between border-b border-slate-100 py-3 last:border-b-0">
                        <span class="text-[15px]">{{ note }}</span>
                        <span class="text-base text-slate-300">=</span>
                      </div>
                    </div>
                  </div>
                </template>

                <template v-else-if="item.widgetType === 'aiHub'">
                  <div class="absolute inset-0 opacity-90">
                    <div class="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#6C5CE7]/12 blur-3xl"></div>
                  </div>
                  <div class="relative flex h-full flex-col items-center justify-center gap-5 px-4 text-center text-slate-800">
                    <div class="relative flex h-24 w-24 items-center justify-center">
                      <div class="absolute inset-2 rotate-12 rounded-[26px] border border-[#6C5CE7]/35"></div>
                      <div class="absolute inset-4 -rotate-12 rounded-[22px] border border-[#3A86FF]/35"></div>
                      <div class="h-8 w-8 rounded-full bg-[radial-gradient(circle,#c4d6ff,#6aa7ff_58%,#6C5CE7)] shadow-[0_0_25px_rgba(108,92,231,0.28)]"></div>
                    </div>
                    <div>
                      <p class="bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-[17px] font-semibold tracking-wide text-transparent">Chat AI</p>
                      <p class="mt-1 text-sm text-slate-500">Smart chat, open now</p>
                    </div>
                  </div>
                </template>

                <template v-else-if="item.widgetType === 'appFolder'">
                  <div class="flex h-full flex-col justify-between p-6">
                    <div class="grid grid-cols-2 gap-4">
                      <div v-for="app in folderApps" :key="app.id" class="flex h-[74px] items-center justify-center rounded-[22px] bg-white/82 shadow-[0_10px_24px_rgba(108,92,231,0.08)]">
                        <div class="flex h-14 w-14 items-center justify-center rounded-[18px] bg-gradient-to-br text-white shadow-lg" :class="app.color">
                          <component :is="app.icon" class="h-8 w-8" />
                        </div>
                      </div>
                    </div>
                  </div>
                </template>

                <template v-else-if="item.widgetType === 'weather'">
                  <div class="flex h-full items-center justify-between px-5 text-white">
                    <div>
                      <p class="text-sm font-medium text-white/85">{{ item.data.city }}</p>
                      <p class="mt-1 text-5xl font-semibold leading-none">{{ item.data.temperature }}C</p>
                    </div>
                    <div class="text-right">
                      <div class="text-2xl font-semibold tracking-wide">Rain</div>
                      <p class="mt-1 text-sm text-white/82">{{ item.data.description }}</p>
                    </div>
                  </div>
                </template>

                <template v-else-if="item.widgetType === 'calendar'">
                  <div class="flex h-full">
                    <div class="flex w-[34%] flex-col justify-center bg-gradient-to-b from-[#3A86FF] to-[#6C5CE7] px-3 text-white">
                      <p class="text-xs font-semibold tracking-wide">{{ calendarInfo.year }}</p>
                      <p class="mt-1 text-[28px] font-semibold leading-none">{{ calendarInfo.month }}</p>
                    </div>
                    <div class="flex flex-1 items-center justify-between px-5 text-[#25213a]">
                      <p class="text-[58px] font-semibold leading-none">{{ calendarInfo.day }}</p>
                      <div class="text-right">
                        <p class="text-xl font-semibold">{{ calendarInfo.weekday }}</p>
                        <p class="mt-2 text-sm text-[#6b6476]">{{ calendarInfo.month }}/{{ calendarInfo.day }}</p>
                      </div>
                    </div>
                  </div>
                </template>
              </button>

              <span :class="['max-w-full truncate text-center text-[15px] font-medium tracking-wide', item.type === 'widget' ? panelLabelClass : shortcutLabelClass]">
                {{ item.name }}
              </span>
            </div>

            <button type="button" @click="showAddMenu = true" class="group flex flex-col items-center gap-3" :style="{ width: `${cellSize}px` }">
              <div :class="['desktop-surface flex items-center justify-center rounded-[28px] transition-all duration-300', isDarkMode ? 'bg-white/10 text-white shadow-[0_18px_40px_rgba(0,0,0,0.25)] hover:bg-white/16' : 'border border-dashed border-[#cdd8ff] bg-white/88 text-[#5d6fe7] shadow-[0_18px_40px_rgba(140,150,180,0.18)] hover:border-[#8aa3ff] hover:bg-white']" :style="{ width: `${cellSize}px`, height: `${cellSize}px` }">
                <span class="text-4xl font-light leading-none">+</span>
              </div>
              <span :class="['text-[15px] font-medium tracking-wide', shortcutLabelClass]">{{ TXT.add }}</span>
            </button>
          </div>
        </div>
      </section>
    </main>

    <div v-if="showAddMenu" :class="['fixed inset-0 z-40 flex items-center justify-center px-4 backdrop-blur-sm', isDarkMode ? 'bg-black/28' : 'bg-[#edf2ff]/70']" @click.self="showAddMenu = false">
      <div :class="['w-full max-w-3xl rounded-[30px] border p-6 shadow-2xl md:p-7', isDarkMode ? 'border-white/10 bg-[#1d0b31]/95 text-white' : 'border-[#e5ebff] bg-white/96 text-slate-900 shadow-[0_26px_70px_rgba(108,92,231,0.16)]']">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-xl font-semibold">{{ TXT.addTitle }}</h3>
            <p :class="['mt-1 text-sm', hintClass]">{{ TXT.addHint }}</p>
          </div>
          <button type="button" @click="showAddMenu = false" :class="['flex h-10 w-10 items-center justify-center rounded-full transition', isDarkMode ? 'bg-white/10 hover:bg-white/16' : 'bg-slate-100 hover:bg-[#eef2ff]']">
            x
          </button>
        </div>

        <div class="mt-8 grid gap-8 lg:grid-cols-[1.2fr_1fr]">
          <div>
            <h4 :class="['mb-4 text-sm font-semibold uppercase tracking-[0.24em]', hintClass]">{{ TXT.siteGroup }}</h4>
            <div class="grid grid-cols-2 gap-3">
              <button v-for="site in availableSites" :key="site.id" type="button" @click="addSite(site)" :class="['flex items-center gap-3 rounded-[22px] border p-3 text-left transition-all duration-300 hover:-translate-y-1', isDarkMode ? 'border-white/10 bg-white/5 hover:bg-white/10' : 'border-[#e6ebff] bg-[#fbfcff] hover:shadow-[0_12px_30px_rgba(108,92,231,0.12)]']">
                <div class="flex h-14 w-14 items-center justify-center rounded-[18px] text-white shadow-lg" :class="site.surfaceClass">
                  <img
                    v-if="site.iconType === 'image'"
                    :src="site.icon"
                    :alt="site.name"
                    class="h-8 w-8 rounded-lg object-contain"
                    loading="lazy"
                    referrerpolicy="no-referrer"
                  />
                  <component v-else-if="site.iconType === 'component'" :is="site.icon" class="h-7 w-7" />
                  <span v-else :class="site.iconClass">{{ site.icon }}</span>
                </div>
                <div>
                  <p class="text-sm font-semibold">{{ site.name }}</p>
                  <p :class="['mt-1 text-xs', hintClass]">{{ site.category }}</p>
                </div>
              </button>
            </div>
          </div>

          <div>
            <h4 :class="['mb-4 text-sm font-semibold uppercase tracking-[0.24em]', hintClass]">{{ TXT.widgetGroup }}</h4>
            <div class="grid gap-3">
              <button v-for="panel in availablePanels" :key="panel.id" type="button" @click="addPanel(panel)" :class="['rounded-[22px] border p-4 text-left transition-all duration-300 hover:-translate-y-1', isDarkMode ? 'border-white/10 bg-white/5 hover:bg-white/10' : 'border-[#e6ebff] bg-[#fbfcff] hover:shadow-[0_12px_30px_rgba(108,92,231,0.12)]']">
                <p class="text-sm font-semibold">{{ panel.name }}</p>
                <p :class="['mt-1 text-xs', hintClass]">{{ panel.w }} x {{ panel.h }} panel</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.desktop-scene {
  background-image:
    radial-gradient(circle at top, rgba(58, 134, 255, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.7), rgba(243, 246, 255, 0.92));
}

.planet-ring {
  position: absolute;
  left: 50%;
  top: 54%;
  border-radius: 999px;
  transform: translate(-50%, -50%) rotate(-24deg);
  pointer-events: none;
}

.planet-ring-one {
  width: 960px;
  height: 420px;
  border: 20px solid rgba(108, 92, 231, 0.08);
}

.planet-ring-two {
  width: 760px;
  height: 320px;
  border: 12px solid rgba(58, 134, 255, 0.08);
}

.star-tracks {
  position: absolute;
  inset: 0;
  opacity: 0.38;
  background-image:
    radial-gradient(circle at 8% 24%, rgba(58, 134, 255, 0.18) 0 1px, transparent 1px),
    radial-gradient(circle at 18% 66%, rgba(108, 92, 231, 0.12) 0 1px, transparent 1px),
    radial-gradient(circle at 42% 20%, rgba(58, 134, 255, 0.16) 0 1px, transparent 1px),
    radial-gradient(circle at 60% 54%, rgba(108, 92, 231, 0.14) 0 1px, transparent 1px),
    radial-gradient(circle at 76% 30%, rgba(58, 134, 255, 0.12) 0 1px, transparent 1px),
    radial-gradient(circle at 88% 70%, rgba(108, 92, 231, 0.16) 0 1px, transparent 1px);
  background-size: 260px 160px, 220px 180px, 280px 200px, 240px 180px, 260px 180px, 280px 220px;
}

.desktop-tile {
  user-select: none;
}

.desktop-surface {
  transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease, opacity 180ms ease;
  will-change: transform;
}

.desktop-shortcut:hover,
.desktop-widget-shell:hover {
  transform: translateY(-4px);
  filter: saturate(1.04);
}

.desktop-tile-dragging .desktop-surface {
  opacity: 0.42;
  transform: scale(0.95) rotate(-1.25deg);
  box-shadow: none;
}

.desktop-tile-over .desktop-surface {
  transform: translateY(-2px) scale(1.02);
}

.desktop-widget-shell {
  backdrop-filter: blur(16px);
}

.drag-delete-btn {
  opacity: 0;
  transform: translateY(2px);
}

.group:hover .drag-delete-btn {
  opacity: 1;
  transform: translateY(0);
}

.desktop-drag-preview {
  transform: scale(0.98);
  opacity: 0.94;
}

[draggable='true'] {
  cursor: grab;
}

[draggable='true']:active {
  cursor: grabbing;
}

@media (max-width: 767px) {
  .planet-ring-one {
    width: 620px;
    height: 280px;
    border-width: 18px;
  }

  .planet-ring-two {
    width: 470px;
    height: 220px;
    border-width: 12px;
  }
}
</style>
