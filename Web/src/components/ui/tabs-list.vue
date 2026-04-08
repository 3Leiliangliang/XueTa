<script setup>
import { computed, useAttrs } from 'vue'

const attrs = useAttrs()
const listClass = computed(() => {
  const base = 'inline-flex h-10 items-center justify-center rounded-lg bg-gray-200 p-1 text-slate-500'
  const customClass = attrs.class || ''
  return `${base} ${customClass}`
})
</script>

<template>
  <div :class="listClass">
    <slot />
  </div>
</template>
