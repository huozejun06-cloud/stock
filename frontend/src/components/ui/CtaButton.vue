<template>
  <!-- ★ 呼吸灯按钮：支持 orange / purple 双色 -->
  <button
    class="cta-btn"
    :class="color === 'purple' ? 'cta-purple' : 'cta-orange'"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  color: { type: String, default: 'orange' }
})
defineEmits(['click'])
</script>
