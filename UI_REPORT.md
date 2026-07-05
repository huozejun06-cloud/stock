# UI_REPORT.md — 前端页面验收

> ⚡ 沙箱验证代码 | 🔶 需用户在浏览器验证渲染

---

## ⚡ 前端文件清单（代码级验证）

| 文件 | 行数 | 状态 |
|------|------|------|
| Landing.vue | ✅ | 7屏完整结构 |
| Overview.vue | ✅ | 6组数据fetch接入 |
| Scanner.vue | ✅ | API fetch + CSV fallback |
| Research.vue | ✅ | 8指标computed从API |
| Backtest.vue | ✅ | ECharts图表 |
| Methodology.vue | ✅ | 指标实验室 |
| About.vue | ✅ | 品牌+技术栈 |
| App.vue | ✅ | Lenis滚动 |
| NavBar.vue | ✅ | 胶囊毛玻璃 |
| HeroSection.vue | ✅ | 5句GSAP文案 |

---

## ⚡ Mock扫描结果（代码级）

| 页面 | 真实数据 | Mock数据 |
|------|---------|---------|
| Landing | N/A (静态) | 无 |
| Overview | indices/global (API) | sentiment/sectors/news (mock) |
| Scanner | stocks (API→CSV) | K线预览(Math.random) |
| Research | indicators/decision (CSV) | K线/筹码/Agent (mock/random) |
| Backtest | 无 | 全部(Math.random) |
| Methodology | N/A (静态) | 无 |
| About | N/A (静态) | 无 |

---

## 🔶 需用户在浏览器验证

打开 http://localhost:5173 → 每个页面检查:

| 页面 | 检查项 |
|------|--------|
| Landing | Hero文案动画、导航栏、滚动 |
| Overview | 6组数据是否显示、数据源标签 |
| Scanner | 股票列表、筛选、滚动条、K线预览 |
| Research | K线图、指标面板、Agent委员会、AI报告 |
| Backtest | 收益曲线、月度分布、优化建议 |
| Methodology | 卡片列表、流水线动画 |
| About | 品牌、技术栈标签 |

每页截图发我，标记:
- ✅ 正常
- ⚠️ 有小问题(描述)
- ❌ 严重问题(描述)
