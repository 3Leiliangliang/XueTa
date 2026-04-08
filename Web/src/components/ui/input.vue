<script setup>
import { computed, useAttrs } from 'vue'

const props = defineProps({
  id: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  modelValue: {
    type: [String, Number],
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  autoCapitalize: {
    type: String,
    default: 'off'
  },
  autoComplete: {
    type: String,
    default: 'off'
  },
  autoCorrect: {
    type: String,
    default: 'off'
  }
})

const emit = defineEmits(['update:modelValue'])
const attrs = useAttrs()

const inputClass = computed(() => {
  const base = 'flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3A86FF] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'
  const customClass = attrs.class || ''
  return `${base} ${customClass}`
})

const handleInput = (event) => {
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <input
    :id="id"
    :type="type"
    :placeholder="placeholder"
    :value="modelValue"
    :disabled="disabled"
    :autocapitalize="autoCapitalize"
    :autocomplete="autoComplete"
    :autocorrect="autoCorrect"
    :class="inputClass"
    @input="handleInput"
  />
</template>
