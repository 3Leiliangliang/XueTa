<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  size: {
    type: Number,
    default: 48
  },
  pupilSize: {
    type: Number,
    default: 16
  },
  maxDistance: {
    type: Number,
    default: 10
  },
  eyeColor: {
    type: String,
    default: '#ffffff'
  },
  pupilColor: {
    type: String,
    default: '#000000'
  },
  isBlinking: {
    type: Boolean,
    default: false
  },
  forceLookX: {
    type: Number,
    default: undefined
  },
  forceLookY: {
    type: Number,
    default: undefined
  }
})

const mouseX = ref(0)
const mouseY = ref(0)
const eyeRef = ref(null)

const handlePointerMove = (event) => {
  mouseX.value = event.clientX
  mouseY.value = event.clientY
}

const position = computed(() => {
  if (props.forceLookX !== undefined && props.forceLookY !== undefined) {
    return {
      x: props.forceLookX,
      y: props.forceLookY
    }
  }

  if (!eyeRef.value) {
    return { x: 0, y: 0 }
  }

  const eye = eyeRef.value.getBoundingClientRect()
  const eyeCenterX = eye.left + eye.width / 2
  const eyeCenterY = eye.top + eye.height / 2
  const deltaX = mouseX.value - eyeCenterX
  const deltaY = mouseY.value - eyeCenterY
  const distance = Math.min(Math.hypot(deltaX, deltaY), props.maxDistance)
  const angle = Math.atan2(deltaY, deltaX)

  return {
    x: Math.cos(angle) * distance,
    y: Math.sin(angle) * distance
  }
})

const eyeStyle = computed(() => ({
  width: `${props.size}px`,
  height: props.isBlinking ? '2px' : `${props.size}px`,
  backgroundColor: props.eyeColor,
  overflow: 'hidden'
}))

const pupilStyle = computed(() => ({
  width: `${props.pupilSize}px`,
  height: `${props.pupilSize}px`,
  backgroundColor: props.pupilColor,
  transform: `translate(${position.value.x}px, ${position.value.y}px)`,
  transition: 'transform 0.1s ease-out'
}))

onMounted(() => {
  mouseX.value = window.innerWidth / 2
  mouseY.value = window.innerHeight / 2
  window.addEventListener('pointermove', handlePointerMove)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', handlePointerMove)
})
</script>

<template>
  <div
    ref="eyeRef"
    class="flex items-center justify-center rounded-full transition-all duration-150"
    :style="eyeStyle"
  >
    <div v-if="!isBlinking" class="rounded-full" :style="pupilStyle"></div>
  </div>
</template>
