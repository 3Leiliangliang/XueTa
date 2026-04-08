<script setup>
import { inject, computed } from 'vue'

const props = defineProps({
  value: {
    type: String,
    required: true
  }
})

const tabs = inject('tabs')

const isActive = computed(() => tabs.activeTab.value === props.value)

const handleClick = () => {
  tabs.setActiveTab(props.value)
}

const triggerClass = computed(() => {
  const base = 'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-outline-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 '
  return isActive.value
    ? base + 'bg-white text-slate-950 shadow-sm '
    : base + 'text-slate-500 hover:text-slate-950'
})
</script>

<template>
  <button
    :class="triggerClass"
    @click="handleClick"
    type="button"
  >
    <slot />
  </button>
</template>
