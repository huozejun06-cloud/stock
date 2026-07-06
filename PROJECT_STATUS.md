
# StockQuant — 项目完整状态文档
> 最后更新: 2026-07-06 | Git HEAD: f9648a3

---

## 已完成阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase A-H | 后端完整 (33工具库/10 Agent/4 API/Pipeline) | ✅ |
| Phase D | 前端 7页+7组件+设计系统+动画 | ✅ |
| E-1 | K线缓存 5365只 153MB 到2026-07-03 | ✅ |
| E-2 | /api/overview 聚合端点 | ✅ |
| E-3 | Overview 接真实API | ✅ |
| E-4 | Research 接真实API (indicators/decision/key_levels) | ✅ |
| P0 Debug | 20+个修复 (见下方) | ✅ |
| GitHub | 代码已推送 huozejun06-cloud/stock | ✅ |

## P0 Debug 已修复 (20+项目)

### 后端数据链路
| # | 问题 | 文件 | Commit |
|---|------|------|--------|
| 1 | ws.py DataFrame→list遍历列名而非行 | ws.py | 5316e9e |
| 2 | ws.py 字段中英文不匹配(code/代码...) | ws.py | d4c0068 |
| 3 | DataSourceManager .empty无hasattr守卫 | 数据源管理器.py | da4b7f9 |
| 4 | scanner data_source标签错误(live/cache/mock) | scanner.py | 756bf25 |
| 5 | ws.py 过滤code缺中文fallback | ws.py | bc0c52b |
| 6 | DataSourceManager 最新价未入result dict | 数据源管理器.py | ece10a1 |
| 7 | ws.py 变量名不对齐 df→stocks | ws.py | f2c4a5c |
| 8 | ws.py isinstance(dict)守卫 | ws.py | eb3570d |
| 9 | DataFrame.to_dict('records')缺失 | ws.py | 5316e9e |
| 10 | 板块过滤前置到Top50之前 | ws.py | b611e07 |
| 11 | 非交易时段降级CSV缓存真实价 | scanner.py | a5986fb |

### 前端
| # | 问题 | 文件 | Commit |
|---|------|------|--------|
| 12 | 滚动: Lenis拦截滚轮事件 | Scanner.vue | be7641e |
| 13 | 滚动: 三层(height+overflow+min-height) | Scanner.vue | 5191190 |
| 14 | stocks初始化为空数组 | Scanner.vue | 1ca9742 |
| 15 | runScan未调fetchStocks | Scanner.vue | f9648a3 |
| 16 | fallbackStocks未赋值 | Scanner.vue | f9648a3 |
| 17 | catch块为空 | Scanner.vue | f9648a3 |
| 18 | fetchStocks未在onMounted调用 | Scanner.vue | 65a05e6 |
| 19 | apiError未声明 | Scanner.vue | 8b395db |
| 20 | Backtest optimizations未声明 | Backtest.vue | eb3570d |
| 21 | Research K线日期修复(6.40→真日期) | Research.vue | b611e07 |

## 当前数据流状态

### Scanner
- API: ✅ Source=live, 同花顺/腾讯可达，东方财富被proxy阻断
- 腾讯API: 扫描4658只 ✅
- 板块过滤: ws.py + scanner.py 双层过滤300/688/8xx
- 价格: 🟡 腾讯批次API parts[3]对部分股不可靠
- 滚动: ✅ data-lenis-prevent修复
- 按钮: ✅ 点击触发扫描

### Research
- API: ✅ /api/research/{code} 从CSV计算真实指标
- K线: ❌ Math.random mock
- 筹码: ❌ mock
- Agent投票: ❌ mock

### Overview
- indices: 🟡 mixed (try real → mock)
- sentiment: 🟡 mock (非交易时段)
- sectors/news/ai_logs: ❌ mock

## 剩余Bug

| # | 优先级 | 问题 | 位置 |
|---|--------|------|------|
| 1 | 🔴 P0 | 腾讯批次API parts[3]价格不准 | 数据源管理器.py |
| 2 | 🔴 P0 | 板块信息随机生成 | Scanner.vue fetchStocks |
| 3 | 🟡 P1 | Research K线为mock | Research.vue |
| 4 | 🟡 P1 | Overview 情绪/板块/快讯mock | overview.py |
| 5 | 🟡 P1 | 东方财富API proxy阻断 | git config + 数据源管理器.py |
| 6 | 🟢 P2 | NavBar Research硬编码600519 | NavBar.vue |
| 7 | 🟢 P3 | 视频文件未提供 | Landing.vue |

## 关键文件路径

### 后端
- server/app.py — FastAPI入口, 4路由注册
- server/routes/scanner.py — /api/scanner (含_cache_stocks降级)
- server/routes/ws.py — _scan_market_top50 (过滤+字段映射)
- server/routes/research.py — /api/research/{code} (CSV计算指标)
- server/routes/overview.py — /api/overview (6组聚合)
- 工具库/数据源管理器.py — DataSourceManager (腾讯/同花顺/东财)
- agents/pipeline.py — Agent全市场选股流水线

### 前端
- frontend/src/views/Scanner.vue — 扫描页 (fetchStocks/runScan/过滤)
- frontend/src/views/Research.vue — 研究页 (indicators computed)
- frontend/src/views/Overview.vue — 看板页 (fetchOverview)
- frontend/src/App.vue — Lenis全局滚动
- frontend/src/components/layout/NavBar.vue — 导航栏
- frontend/src/components/landing/HeroSection.vue — Hero首屏

### 数据
- data/kline/ — 5365个CSV缓存, 153MB, 到2026-07-03
- config.py — CACHE_DIR=data/kline

## 规范文档

| 文档 | 行数 | 用途 |
|------|------|------|
| WORKFLOW_RULES.md | 286 | 工作流+铁律§1-§17 |
| PROJECT_STATUS.md | 本文件 | 项目状态 |
| DESIGN_SYSTEM.md | 99 | 设计Token |
| MOTION_SYSTEM.md | 89 | 动画规范 |
| LANDING_CONTENT.md | 137 | Landing文案 |
| PRODUCT_SPEC.md | 65 | 产品架构 |
| CODING_RULES.md | 68 | 编码规范 |
| FRONTEND_SPEC.md | 376 | 前端完整规范 |



## 当前已知 Bug 列表 (2026-07-06)

| # | 优先级 | 问题 | 位置 | 状态 |
|---|--------|------|------|------|
| 1 | 🔴 P0 | DataSourceManager 'str' object has no attribute 'get' | ws.py | ✅ 已修复 `isinstance(dict)` |
| 1a | 🔴 P0 | data_source 标签误导 | scanner.py | ✅ 已修复 `is_cache` 标志 |
| 1b | 🔴 P0 | git proxy 残留 | git config | ✅ 已清除 |
| 2 | 🔴 P0 | 腾讯 API parts[3] 价格不准 (600048=156.41 实际 4.68) | 数据源管理器.py | ❌ 待修 |
| 3 | 🟡 P1 | Scanner 滚动条 | Scanner.vue | ✅ 已修复 `data-lenis-prevent` |
| 4 | 🟡 P1 | 股票自动显示 (未点按钮就有) | Scanner.vue | ✅ 已修复 `stocks=ref([])` |
| 5 | 🟡 P1 | 688/300 未过滤 | ws.py | ✅ 已修复双名查找 |
| 6 | 🟡 P1 | Research K 线 mock | Research.vue | ❌ |
| 7 | 🟡 P1 | Overview 情绪/快讯/板块 mock | overview.py | ❌ |
| 8 | 🟢 P2 | Backtest optimizations 未声明 | Backtest.vue | ✅ 已修复 |
| 9 | 🟢 P2 | NavBar Research 硬编码 600519 | NavBar.vue | ❌ |
| 10 | ⚪ P3 | 视频文件未提供 | Landing 各页 | ❌ |
| 11 | ⚪ P3 | Backtest 全 mock | Backtest.vue | ❌ |

## 启动命令

```bash
# 后端
cd /Users/harris/Desktop/StockQuant_副本
lsof -ti:8000 | xargs kill -9 2>/dev/null
python3 server/app.py

# 前端
cd /Users/harris/Desktop/StockQuant_副本/frontend
npx vite --host
# → http://localhost:5173

# API测试
curl http://localhost:8000/health
curl http://localhost:8000/api/scanner
curl http://localhost:8000/api/research/600519
```
