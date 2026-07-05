<template>
  <section ref="sectionRef" class="py-[var(--space-section)]" style="background: var(--color-bg)">
    <div class="mx-auto px-6" style="max-width: var(--space-container)">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div ref="textCol" class="lg:col-span-5">
          <h2 class="text-4xl md:text-5xl font-normal leading-tight mb-6" style="font-family: var(--font-hero); color: var(--text-primary); opacity: 0">
            真正重要的，<br />不是预测涨跌。<br />而是理解为什么。
          </h2>
          <p class="text-lg leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body); opacity: 0">
            洞见是一个 AI 量化投资研究平台。我们不预测明天哪只股票涨停，而是用 23 项技术指标和 10 个分析维度，帮你理解每一只股票背后的逻辑。
          </p>
        </div>
        <div ref="mediaCol" class="lg:col-span-7">
          <div class="glass-card overflow-hidden aspect-video flex items-center justify-center" style="opacity: 0">
            <div class="text-center" style="color: var(--text-dim); font-family: var(--font-body)">
              <div class="text-6xl mb-4">📊</div>
              <p class="text-sm">Dashboard 视频将在此展示</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const sectionRef = ref(null)
const textCol = ref(null)
const mediaCol = ref(null)

onMounted(async () => {
  await nextTick()
  if (!sectionRef.value) return

  ScrollTrigger.create({
    trigger: sectionRef.value,
    start: 'top 70%',
    onEnter: () => {
      // Title
      if (textCol.value) {
        const h2 = textCol.value.querySelector('h2')
        const p = textCol.value.querySelector('p')
        if (h2) gsap.fromTo(h2, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' })
        if (p) gsap.fromTo(p, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.8, delay: 0.2, ease: 'power3.out' })
      }
      // Media card
      if (mediaCol.value) {
        const card = mediaCol.value.querySelector('.glass-card')
        if (card) gsap.fromTo(card, { opacity: 0, x: 30, scale: 0.97 }, { opacity: 1, x: 0, scale: 1, duration: 0.8, delay: 0.1, ease: 'power3.out' })
      }
    },
  })
})
</script>
