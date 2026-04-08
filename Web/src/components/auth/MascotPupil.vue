<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  size: {
    type: Number,
    default: 12
  },
  maxDistance: {
    type: Number,
    default: 5
  },
  pupilColor: {
    type: String,
    default: '#000000'
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
const pupilRef = ref(null)

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

  if (!pupilRef.value) {
    return { x: 0, y: 0 }
  }

  const pupil = pupilRef.value.getBoundingClientRect()
  const pupilCenterX = pupil.left + pupil.width / 2
  const pupilCenterY = pupil.top + pupil.height / 2
  const deltaX = mouseX.value - pupilCenterX
  const deltaY = mouseY.value - pupilCenterY
  const distance = Math.min(Math.hypot(deltaX, deltaY), props.maxDistance)
  const angle = Math.atan2(deltaY, deltaX)

  return {
    x: Math.cos(angle) * distance,
    y: Math.sin(angle) * distance
  }
})

const pupilStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
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
  <div ref="pupilRef" class="rounded-full" :style="pupilStyle"></div>
</template>
