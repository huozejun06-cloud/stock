<template>
  <!-- ★ 买/观望/卖 信号标签：纯 CSS 类切换 -->
  <span :class="badgeClass">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ type: { type: String, default: 'watch' } })
const badgeClass = computed(() => ({
  'badge-buy': props.type === 'buy',
  'badge-watch': props.type === 'watch',
  'badge-sell': props.type === 'sell',
}))
</script>
