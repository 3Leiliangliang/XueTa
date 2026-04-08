<script setup>
import { computed } from 'vue'

const props = defineProps({
  id: {
    type: String,
    default: ''
  },
  modelValue: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const handleChange = (event) => {
  emit('update:modelValue', event.target.checked)
}
</script>

<template>
  <div class="flex items-center space-x-2">
    <input
      :id="id"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      class="peer h-4 w-4 shrink-0 rounded-sm border border-slate-300 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-slate-900 data-[state=checked]:text-slate-50"
      @change="handleChange"
    />
  </div>
</template>
