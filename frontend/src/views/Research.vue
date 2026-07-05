<template>
  <div class="min-h-screen pt-28 pb-16 px-6" style="background: var(--color-bg)">
    <div class="mx-auto" style="max-width: var(--space-container)">

      <!-- Header -->
      <div ref="headerRef" class="mb-8 flex items-end justify-between" style="opacity: 0">
        <div>
          <div class="text-sm mb-1" style="color: var(--text-dim); font-family: var(--font-number)">{{ code }}</div>
          <h1 class="text-3xl md:text-4xl font-normal" style="font-family: var(--font-hero); color: var(--text-primary)">{{ name }}</h1>
        </div>
        <div class="text-right">
          <div class="text-3xl font-bold" style="font-family: var(--font-number); color: var(--text-primary)">{{ priceDisplay }}</div>
          <div class="text-lg font-medium" style="font-family: var(--font-number)" :style="{ color: pct > 0 ? 'var(--color-green)' : 'var(--color-red)' }">{{ pct > 0 ? '+' : '' }}{{ pct }}%</div>
        </div>
      </div>

      <!-- Row 1: K-line + Indicators -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div ref="klineRef" class="glass-card p-4 lg:col-span-2" style="opacity: 0">
          <div class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">日K线（近30日）</div>
          <div ref="klineChartRef" style="height: 300px"></div>
        </div>
        <div ref="indicatorsRef" class="glass-card p-4" style="opacity: 0">
          <div class="text-xs mb-3" style="color: var(--text-dim); font-family: var(--font-body)">技术指标</div>
          <div class="space-y-3">
            <div v-for="ind in indicators" :key="ind.label" class="flex justify-between items-center py-2" style="border-bottom: 1px solid rgba(255,255,255,.04)">
              <span class="text-sm" style="color: var(--text-secondary); font-family: var(--font-body)">{{ ind.label }}</span>
              <span class="text-sm font-medium" style="font-family: var(--font-number)" :style="{ color: ind.color }">{{ ind.value }}</span>
            </div>
          </div>
        </div>
      </div>

      
      <!-- Pattern Recognition -->
      <div ref="patternRef" class="glass-card p-4 mb-6" style="opacity: 0">
        <div class="text-xs mb-3" style="color: var(--text-dim); font-family: var(--font-body)">形态识别</div>
        <div class="flex flex-wrap gap-2">
          <span v-for="p in patterns" :key="p.name" class="px-3 py-1.5 rounded-full text-xs font-medium cursor-default transition-all duration-300 hover:scale-105"
            :style="{ background: p.active ? 'rgba(108,140,255,.15)' : 'rgba(255,255,255,.03)', color: p.active ? 'var(--color-highlight)' : 'var(--text-dim)', border: '1px solid ' + (p.active ? 'rgba(108,140,255,.25)' : 'rgba(255,255,255,.05)'), fontFamily: 'var(--font-body)' }"
          >{{ p.active ? '🔺' : '○' }} {{ p.name }}</span>
        </div>
      </div>

      <!-- Row 2: Chip Distribution -->
      <div ref="chipRef" class="glass-card p-4 mb-6" style="opacity: 0">
        <div class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">筹码分布</div>
        <div ref="chipChartRef" style="height: 160px"></div>
      </div>

      
      <!-- Fundamentals Panel -->
      <div ref="fundRef" class="glass-card p-4 mb-6" style="opacity: 0">
        <div class="text-xs mb-3" style="color: var(--text-dim); font-family: var(--font-body)">基本面数据</div>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div v-for="f in fundamentals" :key="f.label" class="bg-white/4 rounded-lg p-3">
            <div class="text-xs mb-0.5" style="color: var(--text-dim); font-family: var(--font-body)">{{ f.label }}</div>
            <div class="text-base font-bold" style="font-family: var(--font-number); color: var(--text-primary)">{{ f.value }}</div>
          </div>
        </div>
      </div>

      <!-- Row 3: Agent Committee -->
      <div ref="agentRef" class="glass-card p-4 mb-6" style="opacity: 0">
        <div class="text-xs mb-4" style="color: var(--text-dim); font-family: var(--font-body)">协同研判委员会（10 模块独立投票）</div>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div v-for="(a, ai) in agents" :key="a.name" @click="toggleDebate(ai)" class="text-center py-3 px-2 rounded-xl transition-all duration-300 cursor-pointer" :class="a.vote === 'BUY' ? 'bg-green-500/8 border border-green-500/20' : a.vote === 'WATCH' ? 'bg-yellow-500/8 border border-yellow-500/20' : 'bg-red-500/8 border border-red-500/20'">
            <div class="text-xs mb-1" style="color: var(--text-dim); font-family: var(--font-body)">{{ a.name }}</div>
            <div class="text-lg font-bold" style="font-family: var(--font-number)" :style="{ color: a.vote === 'BUY' ? 'var(--color-green)' : a.vote === 'WATCH' ? '#eab308' : 'var(--color-red)' }">{{ a.vote }}</div>
            <div class="text-2xs mt-0.5" style="color: var(--text-dim); font-family: var(--font-body)">{{ a.confidence }}%</div>
            <div v-if="debateOpen[ai]" class="mt-2 pt-2 text-2xs leading-relaxed" style="color: var(--text-dim); border-top:1px solid rgba(255,255,255,.06); font-family: var(--font-body)">{{ a.reason }}</div>
          </div>
        </div>
        <div class="mt-4 text-center">
          <span class="text-sm font-semibold px-4 py-1.5 rounded-full" style="font-family: var(--font-body)" :style="consensusStyle">{{ consensusText }}</span>
        </div>
      </div>

      <!-- Row 4: AI Report -->
      <div ref="reportRef" class="glass-card p-6" style="opacity: 0">
        <div class="text-xs mb-3" style="color: var(--text-dim); font-family: var(--font-body)">AI 研判报告</div>
        <div class="prose prose-invert max-w-none text-sm leading-relaxed space-y-3" style="font-family: var(--font-body)">
          <p style="color: var(--text-secondary)">
            <strong style="color: var(--text-primary)">综合评级：</strong>
            <span :style="{ color: signalColor }">{{ signalText }}</span>
            · 评分 {{ totalScore }} 分
          </p>
          <p style="color: var(--text-secondary)">
            <strong style="color: var(--text-primary)">趋势分析：</strong>
            当前处于 MA5/MA10/MA20 多头排列，ADX 值 {{ adx }} 显示趋势强度 {{ adxLevel }}。布林带中轨向上发散，价格运行于中上轨之间。
          </p>
          <p style="color: var(--text-secondary)">
            <strong style="color: var(--text-primary)">资金面：</strong>
            近5日主力资金 {{ fundFlow }}，大单净量 {{ bigOrder }}。量比 {{ volRatio }}，{{ volLevel }}。
          </p>
          <p style="color: var(--text-secondary)">
            <strong style="color: var(--text-primary)">筹码结构：</strong>
            获利比例 {{ profitRatio }}%，筹码集中度 {{ concentration }}，{{ chipLevel }}。
          </p>
          <p style="color: var(--text-secondary)">
            <strong style="color: var(--text-primary)">风险提示：</strong>
            ATR 波动率 {{ atr }}%，止损建议设在 ¥{{ stopLoss }}（关键支撑位 - ATR × 1.0）。盈亏比 {{ profitRatio2 }}。
          </p>
          <p style="color: var(--text-secondary)">
            <strong style="color: var(--text-primary)">委员会共识：</strong>
            10 个模块中 {{ buyCount }} 票 BUY、{{ watchCount }} 票 WATCH、{{ sellCount }} 票 SELL。
            {{ consensusDetail }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { gsap } from 'gsap'
import * as echarts from 'echarts'

const route = useRoute()

// Mock data
const code = computed(() => route.params.code || '600519')

// Fetch real data from backend
const API_BASE = 'http://localhost:8000'
const apiData = ref(null)

async function fetchResearch() {
  try {
    const res = await fetch(`${API_BASE}/api/research/${code.value}`)
    if (res.ok) {
      const data = await res.json()
      apiData.value = data
    }
  } catch (e) {
    console.warn('Research API unavailable, using mock data')
  }
}

// Override name/price from API data if available
const apiName = computed(() => apiData.value?.name || stockInfo.value[0])
const apiPrice = computed(() => {
  if (apiData.value?.price) return typeof apiData.value.price === 'number' ? apiData.value.price.toFixed(2) : apiData.value.price
  const bp = basePrice.value
  if (bp >= 100) return bp.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.00'
  if (bp >= 10) return bp.toFixed(2)
  return bp.toFixed(2)
})

// Quick stock lookup — maps code to name + base price for dynamic mock data
const stockMap = {
  '600519':['贵州茅台',1195],'000858':['五粮液',168],'300750':['宁德时代',257],'002594':['比亚迪',312],
  '601899':['紫金矿业',18.6],'600276':['恒瑞医药',52],'000333':['美的集团',79],'300274':['阳光电源',98],
  '600036':['招商银行',42],'601318':['中国平安',57],'600900':['长江电力',27.6],'002415':['海康威视',36.5],
  '300124':['汇川技术',68],'600809':['山西汾酒',245],'000651':['格力电器',45],'601012':['隆基绿能',22.8],
  '600031':['三一重工',18.9],'002230':['科大讯飞',52],'300059':['东方财富',19.5],'600585':['海螺水泥',32],
  '000725':['京东方A',5.8],'601166':['兴业银行',19.2],'600030':['中信证券',28.6],'002714':['牧原股份',48.7],
  '300015':['爱尔眼科',35],'600887':['伊利股份',33],'000063':['中兴通讯',42],'601088':['中国神华',38.5],
  '002475':['立讯精密',37],'300122':['智飞生物',56],'600048':['保利发展',14.3],'000568':['泸州老窖',198],
  '601857':['中国石油',8.6],'002271':['东方雨虹',25.4],'300529':['健帆生物',32],'600690':['海尔智家',30],
  '000002':['万科A',12.5],'601138':['工业富联',26.4],'002352':['顺丰控股',52],'300450':['先导智能',38],
  '600436':['片仔癀',298],'000538':['云南白药',62.5],'601336':['新华保险',43],'002236':['大华股份',22.4],
  '300502':['新易盛',69],'600009':['上海机场',46],'000977':['浪潮信息',38.6],'601628':['中国人寿',36],
  '002460':['赣锋锂业',52],'300433':['蓝思科技',18.6],
}
const stockInfo = computed(() => stockMap[code.value] || [code.value, 50])
const name = computed(() => apiName.value)
const basePrice = computed(() => stockInfo.value[1])
const priceDisplay = computed(() => {
  if (apiData.value?.price) return apiPrice.value
  const bp = basePrice.value
  if (bp >= 100) return bp.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.00'
  if (bp >= 10) return bp.toFixed(2)
  return bp.toFixed(2)
})
const pct = computed(() => {
  let h = 0; for (const ch of code.value) h = ((h << 5) - h) + ch.charCodeAt(0)
  return +((h % 8 - 2).toFixed(2))
})

// API-derived indicators (mock fallback when API unavailable)
const indicators = computed(() => {
  const ind = apiData.value?.indicators
  const bp = basePrice.value
  const up = (v) => parseFloat(v) > bp * 0.98 ? ' ↑' : ' ↓'
  return [
    { label: 'MA5', value: ind?.ma5 ? ind.ma5.toFixed(2) + up(ind.ma5) : (bp * 0.993).toFixed(2) + ' ↑', color: 'var(--color-green)' },
    { label: 'MA10', value: ind?.ma10 ? ind.ma10.toFixed(2) + up(ind.ma10) : (bp * 0.978).toFixed(2) + ' ↑', color: 'var(--color-green)' },
    { label: 'MA20', value: ind?.ma20 ? ind.ma20.toFixed(2) + up(ind.ma20) : (bp * 0.955).toFixed(2) + ' ↑', color: 'var(--color-green)' },
    { label: 'MACD', value: ind?.macd ? 'DIF: ' + ind.macd.toFixed(2) : 'DIF: ' + (bp * 0.007).toFixed(2), color: 'var(--color-highlight)' },
    { label: 'RSI(14)', value: ind?.rsi14 ? ind.rsi14.toFixed(1) : '62.5', color: 'var(--text-primary)' },
    { label: 'BOLL', value: ind?.ma20 ? '上轨: ' + (ind.ma20 * 1.06).toFixed(0) : '上轨: ' + (bp * 1.06).toFixed(0), color: 'var(--text-secondary)' },
    { label: 'ATR(14)', value: ind?.atr14 ? ind.atr14.toFixed(2) + ' (' + (ind.atr14 / basePrice.value * 100).toFixed(2) + '%)' : (bp * 0.0156).toFixed(2) + ' (1.56%)', color: 'var(--text-dim)' },
    { label: '量比', value: ind?.volume_ratio ? ind.volume_ratio.toFixed(2) : '1.32', color: 'var(--color-purple)' },
  ]
})

const adx = computed(() => apiData.value?.indicators?.adx || 38)
const adxLevel = computed(() => adx.value >= 40 ? '强趋势' : adx.value >= 25 ? '偏强' : '震荡')
const fundFlow = ref('净流入 3.2 亿')
const bigOrder = ref('+0.42%')
const volRatio = computed(() => apiData.value?.indicators?.volume_ratio?.toFixed(2) || '1.32')
const volLevel = computed(() => parseFloat(volRatio.value) >= 2 ? '明显放量' : parseFloat(volRatio.value) >= 1.2 ? '温和放量' : '缩量')
const profitRatio = ref('72.3')
const concentration = ref('34.5%')
const chipLevel = ref('筹码趋于集中')
const atr = computed(() => apiData.value?.indicators?.atr14?.toFixed(2) || '1.56')
const stopLoss = computed(() => {
  if (apiData.value?.key_levels?.stop_loss) return apiData.value.key_levels.stop_loss.toFixed(2)
  return '1,168.00'
})
const profitRatio2 = ref('2.8 : 1')

const totalScore = computed(() => apiData.value?.decision?.total_score || 88)
const buyCount = ref(7)
const watchCount = ref(2)
const sellCount = ref(1)
const signalText = computed(() => {
  const sig = apiData.value?.decision?.signal
  if (sig === 'B') return 'BUY — 建议关注'
  if (sig === 'H') return 'WATCH — 持续观察'
  if (sig === 'D') return 'SELL — 建议回避'
  return totalScore.value >= 85 ? 'BUY — 建议关注' : totalScore.value >= 70 ? 'WATCH — 持续观察' : 'SELL — 建议回避'
})
const signalColor = computed(() => {
  const txt = signalText.value
  if (txt.startsWith('BUY')) return 'var(--color-green)'
  if (txt.startsWith('WATCH')) return '#eab308'
  return 'var(--color-red)'
})
const consensusDetail = computed(() => {
  if (apiData.value?.decision?.reasoning) return apiData.value.decision.reasoning
  return buyCount.value >= 7 ? '多数模块看好，建议重点关注。' : buyCount.value >= 5 ? '存在分歧，建议观望。' : '多数模块看空，建议回避。'
})

// Add refs for new sections
const patternRef = ref(null)
const fundRef = ref(null)

const agents = [
  { name: 'Trend', vote: 'BUY', confidence: 87, reason: 'MA5/MA10/MA20三线向上发散，ADX=38确认趋势强度，当前位置趋势结构健康。' },
  { name: 'Volume', vote: 'BUY', confidence: 82, reason: '近5日量比1.32温和放量，OBV持续走高，主力资金净流入3.2亿。' },
  { name: 'Chip', vote: 'BUY', confidence: 91, reason: '筹码集中度34.5%趋于集中，获利比例72.3%，上方套牢盘压力较小。' },
  { name: 'Pattern', vote: 'WATCH', confidence: 68, reason: '日线级别呈现双底形态但颈线尚未有效突破，等待放量确认。' },
  { name: 'Risk', vote: 'BUY', confidence: 79, reason: 'ATR波动率1.56%可控，布林带中轨支撑有效，当前风险收益比合理。' },
  { name: 'Sector', vote: 'BUY', confidence: 85, reason: '板块RS强度>80，行业景气度向上，龙头股联动效应明显。' },
  { name: 'News', vote: 'BUY', confidence: 76, reason: '近期无重大利空，北向资金持续流入，市场情绪偏正面。' },
  { name: 'Macro', vote: 'WATCH', confidence: 65, reason: '宏观环境中性偏多，但海外不确定性仍存，需持续关注外围风险。' },
  { name: 'Research', vote: 'BUY', confidence: 88, reason: '综合评分88分，多数指标共振向上，建议纳入核心观察池。' },
  { name: 'Decision', vote: 'SELL', confidence: 58, reason: '虽然基本面和技术面偏多，但短期涨幅较大，追高风险增加。' },
]

const consensusText = computed(() => buyCount >= 7 ? '共识：BUY (7/2/1)' : '共识：WATCH')
const debateOpen = reactive({})
const toggleDebate = (i) => { debateOpen[i] = !debateOpen[i] }

const patterns = [
  { name: '双底', active: true }, { name: '头肩底', active: false }, { name: '杯柄', active: true },
  { name: '三角形', active: false }, { name: '旗形', active: false }, { name: '楔形', active: false },
  { name: '矩形', active: false }, { name: 'V形反转', active: false },
]

const fundamentals = [
  { label: '市盈率 PE', value: '24.3' }, { label: '市净率 PB', value: '8.5' },
  { label: 'ROE', value: '22.1%' }, { label: '营收增速', value: '+18.5%' },
  { label: '净利增速', value: '+25.3%' }, { label: '资产负债率', value: '42.0%' },
]

const consensusStyle = computed(() => buyCount >= 7
  ? 'background:rgba(33,208,122,.12);color:var(--color-green);border:1px solid rgba(33,208,122,.2)'
  : 'background:rgba(234,179,8,.12);color:#eab308;border:1px solid rgba(234,179,8,.2)'
)

// Refs
const headerRef = ref(null)
const klineRef = ref(null)
const indicatorsRef = ref(null)
const chipRef = ref(null)
const agentRef = ref(null)
const reportRef = ref(null)
const klineChartRef = ref(null)
const chipChartRef = ref(null)

function renderKline() {
  if (!klineChartRef.value) return
  const chart = echarts.init(klineChartRef.value)

  // Generate 30-day mock kline
  const dates = []
  const ohlc = []
  let p = basePrice.value * 0.9
  for (let i = 0; i < 30; i++) {
    const dt = new Date(2026, 5, 12 + i); dates.push(`${dt.getMonth()+1}/${dt.getDate()}`)
    p += (Math.random() - 0.45) * p * 0.03
    const o = +p.toFixed(2)
    const c = +(p * (1 + (Math.random() - 0.5) * 0.04)).toFixed(2)
    const l = +Math.min(o, c, o - Math.random() * p * 0.03).toFixed(2)
    const h = +Math.max(o, c, o + Math.random() * p * 0.03).toFixed(2)
    ohlc.push([o, c, l, h])
  }

  chart.setOption({
    grid: { left: 40, right: 16, top: 8, bottom: 24 },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#64748b', fontSize: 10 } },
    yAxis: { type: 'value', scale: true, axisLabel: { color: '#64748b', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,.04)' } } },
    series: [{
      type: 'candlestick',
      data: ohlc,
      itemStyle: { color: '#ff5b6e', color0: '#21d07a', borderColor: '#ff5b6e', borderColor0: '#21d07a' },
    }],
  })
}

function renderChip() {
  if (!chipChartRef.value) return
  const chart = echarts.init(chipChartRef.value)

  const x = []
  const y = []
  let cum = 0
  const peaks = [
    { center: 1150, w: 12, h: 0.8 },
    { center: 1180, w: 8, h: 1.0 },
    { center: 1200, w: 6, h: 0.5 },
    { center: 1170, w: 10, h: 0.6 },
  ]
  for (let i = 0; i < 60; i++) {
    const px = 1120 + i * 1.5
    let h = 0
    for (const pk of peaks) {
      h += pk.h * Math.exp(-((px - pk.center) ** 2) / (2 * pk.w ** 2))
    }
    x.push(px)
    cum += h
    y.push(cum)
  }

  chart.setOption({
    grid: { left: 40, right: 16, top: 8, bottom: 24 },
    xAxis: { type: 'category', data: x.map(v => v.toFixed(0)), axisLabel: { color: '#64748b', fontSize: 10, interval: 9 } },
    yAxis: { type: 'value', show: false },
    series: [{
      type: 'bar',
      data: y,
      itemStyle: { color: '#8b5cf6', borderRadius: [2,2,0,0] },
      barWidth: '95%',
    }],
  })
}

onMounted(async () => {
  await nextTick()
  fetchResearch()

  // Entrance animations
  const els = [headerRef, klineRef, indicatorsRef, chipRef, agentRef, reportRef]
  els.forEach((el, i) => {
    if (!el.value) return
    gsap.fromTo(el.value,
      { opacity: 0, y: 30, filter: 'blur(4px)' },
      { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.6, delay: 0.1 * i, ease: 'power3.out' }
    )
  })

  setTimeout(() => { renderKline(); renderChip() }, 300)
  if (patternRef.value) gsap.fromTo(patternRef.value, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.4, ease: 'power2.out' })
  if (fundRef.value) gsap.fromTo(fundRef.value, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.55, ease: 'power2.out' })
})
</script>
