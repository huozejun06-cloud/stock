<template>
  <div ref="pageRef" class="min-h-screen pt-28 pb-16 px-6" style="background: var(--color-bg)">
    <div class="mx-auto" style="max-width: var(--space-container)">
      <div ref="headerRef" class="mb-12 text-center" style="opacity: 0">
        <h1 class="text-3xl md:text-4xl font-normal mb-3" style="font-family: var(--font-hero); color: var(--text-primary)">研究方法</h1>
        <p class="text-sm" style="color: var(--text-dim); font-family: var(--font-body)">为什么值得相信？这不是黑盒 AI，而是有完整方法论支撑的量化体系。</p>
      </div>

      <!-- Core Principles -->
      <div ref="principlesRef" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8" style="opacity: 0">
        <div v-for="p in principles" :key="p.title" class="glass-card p-6">
          <div class="text-2xl mb-3">{{ p.icon }}</div>
          <h3 class="text-lg font-semibold mb-2" style="color: var(--text-primary); font-family: var(--font-body)">{{ p.title }}</h3>
          <p class="text-sm leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body)">{{ p.desc }}</p>
        </div>
      </div>

      <!-- Data Pipeline -->
      <div ref="pipelineRef" class="glass-card p-6 mb-8" style="opacity: 0">
        <h3 class="text-lg font-semibold mb-6 text-center" style="color: var(--text-primary); font-family: var(--font-body)">数据处理流水线</h3>
        <div class="flex flex-wrap justify-center items-center gap-3">
          <div v-for="(step, i) in pipeline" :key="step" class="flex items-center gap-3">
            <div class="px-4 py-2 rounded-full text-xs font-medium" style="background:rgba(108,140,255,.1);color:var(--color-highlight);font-family:var(--font-body)">{{ step }}</div>
            <span v-if="i < pipeline.length - 1" class="text-lg" style="color: var(--text-dim)">→</span>
          </div>
        </div>
      </div>

      <!-- Indicator Lab -->
      <div ref="labRef" class="mb-8" style="opacity: 0">
        <h3 class="text-lg font-semibold mb-4" style="color: var(--text-primary); font-family: var(--font-body)">指标实验室</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div v-for="ind in indicatorLab" :key="ind.name" class="glass-card p-5">
            <h4 class="text-base font-semibold mb-2" style="color: var(--text-primary); font-family: var(--font-body)">{{ ind.name }}</h4>
            <p class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">{{ ind.category }}</p>
            <p class="text-sm leading-relaxed mb-3" style="color: var(--text-secondary); font-family: var(--font-body)">{{ ind.explanation }}</p>
            <div class="flex items-center gap-2">
              <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(108,140,255,.1);color:var(--color-highlight);font-family:var(--font-number)">权重: {{ ind.weight }}%</span>
              <span class="text-xs" style="color: var(--text-dim); font-family: var(--font-body)">{{ ind.usage }}</span>
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

const pageRef = ref(null)
const headerRef = ref(null)
const principlesRef = ref(null)
const pipelineRef = ref(null)
const labRef = ref(null)

const principles = [
  { icon: '🔍', title: '不是预测，是理解', desc: '我们不预测明天涨跌，而是通过 23 项技术指标量化每一只股票的多空力量对比。市场不可预测，但风险可以量化。' },
  { icon: '🛡️', title: '先排雷，再选股', desc: 'MA20 趋势、ATR 波动率、BIAS 乖离率、MACD 共振、资金流向——五道风险红线先过滤高风险股票，剩下的才是候选池。' },
  { icon: '🧠', title: 'AI 解释，不决定', desc: 'AI 承担指标解读、风险提示、逻辑推理的角色，但最终买卖决策权在用户手中。AI 放大你的判断，而非替代你的判断。' },
  { icon: '🤝', title: '委员会共识机制', desc: '10 个分析模块独立打分后投票，只有 7 票以上 BUY 才会形成强烈推荐。单一模块出错不会影响全局。' },
]

const pipeline = ['实时行情抓取', '三源交叉验证', '数据清洗去噪', '23项指标计算', '五道风险过滤', '六维加权评分', 'Agent协同研判', '研究报告生成']

const indicatorLab = [
  { name: 'MA 趋势体系', category: '趋势族', explanation: 'MA5/MA10/MA20/MA60 四线多头排列时，趋势向上确认。MA20 是核心趋势线，股价必须站上才纳入候选。', weight: 20, usage: '趋势方向判断' },
  { name: 'MACD 动量共振', category: '动量族', explanation: 'DIF 线上穿 DEA 形成金叉，柱状线由绿转红。三重确认（DIF/DEA/柱状线）避免假信号。', weight: 10, usage: '买卖时机确认' },
  { name: 'RSI 超买超卖', category: '动量族', explanation: 'RSI(14) 低于 30 为超卖、高于 70 为超买。结合趋势判断，不单独使用。底部 RSI 背离是重要的反转信号。', weight: 5, usage: '极端状态预警' },
  { name: 'ADX 趋势强度', category: '趋势族', explanation: 'ADX > 25 确认趋势存在，ADX > 40 为强趋势。不关心方向，只关心强度。震荡市中 ADX 低时不参与。', weight: 5, usage: '趋势强度过滤' },
  { name: '布林带波动率', category: '波动族', explanation: '价格触及下轨可能超卖，触及上轨可能超买。带宽收窄预示变盘。中轨方向决定中期趋势。', weight: 5, usage: '波动率估计' },
  { name: '筹码分布集中度', category: '筹码族', explanation: '用高斯分布拟合筹码峰，集中度越高说明主力控盘越强。获利比例 > 70% 时抛压较小。', weight: 15, usage: '主力行为分析' },
]

onMounted(async () => {
  await nextTick()
  ;[headerRef, principlesRef, pipelineRef, labRef].forEach((r, i) => {
    if (r.value) gsap.fromTo(r.value,
      { opacity: 0, y: 30, filter: 'blur(4px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.6, delay: i * 0.12, ease: 'power3.out' }
    )
  })
})
</script>
