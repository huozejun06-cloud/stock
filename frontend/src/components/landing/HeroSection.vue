<template>
  <section ref="heroRef" class="relative w-full h-screen overflow-hidden" style="background: var(--color-bg)">
    <video autoplay muted loop playsinline class="absolute inset-0 w-full h-full object-cover" style="filter: brightness(.45) contrast(1.05) saturate(1.15)">
      <source :src="videoSrc" type="video/mp4" />
    </video>
    <div class="absolute inset-0" style="background: linear-gradient(180deg, rgba(6,10,18,.30) 0%, rgba(8,12,20,.55) 50%, rgba(5,8,15,.72) 100%)" />
    <div class="noise-overlay" />
    <div class="absolute inset-0 pointer-events-none" style="background: radial-gradient(ellipse at 50% 40%, rgba(108,140,255,.06) 0%, transparent 60%)" />

    <div class="absolute inset-0 z-10">

      <!-- Line 0: centered, upper half -->
      <p
        ref="l0"
        class="absolute left-1/2 text-center leading-tight whitespace-nowrap text-transparent bg-gradient-to-b from-white to-gray-500 bg-clip-text pointer-events-none"
        style="top: 28%; transform: translateX(-50%); font-family: var(--font-hero); font-size: clamp(48px, 6vw, 86px); font-weight: 400; opacity: 0"
      >先看风险，再看机会。</p>

      <!-- Lines 1-4: all at top-left, same size, sequential fade in/out -->
      <p
        ref="l1"
        class="absolute top-[15%] left-[8%] max-w-[600px] text-left leading-tight pointer-events-none"
        style="opacity: 0; font-family: var(--font-hero); font-size: clamp(32px, 4vw, 56px); font-weight: 400; color: var(--text-primary)"
      >有人寻找机会，有人验证机会。</p>

      <p
        ref="l2"
        class="absolute top-[15%] left-[8%] max-w-[600px] text-left leading-tight pointer-events-none"
        style="opacity: 0; font-family: var(--font-hero); font-size: clamp(32px, 4vw, 56px); font-weight: 400; color: var(--text-primary)"
      >不懂股票，也能读懂一家公司。</p>

      <p
        ref="l3"
        class="absolute top-[15%] left-[8%] max-w-[600px] text-left leading-tight pointer-events-none"
        style="opacity: 0; font-family: var(--font-hero); font-size: clamp(32px, 4vw, 56px); font-weight: 400; color: var(--text-primary)"
      >不是替你决策，而是解释为什么。</p>

      <p
        ref="l4"
        class="absolute top-[15%] left-[8%] max-w-[600px] text-left leading-tight pointer-events-none"
        style="opacity: 0; font-family: var(--font-hero); font-size: clamp(32px, 4vw, 56px); font-weight: 400; color: var(--text-primary)"
      >AI 不会替代投资者，它会放大你的判断。</p>

      <!-- Bottom group -->
      <div ref="bottomGroup" class="absolute bottom-[10%] left-1/2 flex flex-col items-center" style="transform: translateX(-50%); opacity: 0; pointer-events: none">
        <p class="text-lg md:text-xl text-center max-w-2xl leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body)">
          不是预测市场，而是帮助理解市场。
        </p>
        <div class="flex items-center gap-4 mt-6">
          <CtaButton color="orange" @click="handleEnter">开始体验</CtaButton>
          <CtaButton color="purple" @click="handleMethodology">了解方法</CtaButton>
        </div>
      </div>

      <p ref="scrollHint" class="absolute bottom-6 left-1/2 tracking-widest text-sm" style="transform: translateX(-50%); color: var(--text-dim); opacity: 1; font-family: var(--font-body)">向下滚动</p>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import CtaButton from '@/components/ui/CtaButton.vue'

gsap.registerPlugin(ScrollTrigger)

const router = useRouter()
const heroRef = ref(null)
const l0 = ref(null); const l1 = ref(null); const l2 = ref(null); const l3 = ref(null); const l4 = ref(null)
const bottomGroup = ref(null)
const scrollHint = ref(null)
const videoSrc = '/video/hero-bg.mp4'

let st = null

onMounted(async () => {
  await nextTick()
  if (!heroRef.value || !bottomGroup.value || !scrollHint.value) return
  if (!l0.value || !l1.value || !l2.value || !l3.value || !l4.value) return

  gsap.set(bottomGroup.value, { opacity: 0, pointerEvents: 'none' })
  gsap.set([l1.value, l2.value, l3.value, l4.value], { opacity: 0 })

  const tl = gsap.timeline({
    scrollTrigger: { trigger: heroRef.value, pin: true, scrub: 1.2, end: '+=2500' },
  })

  tl.to(scrollHint.value, { opacity: 0, duration: 0.2 }, 0)

  // Line 0: centered upper half -> fade in then out
  tl.fromTo(l0.value, { opacity: 0, y: 40, scale: 0.96, filter: 'blur(8px)' }, { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'power4.out' })
  tl.to(l0.value, { opacity: 0, y: -20, duration: 0.3 })

  // Lines 1-4: top-left, sequential fade in/out (same focal point rotation)
  tl.fromTo(l1.value, { opacity: 0, y: 40, filter: 'blur(6px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4, ease: 'power3.out' })
  tl.to(l1.value, { opacity: 0, y: -20, duration: 0.25 })

  tl.fromTo(l2.value, { opacity: 0, y: 40, filter: 'blur(6px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4, ease: 'power3.out' })
  tl.to(l2.value, { opacity: 0, y: -20, duration: 0.25 })

  tl.fromTo(l3.value, { opacity: 0, y: 40, filter: 'blur(6px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4, ease: 'power3.out' })
  tl.to(l3.value, { opacity: 0, y: -20, duration: 0.25 })

  tl.fromTo(l4.value, { opacity: 0, y: 40, filter: 'blur(6px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4, ease: 'power3.out' })
  tl.to(l4.value, { opacity: 0, y: -20, duration: 0.25 })

  tl.to(bottomGroup.value, { opacity: 1, pointerEvents: 'auto', duration: 1.2, ease: 'power2.out' })

  st = tl.scrollTrigger
})

onUnmounted(() => { if (st) st.kill(); ScrollTrigger.getAll().forEach(t => t.kill()) })

const handleEnter = () => { sessionStorage.setItem('visited', 'true'); router.push('/overview') }
const handleMethodology = () => { const el = document.getElementById('methodology'); if (el) el.scrollIntoView({ behavior: 'smooth' }) }
</script>
