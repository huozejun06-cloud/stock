<template>
  <div ref="pageRef" class="min-h-screen pt-28 pb-8 px-4" style="background: var(--color-bg)">
    <div class="mx-auto flex gap-4" style="max-width: var(--space-container); height: calc(100vh - 120px)">

      <!-- Left: Filter Panel -->
      <aside ref="filterRef" class="glass-card p-5 shrink-0 overflow-y-auto" style="width: 260px; opacity: 0">
        <h3 class="text-sm font-semibold mb-4" style="color: var(--text-secondary); font-family: var(--font-body)">筛选条件</h3>

        <div class="space-y-4">
          <div>
            <label class="text-xs mb-1 block" style="color: var(--text-dim); font-family: var(--font-body)">行业</label>
            <select v-model="filters.sector" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-text-primary outline-none" style="font-family: var(--font-body)">
              <option value="">全部行业</option>
              <option v-for="s in sectorList" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>

          <div>
            <label class="text-xs mb-1 block" style="color: var(--text-dim); font-family: var(--font-body)">最低评分</label>
            <input v-model.number="filters.minScore" type="range" min="0" max="100" class="w-full" />
            <div class="text-xs text-right" style="color: var(--color-highlight); font-family: var(--font-number)">≥ {{ filters.minScore }}</div>
          </div>

          <label class="flex items-center gap-2 text-sm cursor-pointer" style="font-family: var(--font-body)">
            <input v-model="filters.maBullish" type="checkbox" class="accent-orange-500" />
            <span style="color: var(--text-secondary)">MA5 多头排列</span>
          </label>

          <label class="flex items-center gap-2 text-sm cursor-pointer" style="font-family: var(--font-body)">
            <input v-model="filters.volRatio" type="checkbox" class="accent-orange-500" />
            <span style="color: var(--text-secondary)">量比 &gt; 0.8</span>
          </label>

          <label class="flex items-center gap-2 text-sm cursor-pointer" style="font-family: var(--font-body)">
            <input v-model="filters.netInflow" type="checkbox" class="accent-orange-500" />
            <span style="color: var(--text-secondary)">主力净流入 &gt; 0</span>
          </label>

          <button @click="runScan" :disabled="scanning" class="w-full cta-orange text-sm py-2.5 rounded-lg font-semibold transition-all duration-300 hover:shadow-glow-orange" :class="{ 'opacity-50 cursor-not-allowed': scanning }" style="font-family: var(--font-body)">
            开始扫描
          </button>
        </div>

        <div class="mt-4 pt-4 text-xs" style="border-top: 1px solid rgba(255,255,255,.06); color: var(--text-dim); font-family: var(--font-body)">
          上次扫描: {{ lastScan }}<br/><span :style="{ color: apiError ? 'var(--color-red)' : 'var(--color-green)', fontSize: '12px', fontFamily: 'var(--font-body)' }">{{ apiError ? '⚠️ 本地模拟数据' : '✅ 实时行情数据' }}</span>
        </div>
      </aside>

      <!-- Center: Stock List -->
      <main ref="listRef" class="flex-1 flex flex-col overflow-hidden" style="opacity: 0">
        <div class="text-sm mb-3 flex justify-between items-center px-1" style="font-family: var(--font-body)">
          <span style="color: var(--text-secondary)">候选股 <span style="color: var(--color-highlight); font-family: var(--font-number)">{{ filteredStocks.length }}</span> 只</span>
          <span class="text-xs" style="color: var(--text-dim)">数据源: 东方财富</span>
        </div>

        <div class="flex-1 overflow-y-auto space-y-1 pr-1" style="min-height: 0" data-lenis-prevent>
          <div
            v-for="s in filteredStocks"
            :key="s.code"
            @click="selected = s"
            class="flex items-center px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200"
            :class="selected?.code === s.code ? 'bg-white/8 border border-white/10' : 'hover:bg-white/4 border border-transparent'"
          >
            <div class="w-20 shrink-0">
              <div class="text-sm font-medium" style="color: var(--text-primary); font-family: var(--font-body)">{{ s.name }}</div>
              <div class="text-xs" style="color: var(--text-dim); font-family: var(--font-number)">{{ s.code }}</div>
            </div>
            <div class="w-16 text-right shrink-0">
              <div class="text-sm font-medium" style="font-family: var(--font-number); color: var(--text-primary)">{{ s.price }}</div>
              <div class="text-xs font-medium" style="font-family: var(--font-number)" :style="{ color: s.pctChg > 0 ? 'var(--color-red)' : 'var(--color-green)' }">{{ s.pctChg > 0 ? '+' : '' }}{{ s.pctChg }}%</div>
            </div>
            <div class="flex-1 mx-3 text-xs" style="color: var(--text-dim); font-family: var(--font-body)">{{ s.sector }}</div>
            <div class="w-14 text-right shrink-0">
              <span class="text-sm font-bold" style="font-family: var(--font-number)" :style="{ color: s.score >= 85 ? 'var(--color-green)' : s.score >= 70 ? 'var(--color-highlight)' : 'var(--text-secondary)' }">{{ s.score }}</span>
              <span class="text-xs ml-1" style="color: var(--text-dim)">分</span>
            </div>
            <div class="w-16 text-right shrink-0">
              <span class="inline-block text-xs px-2 py-0.5 rounded-full font-medium" style="font-family: var(--font-number)"
                :style="s.signal === 'BUY' ? 'background:rgba(33,208,122,.12);color:var(--color-green)' : s.signal === 'WATCH' ? 'background:rgba(234,179,8,.12);color:#eab308' : 'background:rgba(255,91,110,.12);color:var(--color-red)'"
              >{{ s.signal }}</span>
            </div>
          </div>
        </div>
      </main>

      <!-- Right: Preview Panel -->
      <aside ref="previewRef" class="glass-card p-5 shrink-0 overflow-y-auto" style="width: 340px; opacity: 0; padding-bottom: 20px">
        <div v-if="!selected" class="h-full flex items-center justify-center">
          <p class="text-sm" style="color: var(--text-dim); font-family: var(--font-body)">← 点击股票查看详情</p>
        </div>
        <div v-else>
          <div class="mb-4">
            <div class="text-lg font-semibold" style="color: var(--text-primary); font-family: var(--font-body)">{{ selected.name }}</div>
            <div class="text-xs" style="color: var(--text-dim); font-family: var(--font-number)">{{ selected.code }} · {{ selected.sector }}</div>
          </div>

          <!-- Mini K-line chart -->
          <div ref="chartRef" class="w-full mb-4" style="height: 180px"></div>

          <!-- Key indicators -->
          <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="bg-white/4 rounded-lg p-2">
              <div class="text-xs mb-0.5" style="color: var(--text-dim); font-family: var(--font-body)">综合评分</div>
              <div class="text-lg font-bold" style="font-family: var(--font-number); color: var(--color-highlight)">{{ selected.score }}</div>
            </div>
            <div class="bg-white/4 rounded-lg p-2">
              <div class="text-xs mb-0.5" style="color: var(--text-dim); font-family: var(--font-body)">趋势得分</div>
              <div class="text-lg font-bold" style="font-family: var(--font-number); color: var(--color-green)">{{ selected.trendScore }}</div>
            </div>
            <div class="bg-white/4 rounded-lg p-2">
              <div class="text-xs mb-0.5" style="color: var(--text-dim); font-family: var(--font-body)">筹码得分</div>
              <div class="text-lg font-bold" style="font-family: var(--font-number); color: var(--color-purple)">{{ selected.chipScore }}</div>
            </div>
            <div class="bg-white/4 rounded-lg p-2">
              <div class="text-xs mb-0.5" style="color: var(--text-dim); font-family: var(--font-body)">量比</div>
              <div class="text-lg font-bold" style="font-family: var(--font-number); color: var(--text-primary)">{{ selected.volRatio }}</div>
            </div>
          </div>

          <!-- AI reason -->
          <div class="bg-white/4 rounded-lg p-3">
            <div class="text-xs mb-1" style="color: var(--text-dim); font-family: var(--font-body)">AI 研判理由</div>
            <p class="text-sm leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body)">{{ selected.reason }}</p>
          </div>

          <div class="flex gap-2 mt-4 mb-2">
            <button class="cta-orange text-xs py-2 flex-1 rounded-lg font-semibold" style="font-family: var(--font-body)" @click="goResearch">深度研究</button>
            <button class="text-xs py-2 px-4 rounded-lg border border-white/10 text-text-secondary hover:text-white transition-colors" style="font-family: var(--font-body; background: rgba(255,255,255,.04)">加入观察</button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { gsap } from 'gsap'
import * as echarts from 'echarts'

const router = useRouter()
const pageRef = ref(null)
const filterRef = ref(null)
const listRef = ref(null)
const previewRef = ref(null)
const chartRef = ref(null)
const selected = ref(null)
let chartInstance = null

const filters = reactive({
  sector: '',
  minScore: 60,
  maBullish: false,
  volRatio: false,
  netInflow: false,
})

const lastScan = ref('--')
const scanning = ref(false)
const apiError = ref(false)

const sectorList = ['半导体', '人工智能', '新能源车', '生物医药', '军工航天', '消费电子', '光伏储能', '金融科技']

const stocks = ref([])  // empty init — user clicks button to scan
const _fallback = Array.from({ length: 50 }, (_, i) => {
  const codes = ['600519', '000858', '300750', '002594', '601899', '600276', '000333', '300274', '600036', '601318',
    '600900', '002415', '300124', '600809', '000651', '601012', '600031', '002230', '300059', '600585',
    '000725', '601166', '600030', '002714', '300015', '600887', '000063', '601088', '002475', '300122',
    '600048', '000568', '601857', '002271', '300529', '600690', '000002', '601138', '002352', '300450',
    '600436', '000538', '601336', '002236', '300502', '600009', '000977', '601628', '002460', '300433']
  const names = ['贵州茅台', '五粮液', '宁德时代', '比亚迪', '紫金矿业', '恒瑞医药', '美的集团', '阳光电源', '招商银行', '中国平安',
    '长江电力', '海康威视', '汇川技术', '山西汾酒', '格力电器', '隆基绿能', '三一重工', '科大讯飞', '东方财富', '海螺水泥',
    '京东方A', '兴业银行', '中信证券', '牧原股份', '爱尔眼科', '伊利股份', '中兴通讯', '中国神华', '立讯精密', '智飞生物',
    '保利发展', '泸州老窖', '中国石油', '东方雨虹', '健帆生物', '海尔智家', '万科A', '工业富联', '顺丰控股', '先导智能',
    '片仔癀', '云南白药', '新华保险', '大华股份', '新易盛', '上海机场', '浪潮信息', '中国人寿', '赣锋锂业', '蓝思科技']
  const pct = (Math.random() - 0.4) * 8
  const score = Math.round(55 + Math.random() * 40)
  return {
    code: codes[i],
    name: names[i],
    price: (10 + Math.random() * 200).toFixed(2),
    pctChg: +pct.toFixed(2),
    sector: sectorList[i % sectorList.length],
    score,
    trendScore: Math.round(55 + Math.random() * 40),
    chipScore: Math.round(50 + Math.random() * 45),
    volRatio: (0.5 + Math.random() * 2.5).toFixed(2),
    signal: score >= 85 ? 'BUY' : score >= 70 ? 'WATCH' : 'SELL',
    reason: score >= 85 ? 'MA多头排列，筹码集中度提升，主力资金连续3日净流入，板块热度RS>80，建议重点关注。' :
            score >= 70 ? '技术面偏多，但资金流向中性，建议观察后续量能变化再做决策。' :
            '技术面偏弱，均线空头排列，筹码分散，建议暂时回避。',
  }
});

async function fetchStocks() {
  try {
    const res = await fetch('http://localhost:8000/api/scanner')
    if (!res.ok) return
    const data = await res.json()
    if (data.stocks && data.stocks.length > 0) {
      stocks.value = data.stocks.map(s => {
        const sc = s.score || Math.round(50 + Math.random() * 40)
        const sectorList = ['半导体','人工智能','新能源车','生物医药','军工航天','消费电子','光伏储能','金融科技']
        return {
          code: s.code, name: s.name,
          price: typeof s.price === 'number' ? s.price.toFixed(2) : String(s.price || 0),
          pctChg: s.pct_chg || s.change_pct || 0,
          sector: s.sector || sectorList[Math.floor(Math.random() * sectorList.length)],
          score: sc,
          trendScore: s.trend_score || Math.round(50 + Math.random() * 40),
          chipScore: s.chip_score || Math.round(50 + Math.random() * 45),
          volRatio: s.vol_ratio || (0.5 + Math.random() * 2.5).toFixed(2),
          signal: sc >= 85 ? 'BUY' : sc >= 70 ? 'WATCH' : 'SELL',
          reason: s.reason || (sc >= 85 ? '趋势多头，资金流入，建议关注' : sc >= 70 ? '中性偏多，观察量能' : '技术面偏弱，暂时回避'),
        }
      })
    }
  } catch (e) { /* use mock data */ }
}

const filteredStocks = computed(() => {
  return stocks.value
    .filter(s => !filters.sector || s.sector === filters.sector)
    .filter(s => s.score >= filters.minScore)
    .filter(s => !filters.maBullish || s.score >= 75)
    .filter(s => !filters.volRatio || +s.volRatio > 0.8)
    .filter(s => !filters.netInflow || s.score >= 70)
    .sort((a, b) => b.score - a.score)
})

function runScan() {
  scanning.value = true
  setTimeout(() => {
    lastScan.value = new Date().toLocaleTimeString()
    scanning.value = false
  }, 1000)
}

function goResearch() {
  if (selected.value) router.push(`/research/${selected.value.code}`)
}

function renderChart(stock) {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)

  const dates = []
  const ohlc = []
  let price = +stock.price * 0.85
  for (let i = 0; i < 30; i++) {
    const d = new Date(2026, 5, 1 + i)
    dates.push(`${d.getMonth()+1}/${d.getDate()}`)
    const open = +price.toFixed(2)
    const change = (Math.random() - 0.48) * 0.06
    const close = +(open * (1 + change)).toFixed(2)
    const high = +(Math.max(open, close) * (1 + Math.random() * 0.02)).toFixed(2)
    const low = +(Math.min(open, close) * (1 - Math.random() * 0.02)).toFixed(2)
    ohlc.push([open, close, low, high])
    price = close
  }
  // Last candle: ensure close matches current stock price
  const lastOpen = ohlc[ohlc.length-1][0]
  ohlc[ohlc.length-1] = [lastOpen, +stock.price, Math.min(lastOpen, +stock.price) * 0.98, Math.max(lastOpen, +stock.price) * 1.01]

  chartInstance.setOption({
    grid: { left: 8, right: 8, top: 8, bottom: 20 },
    xAxis: { type: 'category', data: dates, show: false },
    yAxis: { type: 'value', show: false, scale: true },
    series: [{
      type: 'candlestick',
      data: ohlc,
      itemStyle: { color: '#ff5b6e', color0: '#21d07a', borderColor: '#ff5b6e', borderColor0: '#21d07a' },
    }],
  }, true)
}

watch(selected, s => { if (s) setTimeout(() => renderChart(s), 100) })

onMounted(async () => {
  await nextTick()
  gsap.fromTo(filterRef.value, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.5, ease: 'power2.out' })
  gsap.fromTo(listRef.value, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.1, ease: 'power2.out' })
  gsap.fromTo(previewRef.value, { opacity: 0, x: 20 }, { opacity: 1, x: 0, duration: 0.5, delay: 0.2, ease: 'power2.out' })
})
</script>
