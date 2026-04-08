<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import MascotEyeBall from '@/components/auth/MascotEyeBall.vue'
import MascotPupil from '@/components/auth/MascotPupil.vue'

const props = defineProps({
  typingActive: {
    type: Boolean,
    default: false
  },
  typingPulse: {
    type: Number,
    default: 0
  },
  hasPasswordValue: {
    type: Boolean,
    default: false
  },
  passwordVisible: {
    type: Boolean,
    default: false
  },
  scale: {
    type: Number,
    default: 1
  }
})

const mouseX = ref(0)
const mouseY = ref(0)
const isPurpleBlinking = ref(false)
const isBlackBlinking = ref(false)
const isLookingAtEachOther = ref(false)
const isPurplePeeking = ref(false)

const purpleRef = ref(null)
const blackRef = ref(null)
const yellowRef = ref(null)
const orangeRef = ref(null)

let lookTimer = 0
let purpleBlinkTimer = 0
let purpleBlinkResetTimer = 0
let blackBlinkTimer = 0
let blackBlinkResetTimer = 0
let purplePeekTimer = 0
let purplePeekResetTimer = 0

const sceneWidth = 550
const sceneHeight = 400

const hiddenPasswordMode = computed(() => props.hasPasswordValue && !props.passwordVisible)
const visiblePasswordMode = computed(() => props.hasPasswordValue && props.passwordVisible)
const leanMode = computed(() => props.typingActive || hiddenPasswordMode.value)

const handlePointerMove = (event) => {
  mouseX.value = event.clientX
  mouseY.value = event.clientY
}

const getRandomBlinkInterval = () => Math.random() * 4000 + 3000
const getRandomPeekInterval = () => Math.random() * 3000 + 2000

const clearPurpleBlinkTimers = () => {
  window.clearTimeout(purpleBlinkTimer)
  window.clearTimeout(purpleBlinkResetTimer)
}

const clearBlackBlinkTimers = () => {
  window.clearTimeout(blackBlinkTimer)
  window.clearTimeout(blackBlinkResetTimer)
}

const clearPurplePeekTimers = () => {
  window.clearTimeout(purplePeekTimer)
  window.clearTimeout(purplePeekResetTimer)
}

const schedulePurpleBlink = () => {
  clearPurpleBlinkTimers()
  purpleBlinkTimer = window.setTimeout(() => {
    isPurpleBlinking.value = true
    purpleBlinkResetTimer = window.setTimeout(() => {
      isPurpleBlinking.value = false
      schedulePurpleBlink()
    }, 150)
  }, getRandomBlinkInterval())
}

const scheduleBlackBlink = () => {
  clearBlackBlinkTimers()
  blackBlinkTimer = window.setTimeout(() => {
    isBlackBlinking.value = true
    blackBlinkResetTimer = window.setTimeout(() => {
      isBlackBlinking.value = false
      scheduleBlackBlink()
    }, 150)
  }, getRandomBlinkInterval())
}

const schedulePurplePeek = () => {
  clearPurplePeekTimers()

  if (!visiblePasswordMode.value) {
    isPurplePeeking.value = false
    return
  }

  purplePeekTimer = window.setTimeout(() => {
    isPurplePeeking.value = true
    purplePeekResetTimer = window.setTimeout(() => {
      isPurplePeeking.value = false
      schedulePurplePeek()
    }, 800)
  }, getRandomPeekInterval())
}

const calculatePosition = (element) => {
  if (!element) {
    return { faceX: 0, faceY: 0, bodySkew: 0 }
  }

  const rect = element.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 3
  const deltaX = mouseX.value - centerX
  const deltaY = mouseY.value - centerY

  return {
    faceX: Math.max(-15, Math.min(15, deltaX / 20)),
    faceY: Math.max(-10, Math.min(10, deltaY / 30)),
    bodySkew: Math.max(-6, Math.min(6, -deltaX / 120))
  }
}

const purplePos = computed(() => calculatePosition(purpleRef.value))
const blackPos = computed(() => calculatePosition(blackRef.value))
const yellowPos = computed(() => calculatePosition(yellowRef.value))
const orangePos = computed(() => calculatePosition(orangeRef.value))

const containerStyle = computed(() => ({
  width: `${sceneWidth * props.scale}px`,
  height: `${sceneHeight * props.scale}px`
}))

const sceneStyle = computed(() => ({
  width: `${sceneWidth}px`,
  height: `${sceneHeight}px`,
  transform: `scale(${props.scale})`,
  transformOrigin: 'top left'
}))

const purpleBodyStyle = computed(() => ({
  left: '70px',
  width: '180px',
  height: leanMode.value ? '440px' : '400px',
  backgroundColor: '#6C3FF5',
  borderRadius: '10px 10px 0 0',
  zIndex: 1,
  transform: visiblePasswordMode.value
    ? 'skewX(0deg)'
    : leanMode.value
      ? `skewX(${(purplePos.value.bodySkew || 0) - 12}deg) translateX(40px)`
      : `skewX(${purplePos.value.bodySkew || 0}deg)`,
  transformOrigin: 'bottom center'
}))

const purpleEyesStyle = computed(() => ({
  left: visiblePasswordMode.value
    ? '20px'
    : isLookingAtEachOther.value
      ? '55px'
      : `${45 + purplePos.value.faceX}px`,
  top: visiblePasswordMode.value
    ? '35px'
    : isLookingAtEachOther.value
      ? '65px'
      : `${40 + purplePos.value.faceY}px`
}))

const purpleForceLook = computed(() => {
  if (visiblePasswordMode.value) {
    return {
      x: isPurplePeeking.value ? 4 : -4,
      y: isPurplePeeking.value ? 5 : -4
    }
  }

  if (isLookingAtEachOther.value) {
    return { x: 3, y: 4 }
  }

  return undefined
})

const blackBodyStyle = computed(() => ({
  left: '240px',
  width: '120px',
  height: '310px',
  backgroundColor: '#2D2D2D',
  borderRadius: '8px 8px 0 0',
  zIndex: 2,
  transform: visiblePasswordMode.value
    ? 'skewX(0deg)'
    : isLookingAtEachOther.value
      ? `skewX(${(blackPos.value.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
      : leanMode.value
        ? `skewX(${(blackPos.value.bodySkew || 0) * 1.5}deg)`
        : `skewX(${blackPos.value.bodySkew || 0}deg)`,
  transformOrigin: 'bottom center'
}))

const blackEyesStyle = computed(() => ({
  left: visiblePasswordMode.value
    ? '10px'
    : isLookingAtEachOther.value
      ? '32px'
      : `${26 + blackPos.value.faceX}px`,
  top: visiblePasswordMode.value
    ? '28px'
    : isLookingAtEachOther.value
      ? '12px'
      : `${32 + blackPos.value.faceY}px`
}))

const blackForceLook = computed(() => {
  if (visiblePasswordMode.value) {
    return { x: -4, y: -4 }
  }

  if (isLookingAtEachOther.value) {
    return { x: 0, y: -4 }
  }

  return undefined
})

const orangeBodyStyle = computed(() => ({
  left: '0px',
  width: '240px',
  height: '200px',
  zIndex: 3,
  backgroundColor: '#FF9B6B',
  borderRadius: '120px 120px 0 0',
  transform: visiblePasswordMode.value
    ? 'skewX(0deg)'
    : `skewX(${orangePos.value.bodySkew || 0}deg)`,
  transformOrigin: 'bottom center'
}))

const orangeFaceStyle = computed(() => ({
  left: visiblePasswordMode.value ? '50px' : `${82 + orangePos.value.faceX}px`,
  top: visiblePasswordMode.value ? '85px' : `${90 + orangePos.value.faceY}px`
}))

const yellowBodyStyle = computed(() => ({
  left: '310px',
  width: '140px',
  height: '230px',
  backgroundColor: '#E8D754',
  borderRadius: '70px 70px 0 0',
  zIndex: 4,
  transform: visiblePasswordMode.value
    ? 'skewX(0deg)'
    : `skewX(${yellowPos.value.bodySkew || 0}deg)`,
  transformOrigin: 'bottom center'
}))

const yellowEyesStyle = computed(() => ({
  left: visiblePasswordMode.value ? '20px' : `${52 + yellowPos.value.faceX}px`,
  top: visiblePasswordMode.value ? '35px' : `${40 + yellowPos.value.faceY}px`
}))

const yellowMouthStyle = computed(() => ({
  left: visiblePasswordMode.value ? '10px' : `${40 + yellowPos.value.faceX}px`,
  top: visiblePasswordMode.value ? '88px' : `${88 + yellowPos.value.faceY}px`
}))

watch(
  () => props.typingPulse,
  (value, previousValue) => {
    if (value === previousValue || !props.typingActive) {
      return
    }

    isLookingAtEachOther.value = true
    window.clearTimeout(lookTimer)
    lookTimer = window.setTimeout(() => {
      isLookingAtEachOther.value = false
    }, 800)
  }
)

watch(
  () => props.typingActive,
  (active) => {
    if (!active) {
      window.clearTimeout(lookTimer)
      isLookingAtEachOther.value = false
    }
  }
)

watch(
  visiblePasswordMode,
  (active) => {
    if (!active) {
      clearPurplePeekTimers()
      isPurplePeeking.value = false
      return
    }

    schedulePurplePeek()
  },
  { immediate: true }
)

onMounted(() => {
  mouseX.value = window.innerWidth / 2
  mouseY.value = window.innerHeight / 2
  schedulePurpleBlink()
  scheduleBlackBlink()
  window.addEventListener('pointermove', handlePointerMove)
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', handlePointerMove)
  window.clearTimeout(lookTimer)
  clearPurpleBlinkTimers()
  clearBlackBlinkTimers()
  clearPurplePeekTimers()
})
</script>

<template>
  <div class="relative mx-auto" :style="containerStyle">
    <div class="absolute left-0 top-0" :style="sceneStyle">
      <div class="relative h-full w-full">
        <div
          ref="purpleRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="purpleBodyStyle"
        >
          <div
            class="absolute flex gap-8 transition-all duration-700 ease-in-out"
            :style="purpleEyesStyle"
          >
            <MascotEyeBall
              :size="18"
              :pupil-size="7"
              :max-distance="5"
              eye-color="white"
              pupil-color="#2D2D2D"
              :is-blinking="isPurpleBlinking"
              :force-look-x="purpleForceLook?.x"
              :force-look-y="purpleForceLook?.y"
            />
            <MascotEyeBall
              :size="18"
              :pupil-size="7"
              :max-distance="5"
              eye-color="white"
              pupil-color="#2D2D2D"
              :is-blinking="isPurpleBlinking"
              :force-look-x="purpleForceLook?.x"
              :force-look-y="purpleForceLook?.y"
            />
          </div>
        </div>

        <div
          ref="blackRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="blackBodyStyle"
        >
          <div
            class="absolute flex gap-6 transition-all duration-700 ease-in-out"
            :style="blackEyesStyle"
          >
            <MascotEyeBall
              :size="16"
              :pupil-size="6"
              :max-distance="4"
              eye-color="white"
              pupil-color="#2D2D2D"
              :is-blinking="isBlackBlinking"
              :force-look-x="blackForceLook?.x"
              :force-look-y="blackForceLook?.y"
            />
            <MascotEyeBall
              :size="16"
              :pupil-size="6"
              :max-distance="4"
              eye-color="white"
              pupil-color="#2D2D2D"
              :is-blinking="isBlackBlinking"
              :force-look-x="blackForceLook?.x"
              :force-look-y="blackForceLook?.y"
            />
          </div>
        </div>

        <div
          ref="orangeRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="orangeBodyStyle"
        >
          <div
            class="absolute flex gap-8 transition-all duration-200 ease-out"
            :style="orangeFaceStyle"
          >
            <MascotPupil
              :size="12"
              :max-distance="5"
              pupil-color="#2D2D2D"
              :force-look-x="visiblePasswordMode ? -5 : undefined"
              :force-look-y="visiblePasswordMode ? -4 : undefined"
            />
            <MascotPupil
              :size="12"
              :max-distance="5"
              pupil-color="#2D2D2D"
              :force-look-x="visiblePasswordMode ? -5 : undefined"
              :force-look-y="visiblePasswordMode ? -4 : undefined"
            />
          </div>
        </div>

        <div
          ref="yellowRef"
          class="absolute bottom-0 transition-all duration-700 ease-in-out"
          :style="yellowBodyStyle"
        >
          <div
            class="absolute flex gap-6 transition-all duration-200 ease-out"
            :style="yellowEyesStyle"
          >
            <MascotPupil
              :size="12"
              :max-distance="5"
              pupil-color="#2D2D2D"
              :force-look-x="visiblePasswordMode ? -5 : undefined"
              :force-look-y="visiblePasswordMode ? -4 : undefined"
            />
            <MascotPupil
              :size="12"
              :max-distance="5"
              pupil-color="#2D2D2D"
              :force-look-x="visiblePasswordMode ? -5 : undefined"
              :force-look-y="visiblePasswordMode ? -4 : undefined"
            />
          </div>
          <div
            class="absolute h-[4px] w-20 rounded-full bg-[#2D2D2D] transition-all duration-200 ease-out"
            :style="yellowMouthStyle"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
