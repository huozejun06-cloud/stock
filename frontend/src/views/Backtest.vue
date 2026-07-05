<template>
  <div ref="pageRef" class="min-h-screen pt-28 pb-16 px-6" style="background: var(--color-bg)">
    <div class="mx-auto" style="max-width: var(--space-container)">
      <div ref="headerRef" class="mb-10" style="opacity: 0">
        <h1 class="text-3xl md:text-4xl font-normal mb-2" style="font-family: var(--font-hero); color: var(--text-primary)">策略验证</h1>
        <p class="text-sm" style="color: var(--text-dim); font-family: var(--font-body)">历史回测 · 策略参数优化 · 风险收益评估</p>
      </div>

      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div v-for="(m, i) in metrics" :key="m.label"
          :ref="el => { if (el) metricRefs[i] = el }"
          class="glass-card p-6 text-center" style="opacity: 0"
        >
          <div class="text-3xl font-bold mb-1" style="font-family: var(--font-number); color: var(--text-primary)">{{ m.value }}</div>
          <div class="text-xs" style="color: var(--text-dim); font-family: var(--font-body)">{{ m.label }}</div>
          <div class="text-xs mt-2" style="font-family: var(--font-number)" :style="{ color: m.trend > 0 ? 'var(--color-green)' : 'var(--color-red)' }">{{ m.sub }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div ref="chartRef1" class="glass-card p-4" style="opacity: 0">
          <div class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">累计收益曲线</div>
          <div ref="equityChartRef" style="height: 300px"></div>
        </div>
        <div ref="chartRef2" class="glass-card p-4" style="opacity: 0">
          <div class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">月度收益分布</div>
          <div ref="monthlyChartRef" style="height: 300px"></div>
        </div>
      </div>

      <div ref="paramsRef" class="glass-card p-6" style="opacity: 0">
        <h3 class="text-sm font-semibold mb-4" style="color: var(--text-secondary); font-family: var(--font-body)">策略参数配置</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div v-for="p in params" :key="p.name" class="bg-white/4 rounded-lg p-3">
            <div class="text-xs mb-1" style="color: var(--text-dim); font-family: var(--font-body)">{{ p.name }}</div>
            <div class="font-medium" style="color: var(--text-primary); font-family: var(--font-number)">{{ p.value }}</div>
          </div>
        </div>
      </div>
    
      <!-- Strategy Optimization -->
      <div ref="optRef" class="glass-card p-6 mt-6" style="opacity: 0">
        <h3 class="text-sm font-semibold mb-4" style="color: var(--text-secondary); font-family: var(--font-body)">💡 策略优化建议</h3>
        <div class="space-y-3">
          <div v-for="o in optimizations" :key="o.title" class="bg-white/4 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs px-2 py-0.5 rounded-full" style="font-family: var(--font-number)" :style="{ background: o.severity === 'high' ? 'rgba(33,208,122,.12)' : 'rgba(108,140,255,.12)', color: o.severity === 'high' ? 'var(--color-green)' : 'var(--color-highlight)' }">{{ o.severity === 'high' ? '高收益' : '中收益' }}</span>
              <span class="text-sm font-semibold" style="color: var(--text-primary); font-family: var(--font-body)">{{ o.title }}</span>
            </div>
            <p class="text-sm leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body)">{{ o.desc }}</p>
            <div class="flex items-center gap-3 mt-1 text-xs" style="font-family: var(--font-number)">
              <span style="color: var(--text-dim)">预期提升: <span style="color: var(--color-green)">{{ o.expected }}</span></span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import * as echarts from 'echarts'

const pageRef = ref(null)
const headerRef = ref(null)
const metricRefs = ref([])
const chartRef1 = ref(null)
const chartRef2 = ref(null)
const paramsRef = ref(null)
const optRef = ref(null)
const equityChartRef = ref(null)
const monthlyChartRef = ref(null)

const metrics = [
  { label: '累计收益率', value: '+186.4%', sub: '基准: +32.1%', trend: 1 },
  { label: '年化收益率', value: '+24.8%', sub: '超额: +18.5%', trend: 1 },
  { label: '夏普比率', value: '2.31', sub: 'Calmar: 3.12', trend: 1 },
  { label: '最大回撤', value: '-14.2%', sub: '发生在 2025/02', trend: -1 },
]

const params = [
  { name: '选股评分阈值', value: '≥ 75' },
  { name: '最大持仓数', value: '8 只' },
  { name: '单只仓位上限', value: '15%' },
  { name: '止损线', value: '-5%' },
  { name: '止盈线', value: '+20%' },
  { name: '调仓周期', value: '每日尾盘' },
  { name: '交易成本', value: '0.1%' },
  { name: '回测区间', value: '2024.01 - 2026.06' },
]

onMounted(async () => {
  await nextTick()

  gsap.fromTo(headerRef.value, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' })
  const mCards = metricRefs.value.filter(Boolean)
  mCards.forEach((c, i) => {
    gsap.fromTo(c, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.4, delay: 0.1 * i, ease: 'power2.out' })
  })
  ;[chartRef1, chartRef2, paramsRef].forEach((r, i) => {
    if (r.value) gsap.fromTo(r.value, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.4 + i * 0.1, ease: 'power2.out' })
  })

  setTimeout(() => {
    // Equity curve
    if (equityChartRef.value) {
      const c1 = echarts.init(equityChartRef.value)
      const data = []
      let v = 100
      for (let i = 0; i < 30; i++) {
        v *= 1 + (Math.random() - 0.42) * 0.12
        data.push(+v.toFixed(1))
      }
      c1.setOption({
        grid: { left: 40, right: 16, top: 8, bottom: 24 },
        xAxis: { data: data.map((_,i) => `${i+1}月`), axisLabel: { color: '#64748b', fontSize: 10 } },
        yAxis: { axisLabel: { color: '#64748b', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } } },
        series: [{ type: 'line', data, smooth: true, lineStyle: { color: '#6c8cff', width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0,color:'rgba(108,140,255,.2)'},{offset:1,color:'rgba(108,140,255,.0)'}]) }, symbol: 'none' }],
      })
    }
    // Monthly returns
    if (monthlyChartRef.value) {
      const c2 = echarts.init(monthlyChartRef.value)
      const data2 = Array.from({length: 30}, () => +((Math.random() - 0.45) * 15).toFixed(1))
      c2.setOption({
        grid: { left: 40, right: 16, top: 8, bottom: 24 },
        xAxis: { data: data2.map((_,i) => `${i+1}月`), axisLabel: { color: '#64748b', fontSize: 10 } },
        yAxis: { axisLabel: { color: '#64748b', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } } },
        series: [{ type: 'bar', data: data2, itemStyle: { color: (params) => params.value >= 0 ? '#21d07a' : '#ff5b6e', borderRadius: [3,3,0,0] }, barWidth: '60%' }],
      })
    }
  }, 500)
})
</script>
