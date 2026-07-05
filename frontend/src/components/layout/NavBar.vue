<template>
  <div class="fixed top-0 left-0 right-0 z-50 flex justify-center pointer-events-none" style="padding-top: 22px">
    <nav
      class="pointer-events-auto flex items-center justify-between transition-all duration-300"
      :style="navStyle"
    >
      <!-- Logo -->
      <router-link to="/" class="flex flex-col items-start leading-none shrink-0 mr-6">
        <span class="text-lg font-semibold tracking-wide" style="color: var(--text-primary); font-family: var(--font-hero)">洞见</span>
        <span class="text-xs tracking-widest" style="color: var(--text-dim); font-family: var(--font-number)">INSIGHT</span>
      </router-link>

      <!-- 6 independent pill buttons, evenly distributed -->
      <div class="flex items-center gap-3">
        <router-link
          v-for="item in links"
          :key="item.path"
          :to="item.path"
          class="nav-pill"
          :class="{ 'nav-pill-active': $route.path === item.path }"
        >{{ item.label }}</router-link>
      </div>

      <!-- CTA (hidden on Landing) -->
      <CtaButton v-if="!isLanding" class="text-sm ml-4" style="height:38px;padding:0 20px;font-size:13px" @click="handleCta">
        开始体验
      </CtaButton>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CtaButton from '@/components/ui/CtaButton.vue'

const route = useRoute()
const router = useRouter()
const scrolled = ref(false)
const isLanding = computed(() => route.path === '/')

const links = [
  { path: '/overview', label: '市场全景' },
  { path: '/scanner', label: '机会扫描' },
  { path: '/research/600519', label: '深度研究' },
  { path: '/backtest', label: '策略验证' },
  { path: '/methodology', label: '研究方法' },
  { path: '/about', label: '关于洞见' },
]

const navStyle = computed(() => {
  const base = 'width:min(1160px, calc(100vw - 48px)); height:64px; border-radius:999px; padding:0 24px; '
  if (!isLanding.value || scrolled.value) {
    return base + 'background:rgba(18,22,32,.45); backdrop-filter:blur(26px) saturate(180%) brightness(110%); -webkit-backdrop-filter:blur(26px) saturate(180%) brightness(110%); border:1px solid rgba(255,255,255,.08); box-shadow:0 20px 60px rgba(0,0,0,.35);'
  }
  return base + 'background:transparent;'
})

const handleCta = () => {
  if (isLanding.value) {
    sessionStorage.setItem('visited', 'true')
    router.push('/overview')
  } else {
    router.push('/')
  }
}

const onScroll = () => { scrolled.value = window.scrollY > 60 }
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.nav-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 18px;
  font-size: 14px;
  font-family: var(--font-body);
  color: rgba(255,255,255,.7);
  background: rgba(255,255,255,.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 999px;
  transition: all 300ms ease;
  text-decoration: none;
  white-space: nowrap;
}
.nav-pill:hover {
  background: rgba(255,255,255,.1);
  color: #fff;
  border-color: rgba(255,255,255,.12);
  transform: translateY(-1px);
}
.nav-pill-active {
  background: rgba(255,255,255,.12);
  color: #fff;
  border-color: rgba(255,255,255,.15);
}
</style>
