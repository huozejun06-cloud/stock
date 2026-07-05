<template>
  <div ref="pageRef" class="min-h-screen pt-28 pb-16 px-6" style="background: var(--color-bg)">
    <div class="mx-auto" style="max-width: var(--space-container)">

      <div ref="headerRef" class="mb-10" style="opacity: 0">
        <h1 class="text-3xl md:text-4xl font-normal mb-2" style="font-family: var(--font-hero); color: var(--text-primary)">市场全景</h1>
        <p class="text-sm" style="color: var(--text-dim); font-family: var(--font-body)">实时市场数据概览 · 数据延迟 &lt; 2s</p>
      </div>

      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div v-for="(idx, i) in indices" :key="i" :ref="el => { if (el) cardRefs[i] = el }" class="glass-card p-6" style="opacity: 0">
          <div class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">{{ idx.name }}</div>
          <div class="text-2xl font-bold mb-1" style="font-family: var(--font-number); color: var(--text-primary)">{{ idx.price }}</div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium" style="font-family: var(--font-number)" :style="{ color: idx.change > 0 ? 'var(--color-green)' : 'var(--color-red)' }">{{ idx.change > 0 ? '+' : '' }}{{ idx.change }}%</span>
            <span class="text-xs" style="color: var(--text-dim); font-family: var(--font-body)">{{ idx.amount }}</span>
          </div>
        </div>
      </div>

      <div ref="globalRef" class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6" style="opacity: 0">
        <div v-for="g in globalIndices" :key="g.name" class="glass-card p-4 flex items-center gap-3">
          <span class="text-xl">{{ g.flag }}</span>
          <div>
            <div class="text-xs" style="color: var(--text-dim); font-family: var(--font-body)">{{ g.name }}</div>
            <div class="text-sm font-bold" style="font-family: var(--font-number); color: var(--text-primary)">{{ g.price }}</div>
            <div class="text-xs font-medium" style="font-family: var(--font-number)" :style="{ color: g.change > 0 ? 'var(--color-green)' : 'var(--color-red)' }">{{ g.change > 0 ? '+' : '' }}{{ g.change }}%</div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div ref="sentimentRef" class="glass-card p-6 lg:col-span-1" style="opacity: 0">
          <h3 class="text-sm font-semibold mb-4" style="color: var(--text-secondary); font-family: var(--font-body)">市场情绪</h3>
          <div class="space-y-4">
            <div>
              <div class="flex justify-between text-xs mb-1" style="font-family: var(--font-body)"><span style="color: var(--text-dim)">涨跌比</span><span style="color: var(--text-primary); font-family: var(--font-number)">{{ sentiment.upDown }}</span></div>
              <div class="h-1.5 rounded-full overflow-hidden" style="background: rgba(255,255,255,.06)"><div class="h-full rounded-full" style="width: 55%; background: var(--color-green)" /></div>
            </div>
            <div><div class="flex justify-between text-xs mb-1" style="font-family: var(--font-body)"><span style="color: var(--text-dim)">涨停 / 跌停</span><span style="color: var(--text-primary); font-family: var(--font-number)">{{ sentiment.limitUp }} / {{ sentiment.limitDown }}</span></div></div>
            <div><div class="flex justify-between text-xs mb-1" style="font-family: var(--font-body)"><span style="color: var(--text-dim)">连板高度</span><span style="color: var(--color-highlight); font-family: var(--font-number)">{{ sentiment.maxBoard }}板</span></div></div>
            <div><div class="flex justify-between text-xs mb-1" style="font-family: var(--font-body)"><span style="color: var(--text-dim)">成交量</span><span style="color: var(--text-primary); font-family: var(--font-number)">{{ sentiment.volume }}</span></div></div>
          </div>
        </div>
        <div ref="sectorsRef" class="glass-card p-6 lg:col-span-2" style="opacity: 0">
          <h3 class="text-sm font-semibold mb-4" style="color: var(--text-secondary); font-family: var(--font-body)">热门板块</h3>
          <div class="space-y-3">
            <div v-for="s in sectors" :key="s.name" class="flex items-center justify-between py-2" style="border-bottom: 1px solid rgba(255,255,255,.04)">
              <span class="text-sm" style="color: var(--text-primary); font-family: var(--font-body)">{{ s.name }}</span>
              <div class="flex items-center gap-4">
                <span class="text-xs" style="color: var(--text-dim); font-family: var(--font-number)">{{ s.count }}只</span>
                <span class="text-sm font-medium" style="font-family: var(--font-number)" :style="{ color: s.change > 0 ? 'var(--color-green)' : 'var(--color-red)' }">{{ s.change > 0 ? '+' : '' }}{{ s.change }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div ref="newsRef" class="glass-card p-3 mb-4 overflow-hidden" style="opacity: 0">
        <div class="flex items-center gap-3">
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full shrink-0" style="background:rgba(255,107,53,.12);color:var(--color-primary);font-family:var(--font-body)">📡 实时快讯</span>
          <div class="overflow-hidden flex-1">
            <div class="flex gap-8" style="animation: ticker-scroll 20s linear infinite; width: max-content">
              <span v-for="n in newsItems" :key="n" class="text-xs whitespace-nowrap" style="color: var(--text-secondary); font-family: var(--font-body)">{{ n }}</span>
            </div>
          </div>
        </div>
      </div>

      <div ref="logRef" class="glass-card p-6" style="opacity: 0">
        <h3 class="text-sm font-semibold mb-4" style="color: var(--text-secondary); font-family: var(--font-body)">AI 协同研判 · 最新日志</h3>
        <div class="space-y-3">
          <div v-for="(log, i) in agentLogs" :key="i" class="flex items-start gap-3 py-2" style="border-bottom: 1px solid rgba(255,255,255,.04)">
            <span class="text-xs px-2 py-0.5 rounded-full shrink-0 mt-0.5" style="font-family: var(--font-number)" :style="{ background: log.color + '18', color: log.color }">{{ log.agent }}</span>
            <div>
              <p class="text-sm" style="color: var(--text-primary); font-family: var(--font-body)">{{ log.msg }}</p>
              <p class="text-xs mt-1" style="color: var(--text-dim); font-family: var(--font-number)">{{ log.time }}</p>
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

const pageRef = ref(null); const headerRef = ref(null)
const cardRefs = ref([]); const globalRef = ref(null); const newsRef = ref(null)
const sentimentRef = ref(null); const sectorsRef = ref(null); const logRef = ref(null)

const indices = ref([
  { name: '上证指数', price: '3,342.17', change: +0.72, amount: '4,821亿' },
  { name: '深证成指', price: '10,891.55', change: +0.89, amount: '6,254亿' },
  { name: '创业板指', price: '2,194.33', change: -0.14, amount: '1,893亿' },
  { name: '科创50', price: '1,025.60', change: +1.23, amount: '847亿' },
])

const globalIndices = ref([
  { name: '道琼斯', flag: '🇺🇸', price: '42,130.55', change: +0.35 },
  { name: '纳斯达克', flag: '🇺🇸', price: '19,854.21', change: +0.52 },
  { name: '恒生指数', flag: '🇭🇰', price: '22,340.18', change: -0.28 },
  { name: '日经225', flag: '🇯🇵', price: '38,762.44', change: +0.18 },
])

const sentiment = ref({ upDown: '2,847 : 2,156', limitUp: 62, limitDown: 8, maxBoard: 7, volume: '11,428亿' })

const sectors = ref([
  { name: '半导体', count: 48, change: +3.52 },
  { name: '人工智能', count: 62, change: +2.87 },
  { name: '新能源车', count: 35, change: +2.14 },
  { name: '生物医药', count: 56, change: +1.68 },
  { name: '军工航天', count: 28, change: -0.43 },
])

const newsItems = ref(['北向资金今日净流入58.3亿，外资连续第5日加仓A股','央行开展2000亿MLF操作，利率维持不变','半导体板块集体走强，板块内12只个股涨停','新能源车6月销量同比+38%，渗透率突破45%','美联储维持利率不变，点阵图显示年内或降息2次'])

const agentLogs = ref([
  { agent: 'Trend', msg: '市场整体处于多头排列，MA20向上发散，中期趋势看多。', time: '14:32:05', color: 'var(--color-highlight)' },
  { agent: 'Macro', msg: '北向资金今日净流入58.3亿，外资连续第5日加仓A股。', time: '14:31:42', color: 'var(--color-purple)' },
  { agent: 'Sector', msg: '半导体板块RS强度突破85，板块内涨停12家，强势特征明显。', time: '14:30:18', color: 'var(--color-green)' },
  { agent: 'Risk', msg: '当前市场波动率处于低位（ATR占比1.2%），系统性风险可控。', time: '14:29:55', color: 'var(--color-primary)' },
  { agent: 'News', msg: '今日无重大利空公告，市场情绪偏乐观。', time: '14:28:30', color: 'var(--color-highlight)' },
])

// Fetch real data from backend
async function fetchOverview() {
  try {
    const res = await fetch('http://localhost:8000/api/overview')
    if (!res.ok) return
    const d = await res.json()

    // Map API fields to template variables
    if (d.indices?.length) indices.value = d.indices.map(i => ({
      name: i.name, price: i.price?.toLocaleString?.() || String(i.price),
      change: i.change_pct || i.change || 0,
      amount: i.amount || ''
    }))
    if (d.global?.length) globalIndices.value = d.global.map(g => ({
      flag: g.name === '道琼斯' || g.name === '纳斯达克' ? '🇺🇸' : g.name === '恒生指数' ? '🇭🇰' : '🇯🇵',
      name: g.name, price: g.price?.toLocaleString?.() || String(g.price),
      change: g.change_pct || g.change || 0
    }))
    if (d.sentiment) sentiment.value = {
      upDown: d.sentiment.up_down_ratio || sentiment.value.upDown,
      limitUp: d.sentiment.limit_up || sentiment.value.limitUp,
      limitDown: d.sentiment.limit_down || sentiment.value.limitDown,
      maxBoard: d.sentiment.max_board_height || sentiment.value.maxBoard,
      volume: d.sentiment.volume || sentiment.value.volume
    }
    if (d.sectors?.length) sectors.value = d.sectors.map(s => ({
      name: s.name, count: s.count, change: s.change_pct || s.change || 0
    }))
    if (d.news?.length) newsItems.value = d.news
    if (d.ai_logs?.length) agentLogs.value = d.ai_logs.map(a => ({
      agent: a.agent, msg: a.msg, time: a.time,
      color: 'var(--color-highlight)'
    }))
  } catch (e) { /* keep mock data */ }
}


function animateIn(el, delay = 0) {
  if (!el) return
  gsap.fromTo(el, { opacity: 0, y: 30, filter: 'blur(4px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.7, delay, ease: 'power3.out' })
}

onMounted(async () => {
  await nextTick()
  animateIn(headerRef.value, 0)
  cardRefs.value.filter(Boolean).forEach((c, i) => animateIn(c, 0.1 + i * 0.08))
  animateIn(globalRef.value, 0.15)
  animateIn(sentimentRef.value, 0.4)
  animateIn(sectorsRef.value, 0.5)
  animateIn(newsRef.value, 0.5)
  animateIn(logRef.value, 0.8)
})
</script>
