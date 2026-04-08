<script setup>
import { computed, ref, onUnmounted } from 'vue'

const props = defineProps({
    type:{
        type: String,
        default: 'normal',
        validator: (value) => ['normal', 'danger'].includes(value)//validator 是 Vue props 的一个验证器函数，用于验证传入的 prop 值是否有效。
    },
    // 默认状态文字
    defaultText: {
        type: String,
        default: ''
    },
    
    // 加载状态文字
    loadingText: {
        type: String,
        default: ''
    },
    
    // 加载持续时间（毫秒）
    loadingDuration: {
        type: Number,
        default: 1000
    },
})


const emit = defineEmits(['click'])

// 加载状态
const isLoading = ref(false)

//按钮style控制
const buttonClass = computed(() => {
    const base = 'w-full py-2 font-medium rounded-lg  hover:cursor-pointer'
    const types = {
        color: 'bg-gradient-to-r from-[#3A86FF] to-[#6C5CE7]  focus:ring-blue-500',
        normal: 'bg-white  hover:bg-white/90 '
    }
    // 加载状态样式
    const loadingStyle = isLoading.value ? 'opacity-90 scale-[0.98] hover:cursor-wait' : 'hover:scale-[1.02] active:scale-[0.98]'
    return `${base} ${types[props.type]} ${loadingStyle}`
})

const handleClick = async (event) => {
  if (isLoading.value) return
  
  // 切换为加载状态
  isLoading.value = true
  
  // 触发点击事件
  emit('click', event)
  
  // 1秒后恢复
  setTimeout(() => {
    isLoading.value = false
  }, props.loadingDuration)
}

</script>
<template>
    <button 
    :class="buttonClass" 
    @click="handleClick"
    :disabled="isLoading">
     <slot>
        {{ isLoading ? loadingText : defaultText }}
     </slot>
         
    </button>
</template>
<style scoped></style>