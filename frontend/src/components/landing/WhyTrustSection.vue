<template>
  <section ref="sectionRef" class="py-[var(--space-section)]" style="background: var(--color-bg)">
    <div class="mx-auto px-6" style="max-width: var(--space-container)">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6 items-start">
        <div
          v-for="(stat, i) in stats"
          :key="i"
          :ref="el => { if (el) cardRefs[i] = el }"
          class="glass-card p-8 text-center cursor-pointer"
          :class="{ 'ring-1 ring-white/10': expanded[i] }"
          @click="toggleExpand(i)"
        >
          <div class="text-5xl font-bold mb-2" :style="{ color: stat.color, fontFamily: 'var(--font-number)' }">{{ animated[i] }}{{ stat.suffix }}</div>
          <div class="text-sm" style="color: var(--text-secondary); font-family: var(--font-body)">{{ stat.label }}</div>
          <div v-if="expanded[i]" class="mt-4 pt-4 text-xs leading-relaxed" style="color: var(--text-dim); border-top: 1px solid rgba(255,255,255,.05); font-family: var(--font-body)">{{ stat.detail }}</div>
        </div>
      </div>
      <p class="text-center mt-12 text-xl leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body); opacity: 0">
        不是预测市场，而是帮助理解市场。
      </p>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const sectionRef = ref(null)
const cardRefs = ref([])
const expanded = reactive({})
const animated = reactive([0, 0, 0, 0])

const stats = [
  { label: '实时扫描股票', target: 5000, suffix: '+', color: 'var(--color-highlight)', detail: '覆盖沪深两市全部 A 股，每 2 秒完成一次全市场扫描。东方财富、同花顺、腾讯三源实时交叉验证。' },
  { label: '技术指标', target: 23, suffix: '+', color: 'var(--color-purple)', detail: '涵盖 MA 趋势族、MACD 动量族、RSI 超买超卖、布林带波动率、ATR 风险度量、筹码分布、形态识别、资金流向等完整指标体系。' },
  { label: '协同分析模块', target: 10, suffix: '', color: 'var(--color-primary)', detail: 'Trend / Volume / Chip / Pattern / Risk / Sector / News / Macro / Research / Decision 十个维度独立运转，委员会投票形成共识。' },
  { label: '市场扫描速度', target: 2, suffix: 's', color: 'var(--color-green)', detail: '10 线程并行下载 K 线数据，全市场扫描从发起到完成仅需 2 秒，支持实时 WebSocket 推送。' },
]

const toggleExpand = (i) => { expanded[i] = !expanded[i] }

onMounted(async () => {
  await nextTick()
  if (!sectionRef.value) return

  const cards = cardRefs.value.filter(Boolean)

  ScrollTrigger.create({
    trigger: sectionRef.value,
    start: 'top 80%',
    onEnter: () => {
      // Cards stagger entrance
      gsap.fromTo(cards, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.6, stagger: 0.1, ease: 'power2.out' })

      // Count-up for each number using reactive array
      stats.forEach((stat, i) => {
        animated[i] = 0
        const obj = { val: 0 }
        gsap.to(obj, {
          val: stat.target,
          duration: 1.5,
          ease: 'power2.out',
          delay: 0.3 + i * 0.1,
          onUpdate: () => { animated[i] = Math.round(obj.val) },
        })
      })
    },
  })

  // Bottom text
  const bottomText = sectionRef.value.querySelector('p:last-child')
  if (bottomText) {
    ScrollTrigger.create({
      trigger: bottomText,
      start: 'top 90%',
      onEnter: () => gsap.to(bottomText, { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }),
    })
  }
})
</script>
