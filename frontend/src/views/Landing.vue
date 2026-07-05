<template>
  <div id="landing-page">
    <HeroSection />
    <WhyTrustSection />
    <WhyInsightSection />

    <!-- Screen 4: 协同研判 -->
    <section ref="committeeSection" class="py-[var(--space-section)]" style="background: var(--color-bg)">
      <div class="mx-auto px-6" style="max-width: var(--space-container)">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div ref="committeeText" class="lg:col-span-5">
            <h2 class="text-4xl md:text-5xl font-normal leading-tight mb-6" style="font-family: var(--font-hero); color: var(--text-primary); opacity: 0">
              不是 AI 替你拍板，<br />而是十个维度<br />共同验证。
            </h2>
            <p class="text-lg leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body); opacity: 0">
              Trend / Volume / Chip / Pattern / Risk / Sector / News / Macro / Research / Decision —— 每个维度独立分析，最后委员会投票形成共识。
            </p>
          </div>
          <div ref="committeeMedia" class="lg:col-span-7">
            <div class="glass-card overflow-hidden aspect-video flex items-center justify-center" style="opacity: 0">
              <div class="text-center" style="color: var(--text-dim); font-family: var(--font-body)">
                <div class="text-6xl mb-4">🧠</div>
                <p class="text-sm">协同研判视频将在此展示</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Screen 5: 研究方法 -->
    <section id="methodology" ref="methodSection" class="py-[var(--space-section)]" style="background: var(--color-bg)">
      <div class="mx-auto px-6" style="max-width: var(--space-container)">
        <h2 class="text-4xl md:text-5xl font-normal leading-tight mb-16 text-center" style="font-family: var(--font-hero); color: var(--text-primary); opacity: 0">
          为什么值得相信？
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          <div
            v-for="(item, i) in methodologyItems"
            :key="item.title"
            :ref="el => { if (el) methodCardRefs[i] = el }"
            class="glass-card p-8 cursor-pointer"
            :class="{ 'ring-1 ring-white/10': expanded['method-'+i] }"
            @click="toggleExpand('method-'+i)"
            style="opacity: 0"
          >
            <h3 class="text-xl font-semibold mb-3" style="color: var(--text-primary); font-family: var(--font-body)">{{ item.title }}</h3>
            <p class="text-sm leading-relaxed" style="color: var(--text-secondary); font-family: var(--font-body)">{{ item.desc }}</p>
            <div v-if="expanded['method-'+i]" class="mt-4 pt-4 text-xs leading-relaxed" style="color: var(--text-dim); border-top: 1px solid rgba(255,255,255,.05); font-family: var(--font-body)" v-html="item.detail"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Screen 6: 数据来源 -->
    <section ref="dataSection" class="py-[var(--space-section)]" style="background: var(--color-bg)">
      <div class="mx-auto px-6" style="max-width: var(--space-container)">
        <h2 class="text-4xl md:text-5xl font-normal leading-tight mb-16 text-center" style="font-family: var(--font-hero); color: var(--text-primary); opacity: 0">
          多源数据，交叉验证
        </h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 items-start">
          <div
            v-for="(src, i) in dataSources"
            :key="src.name"
            :ref="el => { if (el) dataCardRefs[i] = el }"
            class="glass-card p-6 text-center cursor-pointer"
            :class="{ 'ring-1 ring-white/10': expanded['src-'+i] }"
            @click="toggleExpand('src-'+i)"
            style="opacity: 0"
          >
            <div class="text-3xl mb-3">{{ src.icon }}</div>
            <div class="text-sm font-semibold mb-1" style="color: var(--text-primary); font-family: var(--font-body)">{{ src.name }}</div>
            <div class="text-xs" style="color: var(--text-dim); font-family: var(--font-body)">{{ src.desc }}</div>
            <div v-if="expanded['src-'+i]" class="mt-3 pt-3 text-xs leading-relaxed" style="color: var(--text-dim); border-top: 1px solid rgba(255,255,255,.05); font-family: var(--font-body)" v-html="src.detail"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer ref="footerSection" class="py-16" style="background: #060810; border-top: 1px solid rgba(255,255,255,.05); opacity: 0">
      <div class="mx-auto px-6 text-center" style="max-width: var(--space-container)">
        <div class="mb-4">
          <span class="text-lg font-semibold" style="color: var(--text-primary); font-family: var(--font-hero)">洞见</span>
          <span class="text-xs tracking-widest ml-2" style="color: var(--text-dim); font-family: var(--font-number)">INSIGHT</span>
        </div>
        <p class="text-xs mb-2" style="color: var(--text-dim); font-family: var(--font-body)">Version 3.2 · Built with Vue3 + FastAPI + Python + DeepSeek + ECharts + GSAP</p>
        <p class="text-xs" style="color: var(--text-dim); font-family: var(--font-body)">© 2026 洞见 INSIGHT. AI 量化投资研究平台。</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import HeroSection from '@/components/landing/HeroSection.vue'
import WhyTrustSection from '@/components/landing/WhyTrustSection.vue'
import WhyInsightSection from '@/components/landing/WhyInsightSection.vue'

gsap.registerPlugin(ScrollTrigger)

const expanded = reactive({})
const toggleExpand = (key) => { expanded[key] = !expanded[key] }

// Refs for ScrollTrigger
const committeeSection = ref(null)
const committeeText = ref(null)
const committeeMedia = ref(null)
const methodSection = ref(null)
const methodCardRefs = ref([])
const dataSection = ref(null)
const dataCardRefs = ref([])
const footerSection = ref(null)

// Helper: animate section entrance
function animateSection(triggerEl, targets, opts = {}) {
  if (!triggerEl || !targets) return
  ScrollTrigger.create({
    trigger: triggerEl,
    start: 'top 75%',
    onEnter: () => {
      gsap.fromTo(targets,
        { opacity: 0, y: 40, scale: 0.97, filter: 'blur(6px)' },
        { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 0.8, stagger: opts.stagger || 0.1, ease: 'power3.out' }
      )
    },
  })
}

onMounted(async () => {
  await nextTick()

  // Committee section
  if (committeeSection.value && committeeText.value && committeeMedia.value) {
    const h2 = committeeText.value.querySelector('h2')
    const p = committeeText.value.querySelector('p')
    const card = committeeMedia.value.querySelector('.glass-card')
    ScrollTrigger.create({
      trigger: committeeSection.value,
      start: 'top 75%',
      onEnter: () => {
        if (h2) gsap.fromTo(h2, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' })
        if (p) gsap.fromTo(p, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.8, delay: 0.2, ease: 'power3.out' })
        if (card) gsap.fromTo(card, { opacity: 0, x: 30, scale: 0.97 }, { opacity: 1, x: 0, scale: 1, duration: 0.8, delay: 0.1, ease: 'power3.out' })
      },
    })
  }

  // Methodology cards
  animateSection(methodSection.value, methodCardRefs.value.filter(Boolean))
  const methodTitle = methodSection.value?.querySelector('h2')
  if (methodTitle) {
    ScrollTrigger.create({
      trigger: methodTitle,
      start: 'top 85%',
      onEnter: () => gsap.to(methodTitle, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }),
    })
  }

  // Data source cards
  animateSection(dataSection.value, dataCardRefs.value.filter(Boolean))
  const dataTitle = dataSection.value?.querySelector('h2')
  if (dataTitle) {
    ScrollTrigger.create({
      trigger: dataTitle,
      start: 'top 85%',
      onEnter: () => gsap.to(dataTitle, { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }),
    })
  }

  // Footer
  if (footerSection.value) {
    ScrollTrigger.create({
      trigger: footerSection.value,
      start: 'top 90%',
      onEnter: () => gsap.to(footerSection.value, { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }),
    })
  }
})

const methodologyItems = [
  { title: '先排雷，再选股', desc: 'MA20 趋势、ATR 波动率、BIAS 乖离率、MACD 共振、资金流向五道风险红线，先过滤掉高风险股票。', detail: '<b>五道风险红线：</b><br/>① MA20 趋势：股价必须站上 MA20，排除下行趋势<br/>② ATR 波动率：排除异常波动个股<br/>③ BIAS 乖离率：偏离均线过远时预警回调风险<br/>④ MACD 共振：DIF/DEA/柱状线三重确认<br/>⑤ 资金流向：主力资金连续流出则亮红灯' },
  { title: '六维评分体系', desc: '趋势结构、资金流向、筹码分布、形态识别、板块热度、情绪周期六个维度交叉验证，每个维度独立打分。', detail: '<b>六维权重：</b><br/>趋势结构 35% · 资金流向 15%<br/>筹码分布 25% · 形态识别 15%<br/>板块热度 10% · 情绪周期 5%<br/><br/>最终分数 > 70 进入候选池。' },
  { title: '协同研判', desc: '10 个分析模块独立运转，最终委员会投票达成共识。不是单一 AI 拍板，而是多角度交叉验证。', detail: '<b>委员会 10 模块：</b><br/>Trend · Volume · Chip · Pattern · Risk<br/>Sector · News · Macro · Research · Decision<br/><br/>BUY (≥7票) · WATCH (5-6票) · SELL (≤4票)' },
  { title: '量化背后的逻辑', desc: '不追求预测涨跌，而是通过 23 项技术指标量化每一只股票的多空力量对比。', detail: '<b>23 项指标涵盖：</b><br/>趋势族: MA/ADX · 动量族: MACD/RSI/KDJ<br/>波动族: BOLL/ATR · 量价族: OBV/量比<br/>筹码族: 获利比例/集中度 · 形态族: 12 种形态' },
  { title: '数据层层清洗', desc: '东方财富、同花顺、腾讯三源交叉验证，AKShare 补充历史，确保每一条行情数据真实可靠。', detail: '<b>三级降级策略：</b><br/>第 1 级：东方财富（最快实时行情）<br/>第 2 级：同花顺（备用实时源）<br/>第 3 级：腾讯财经（兜底保障）<br/><br/>任意一级失败自动降级。' },
  { title: 'AI 解释，不决定', desc: 'AI 的责任是解释为什么一只股票值得关注，而不是替你决定买还是不买。', detail: '<b>AI 的角色边界：</b><br/>✅ 负责：指标解读、风险提示、逻辑推理、研报生成<br/>❌ 不做：买卖建议、仓位管理、价格预测<br/><br/>最终决策权始终在你手中。' },
]

const dataSources = [
  { name: '东方财富', desc: '实时行情 · 2秒更新', icon: '📈', detail: '主力实时行情源，覆盖沪深全部 A 股。Tick 级行情、盘口五档、逐笔成交。数据延迟 < 2 秒。' },
  { name: 'AKShare', desc: '历史数据 · 基本面', icon: '📦', detail: '开源金融数据接口，覆盖 A 股/港股/美股/期货/外汇。200+ 数据接口。' },
  { name: 'TuShare', desc: '财务数据 · 因子', icon: '📊', detail: '专业量化平台，资产负债表、利润表、现金流量表等深度财务数据。' },
  { name: 'DeepSeek', desc: '新闻理解 · 推理', icon: '🧠', detail: '大语言模型。公告解读、新闻情绪分析、研报关键信息提取。支持多轮推理。' },
]
</script>
