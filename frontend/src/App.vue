<template>
  <NavBar />
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
import { onMounted, onUnmounted, watch, nextTick } from 'vue'
import NavBar from '@/components/layout/NavBar.vue'
import { useRouter } from 'vue-router'
import Lenis from 'lenis'

let lenis = null

const router = useRouter()
watch(() => router.currentRoute.value, () => {
  nextTick(() => {
    window.scrollTo(0, 0)
    if (lenis) lenis.scrollTo(0, { immediate: true, force: true })
  })
})

onMounted(() => {
  lenis = new Lenis({
    duration: 1.2,
    lerp: 0.08,
    smoothWheel: true,
  })

  function raf(time) {
    lenis.raf(time)
    requestAnimationFrame(raf)
  }
  requestAnimationFrame(raf)
})

onUnmounted(() => {
  if (lenis) lenis.destroy()
})
</script>

<style>
.page-enter-active, .page-leave-active {
  transition: opacity 0.12s ease;
}
.page-enter-from, .page-leave-to {
  opacity: 0;
}
</style>
