<template>
  <div ref="pageRef" class="min-h-screen pt-28 pb-16 px-6" style="background: var(--color-bg)">
    <div class="mx-auto" style="max-width: var(--space-container)">

      <div ref="headerRef" class="text-center mb-12" style="opacity: 0">
        <div class="mb-4">
          <span class="text-3xl font-semibold" style="font-family: var(--font-hero); color: var(--text-primary)">洞见</span>
          <span class="text-sm tracking-widest ml-3" style="color: var(--text-dim); font-family: var(--font-number)">INSIGHT</span>
        </div>
        <p class="text-lg mb-1" style="color: var(--text-secondary); font-family: var(--font-body)">AI 量化投资研究平台</p>
        <p class="text-sm" style="color: var(--text-dim); font-family: var(--font-body)">Version 3.2</p>
      </div>

      <div ref="descRef" class="glass-card p-6 mb-6 max-w-2xl mx-auto text-center" style="opacity: 0">
        <p class="text-sm leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body)">
          洞见是一个面向 A 股市场的 AI 量化投资研究平台。我们不预测涨跌，而是通过 23 项技术指标和 10 个分析维度，
          帮助投资者理解每一只股票背后的多空力量对比。所有 AI 研判仅作为研究参考，不构成投资建议。
        </p>
      </div>

      <div ref="techRef" class="mb-8" style="opacity: 0">
        <h3 class="text-lg font-semibold mb-4 text-center" style="color: var(--text-primary); font-family: var(--font-body)">技术架构</h3>
        <div class="flex flex-wrap justify-center gap-3">
          <span v-for="t in techStack" :key="t" class="px-4 py-2 rounded-full text-xs font-medium" style="background:rgba(255,255,255,.04);color:var(--text-secondary);border:1px solid rgba(255,255,255,.06);font-family:var(--font-body)">{{ t }}</span>
        </div>
      </div>

      <div ref="footerRef" class="text-center" style="opacity: 0">
        <p class="text-xs mt-8" style="color: var(--text-dim); font-family: var(--font-body)">© 2026 洞见 INSIGHT. Built with Vue3 + FastAPI + Python + DeepSeek + ECharts + GSAP.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { gsap } from 'gsap'

const pageRef = ref(null)
const headerRef = ref(null)
const descRef = ref(null)
const techRef = ref(null)
const footerRef = ref(null)

const techStack = ['Vue 3', 'Vite', 'Tailwind CSS', 'GSAP', 'ECharts', 'FastAPI', 'Python', 'DeepSeek', 'SQLite', 'WebSocket', '东方财富 API', 'AKShare', 'TuShare']

onMounted(async () => {
  await nextTick()
  ;[headerRef, descRef, techRef, footerRef].forEach((r, i) => {
    if (r.value) gsap.fromTo(r.value,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.5, delay: i * 0.15, ease: 'power2.out' }
    )
  })
})
</script>
