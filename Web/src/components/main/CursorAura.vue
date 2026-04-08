<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

const isVisible = ref(false)
const isEnabled = ref(false)

const target = reactive({
  x: 0,
  y: 0
})

const motion = reactive({
  x: 0,
  y: 0
})

let frameId = 0
let mediaQueryList = null
let reducedMotionList = null

const updateSupport = () => {
  const finePointer = mediaQueryList?.matches ?? true
  const reducedMotion = reducedMotionList?.matches ?? false
  isEnabled.value = finePointer && !reducedMotion
}

const handlePointerMove = (event) => {
  target.x = event.clientX
  target.y = event.clientY
  isVisible.value = true
}

const handlePointerLeave = () => {
  isVisible.value = false
}

const animate = () => {
  motion.x += (target.x - motion.x) * 0.13
  motion.y += (target.y - motion.y) * 0.13
  frameId = window.requestAnimationFrame(animate)
}

const primaryStyle = computed(() => ({
  transform: `translate3d(${(motion.x - 140).toFixed(2)}px, ${(motion.y - 140).toFixed(2)}px, 0)`
}))

const secondaryStyle = computed(() => ({
  transform: `translate3d(${(motion.x - 94 + 28).toFixed(2)}px, ${(motion.y - 94 - 14).toFixed(2)}px, 0)`
}))

const coreStyle = computed(() => ({
  transform: `translate3d(${(motion.x - 48 - 12).toFixed(2)}px, ${(motion.y - 48 + 8).toFixed(2)}px, 0)`
}))

const sheenStyle = computed(() => ({
  transform: `translate3d(${(motion.x - 72 + 10).toFixed(2)}px, ${(motion.y - 52 - 18).toFixed(2)}px, 0)`
}))

onMounted(() => {
  mediaQueryList = window.matchMedia('(pointer: fine)')
  reducedMotionList = window.matchMedia('(prefers-reduced-motion: reduce)')
  updateSupport()

  mediaQueryList.addEventListener('change', updateSupport)
  reducedMotionList.addEventListener('change', updateSupport)

  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('pointerleave', handlePointerLeave)
  window.addEventListener('blur', handlePointerLeave)

  frameId = window.requestAnimationFrame(animate)
})

onBeforeUnmount(() => {
  mediaQueryList?.removeEventListener('change', updateSupport)
  reducedMotionList?.removeEventListener('change', updateSupport)
  window.removeEventListener('pointermove', handlePointerMove)
  window.removeEventListener('pointerleave', handlePointerLeave)
  window.removeEventListener('blur', handlePointerLeave)
  window.cancelAnimationFrame(frameId)
})
</script>

<template>
  <div
    v-if="isEnabled"
    class="cursor-aura-layer pointer-events-none fixed inset-0 z-[12] overflow-hidden"
    :class="isVisible ? 'opacity-100' : 'opacity-0'"
  >
    <div class="cursor-aura cursor-aura--primary" :style="primaryStyle"></div>
    <div class="cursor-aura cursor-aura--secondary" :style="secondaryStyle"></div>
    <div class="cursor-aura cursor-aura--core" :style="coreStyle"></div>
    <div class="cursor-aura cursor-aura--sheen" :style="sheenStyle"></div>
  </div>
</template>

<style scoped>
.cursor-aura {
  position: absolute;
  border-radius: 9999px;
  will-change: transform, opacity;
}

.cursor-aura--primary {
  width: 250px;
  height: 250px;
  background:
    radial-gradient(circle at center, rgba(117, 128, 231, 0.11) 0%, rgba(117, 128, 231, 0.045) 28%, rgba(117, 128, 231, 0) 64%);
  filter: blur(24px);
  mix-blend-mode: multiply;
  opacity: 0.82;
}

.cursor-aura--secondary {
  width: 156px;
  height: 156px;
  background:
    radial-gradient(circle at center, rgba(138, 174, 255, 0.14) 0%, rgba(138, 174, 255, 0.05) 34%, rgba(138, 174, 255, 0) 70%);
  filter: blur(16px);
  mix-blend-mode: soft-light;
  opacity: 0.86;
}

.cursor-aura--core {
  width: 72px;
  height: 72px;
  background:
    radial-gradient(circle at center, rgba(255, 255, 255, 0.13) 0%, rgba(209, 223, 255, 0.08) 34%, rgba(209, 223, 255, 0) 72%);
  filter: blur(8px);
  mix-blend-mode: soft-light;
  opacity: 0.9;
}

.cursor-aura--sheen {
  width: 124px;
  height: 86px;
  background:
    radial-gradient(ellipse at center, rgba(255, 255, 255, 0.14) 0%, rgba(255, 255, 255, 0.06) 38%, rgba(255, 255, 255, 0) 74%);
  filter: blur(14px);
  mix-blend-mode: soft-light;
  opacity: 0.78;
}

.cursor-aura-layer {
  transition: opacity 260ms ease;
}
</style>
