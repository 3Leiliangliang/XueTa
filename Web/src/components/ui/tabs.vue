<script setup>
import { provide, ref, computed } from 'vue'

const props = defineProps({
  defaultValue: {
    type: String,
    default: ''
  },
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const activeTab = ref(props.modelValue || props.defaultValue)

const setActiveTab = (value) => {
  activeTab.value = value
  emit('update:modelValue', value)
}

provide('tabs', {
  activeTab: computed(() => activeTab.value),
  setActiveTab
})
</script>

<template>
  <div class="w-full">
    <slot />
  </div>
</template>
