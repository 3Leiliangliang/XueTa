<script setup>
defineOptions({
  inheritAttrs: true
})

defineProps({
  colorSVG: {
    type: String,
    default: 'text-[#3A86FF]'
  },
  colorText: {
    type: String,
    default: 'bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7] bg-clip-text text-transparent'
  },
  text: {
    type: String,
    default: '学塔'
  },
  showText: {
    type: Boolean,
    default: true
  }
})
</script>

<template>
  <div class="flex items-center gap-2">
    <svg
      class="h-8 w-8 lucide lucide-layers"
      :class="colorSVG"
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z" />
      <path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12" />
      <path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17" />
    </svg>
    <div v-if="showText" class="text-xl font-bold" :class="colorText">
      {{ text }}
    </div>
  </div>
</template>
