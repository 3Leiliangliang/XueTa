import { computed, reactive, ref, watch } from 'vue'

export function useAuthMascot(options = {}) {
  const fieldNames = options.fieldNames?.length ? options.fieldNames : ['password']
  const typingFieldNames = options.typingFieldNames ?? []
  const passwordRefs = options.passwordRefs ?? []
  const enabled = options.enabled ?? computed(() => true)

  const passwordHover = reactive(
    Object.fromEntries(fieldNames.map((name) => [name, false]))
  )

  const passwordFocus = reactive(
    Object.fromEntries(fieldNames.map((name) => [name, false]))
  )

  const passwordVisible = reactive(
    Object.fromEntries(fieldNames.map((name) => [name, false]))
  )

  const typingFocus = reactive(
    Object.fromEntries(typingFieldNames.map((name) => [name, false]))
  )

  const typingPulse = ref(0)

  const setPasswordHover = (name, value) => {
    if (name in passwordHover) {
      passwordHover[name] = value
    }
  }

  const setPasswordFocus = (name, value) => {
    if (name in passwordFocus) {
      passwordFocus[name] = value
    }
  }

  const setTypingFocus = (name, value) => {
    if (!(name in typingFocus)) {
      return
    }

    const previousValue = typingFocus[name]
    typingFocus[name] = value

    if (enabled.value && value && !previousValue) {
      typingPulse.value += 1
    }
  }

  const togglePasswordVisibility = (name) => {
    if (name in passwordVisible) {
      passwordVisible[name] = !passwordVisible[name]
    }
  }

  const resetMascot = () => {
    fieldNames.forEach((name) => {
      passwordHover[name] = false
      passwordFocus[name] = false
      passwordVisible[name] = false
    })

    typingFieldNames.forEach((name) => {
      typingFocus[name] = false
    })
  }

  const hasPasswordValue = computed(() => {
    if (!enabled.value) {
      return false
    }

    return passwordRefs.some((fieldRef) => String(fieldRef?.value ?? '').length > 0)
  })

  const isPasswordVisible = computed(() => {
    if (!enabled.value) {
      return false
    }

    return Object.values(passwordVisible).some(Boolean)
  })

  const isTypingActive = computed(() => {
    if (!enabled.value) {
      return false
    }

    return Object.values(typingFocus).some(Boolean)
  })

  watch(enabled, (value) => {
    if (!value) {
      resetMascot()
    }
  })

  return {
    hasPasswordValue,
    isPasswordVisible,
    isTypingActive,
    passwordFocus,
    passwordHover,
    passwordVisible,
    setPasswordFocus,
    setPasswordHover,
    setTypingFocus,
    togglePasswordVisibility,
    typingPulse,
    resetMascot
  }
}
