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
</script>

<template>
  <div v-if="isActive" class="mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2">
    <slot />
  </div>
</template>
