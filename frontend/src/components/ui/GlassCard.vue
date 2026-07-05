<template>
  <!-- ★ 兼顾毛玻璃+rgba兜底：class走Tailwind，样式走CSS变量 -->
  <div
    class="glass-card p-4"
    :class="[hoverable ? 'cursor-pointer hover:-translate-y-0.5' : '']"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({ hoverable: { type: Boolean, default: true } })
</script>

<style scoped>
/* 所有毛玻璃样式在 main.css 的 .glass-card 中定义 */
/* 双保险：rgba(17,19,24,0.8) + backdrop-blur(12px) */
</style>
