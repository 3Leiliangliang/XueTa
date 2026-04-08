<script setup>
const props = defineProps({
  name: {
    type: String,
    required: true,
    validator: (value) => ['mail', 'lock', 'phone', 'eye', 'eye-off'].includes(value)
  },
  class: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <svg
    v-if="name === 'mail'"
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :class="class"
  >
    <rect width="20" height="16" x="2" y="4" rx="2" />
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
  </svg>

  <svg
    v-else-if="name === 'lock'"
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :class="class"
  >
    <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>

  <svg
    v-else-if="name === 'phone'"
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :class="class"
  >
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
  </svg>

  <svg
    v-else-if="name === 'eye'"
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :class="class"
  >
    <path d="M2.06 12.32a1 1 0 0 1 0-.64 10.97 10.97 0 0 1 19.88 0 1 1 0 0 1 0 .64 10.97 10.97 0 0 1-19.88 0" />
    <circle cx="12" cy="12" r="3" />
  </svg>

  <svg
    v-else-if="name === 'eye-off'"
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    :class="class"
  >
    <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c4.39 0 8.06 2.5 9.6 6.11a1.3 1.3 0 0 1 0 1.78 11.4 11.4 0 0 1-2.17 3.19" />
    <path d="M6.61 6.61A11.46 11.46 0 0 0 2.4 11.11a1.3 1.3 0 0 0 0 1.78C3.98 15.7 7.6 19 12 19c1.94 0 3.73-.5 5.27-1.38" />
    <path d="m2 2 20 20" />
    <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
  </svg>
</template>
