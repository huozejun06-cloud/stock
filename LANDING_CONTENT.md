# Landing Content — 洞见 INSIGHT

> Landing Page 每一屏的文案、布局、CTA 规范。

---

## 第 1 屏: Hero

### 5 句 GSAP 文案 (逐句轮播)

1. 先看风险，再看机会。
2. 有人寻找机会，有人验证机会。
3. 不懂股票，也能读懂一家公司。
4. 不是替你决策，而是解释为什么。
5. AI 不会替代投资者，它会放大你的判断。

### 布局

| 属性 | 值 |
|------|-----|
| 高度 | 100vh |
| 文字位置 | 绝对定位，中心对齐 |
| 文字字体 | var(--font-hero) |
| 文字大小 | clamp(58px, 6vw, 86px) |
| 文字颜色 | 渐变 white -> gray-500 |
| CTA Primary | 开始体验 (橙色呼吸灯) |
| CTA Secondary | 了解方法 (透明边框) |

### 视频

| 属性 | 值 |
|------|-----|
| 文件 | /video/hero-bg.mp4 |
| 时长 | 12s |
| 格式 | 1080P 30fps H264 |
| 压暗 | brightness(.45) contrast(1.05) saturate(1.15) |

---

## 第 2 屏: 为什么相信 (Why Trust)

### 布局

4 个数字卡片:

| 数字 | 描述 |
|------|------|
| 5000+ | 实时扫描股票 |
| 23+ | 技术指标 |
| 10 | 协同分析模块 |
| 2s | 市场扫描速度 |

底部文案: 不是预测市场，而是帮助理解市场。

### 动画

数字使用 CountUp 动画。卡片 stagger 120ms。

---

## 第 3 屏: 为什么叫洞见

### 布局

左 (5): 文字
右 (7): Dashboard 视频

左标题: 真正重要的，不是预测涨跌。而是理解为什么。

### 视频

| 属性 | 值 |
|------|-----|
| 文件 | /video/dashboard.mp4 |
| 时长 | 8s |
| 内容 | Dashboard 缓慢旋转 + 指标浮现 |

---

## 第 4 屏: 协同研判

### 布局

左 (5): 文字
右 (7): Agent 视频

左标题: 不是 AI 替你拍板，而是十个维度共同验证。

10 张卡片: Trend / Volume / Chip / Pattern / Risk / Sector / News / Macro / Research / Decision

### 视频

| 属性 | 值 |
|------|-----|
| 文件 | /video/agent-committee.mp4 |
| 时长 | 10s |
| 内容 | 10 个模块依次亮灯 -> Consensus 94% BUY |

---

## 第 5 屏: 研究方法

### 内部结构

方法论文案 + 数据来源卡片 + AI 流程图 + 技术架构卡片

### 视频

| 属性 | 值 |
|------|-----|
| 文件 | /video/methodology.mp4 |
| 时长 | 8s |
| 内容 | 系统流程动态流光 |

---

## 第 6 屏: 数据来源

4 张卡片: 东方财富 / AKShare / TuShare / DeepSeek

---

## 第 7 屏: Footer

洞见 INSIGHT / Version 3.2 / Built with Vue3 + FastAPI + Python + DeepSeek + ECharts + GSAP

---

## 视频汇总

| # | 文件 | 时长 | 内容 |
|---|------|------|------|
| 1 | hero-bg.mp4 | 12s | 云海->K线->光照 |
| 2 | dashboard.mp4 | 8s | Dashboard旋转 |
| 3 | agent-committee.mp4 | 10s | Agent亮灯->Consensus |
| 4 | research.mp4 | 10s | 研究报告滚动 |
| 5 | methodology.mp4 | 8s | 系统流程流光 |
