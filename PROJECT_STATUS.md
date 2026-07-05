# StockQuant_副本 — 完整项目状态文档
> 生成时间: 2026-07-05 | 总提交数: 55 | Python文件数: 79

---

## 1. 项目文件清单

### agents/ (Multi-Agent 辩论系统)
| 文件 | 类型 | 职责 |
|------|------|------|
| pipeline.py | 编排 | 全流程: 扫描→规则Agent→LLM辩论→委员会 |
| technical.py | 规则引擎 | 趋势分析: MA/MACD/ADX/BIAS/BOLL/RSI |
| chip.py | 规则引擎 | 筹码分布: 集中度/获利盘/支撑/压力 |
| pattern.py | 规则引擎 | K线形态: 晨星/黄昏/红三兵/三乌鸦/吞没/W底 |
| risk.py | 规则引擎 | 风控: 五条红线/背离/换手/盈亏比/止损 |
| trend_follower.py | LLM驱动 | 趋势派: 游资操盘手视角 |
| value_investor.py | LLM驱动 | 价值派: 私募研究员视角 |
| sentiment_trader.py | LLM驱动 | 情绪派: 量化交易员视角 |
| committee.py | LLM驱动 | 委员会: 汇总辩论, 加权投票, 输出最终决策 |

### server/ (FastAPI 后端)
| 文件 | 职责 |
|------|------|
| app.py | FastAPI 入口, /health 端点 |
| config.py | 服务配置, 引用项目 config.py |
| llm/base.py | LLM Adapter 抽象基类 + 限流/重试 |
| llm/deepseek.py | DeepSeek 适配器 |
| llm/openai.py | OpenAI 适配器 |
| llm/__init__.py | 工厂函数 create_llm_adapter() |
| routes/ws.py | WebSocket /ws/scanner 实时推送 |
| routes/scanner.py | GET /api/scanner 全市场扫描 |
| routes/research.py | GET /api/research/{code} 个股穿透 |

### 工具库/ (基础功能)
| 文件 | 关键函数 |
|------|---------|
| 数据工具.py | 计算全部技术指标(), 获取资金流向(), 获取龙虎榜数据(), 获取市场情绪数据(), 动态板块扫描(), 获取日K线数据() |
| 筹码分布.py | 计算筹码分布() |
| 形态识别.py | detect_w_bottom() |
| 形态识别_增强.py | 识别早晨之星/黄昏之星/红三兵/三只乌鸦/看涨吞没 |
| 交易决策引擎.py | level2_方向判断(), 判断市场状态(), BIAS过滤器(), 背离检测(), 风控红线检查(), 计算盈亏比(), 建议目标价与止损() |
| 情绪周期.py | 判断情绪周期(), 市场温度(), 仓位建议() |
| 新闻搜索.py | 搜索新闻() |
| 新闻情绪分析.py | 搜索个股新闻(), 分析新闻情绪() |
| 公告检查.py | 检查巨潮公告() |
| 热点归因.py | 获取股票题材() |
| 全球市场.py | 获取全球市场快照() |
| 指标注册表.py | 22个指标注册 + DecisionCache |
| 数据源管理器.py | DataSourceManager: 三级降级(东财→同花顺→腾讯) |
| 本地缓存.py | SQLite缓存 |
| __init__.py | (空) |

---

## 2. 各 Phase 完成状态

### Phase A — 代码安全与基础修复 ✅
| Task | 内容 | 提交 |
|------|------|------|
| A-1 | Git Checkpoint + .gitignore | 3acce92, 5cc2745 |
| A-2 | 硬编码路径→config.py (17个文件) | 29906f8, 65366fe |
| A-3 | API Key → .env | 1eb2558 |
| A-4 | 统一缓存目录 cache/+缓存/ → data/ | 3942ddd, 5566020, 42dfbf5 |
| A-5 | 精简冗余指标 (30+→20个) | 3406aa1, 42dfbf5 |
| A-6 | 资金流向仅盘中启用 | 7d62f35 |
| A-7 | Mini回测验证评分权重 | 5712b9a |

### Phase B — 架构升级: API网关+LLM Adapter ✅
| Task | 内容 | 提交 |
|------|------|------|
| B-1 | FastAPI骨架 + /health | f2797e0 |
| B-2 | LLM Adapter 抽象基类 | 2c4bb1a |
| B-3 | DeepSeek 适配器 | 9bff7b0 |
| B-4 | OpenAI 适配器 | f6b2d1f |
| B-5 | 配置驱动切换 create_llm_adapter() | 4827a2f |
| B-6 | 限流+重试+降级 | 047b46f |
| B-7 | WebSocket /ws/scanner | 61124e0 |
| B-8 | GET /api/scanner | e44715f |
| B-9 | GET /api/research/{code} | 88f0b1c |

### Phase C — Multi-Agent 辩论系统 ✅
| Task | 内容 | 提交 |
|------|------|------|
| C-1 | Indicator Registry + 决策缓存 | fe2e970 |
| C-2 | Technical Agent (规则引擎1) | 2dc57bd |
| C-3 | Chip Agent (规则引擎2) | 6470665 |
| C-4 | Pattern Agent (规则引擎3) | 9494178 |
| C-5 | Risk Agent (规则引擎4) | c005194 |
| C-6 | 趋势派 Agent (LLM) | 95bb61e |
| C-7 | 价值派 Agent (LLM) | c9316af |
| C-8 | 情绪派 Agent (LLM) | 332d8cc |
| C-9 | 委员会裁决 Agent (LLM) | ac4e053 |
| C-10 | 逻辑一致性验证 | b841bc6 |

### Pipeline — 端到端选股流水线 ✅
| Task | 内容 | 提交 |
|------|------|------|
| Init | pipeline.py 创建 | cd4af69 |
| P0-1 | 过滤科创板/创业板/北交所 | 100bde5 |
| P0-2 | 接入实时市场情绪数据 | a253004 |
| P0-3 | 接入资金流向数据 | 612d316 |
| P0-4 | 接入动态板块扫描 | 88bd9a0 |
| P0-5 | 连涨天数+3日涨幅+MA5斜率 | d54fd3d |
| P1-6 | 接入龙虎榜数据 | 515f80f |
| P2-7 | 接入新闻/题材/公告 | fa701d0 |
| T2+3 | 展示修复+新鲜度标记 | e3bb99b |
| T1 | K线数据自动更新+缓存保护 | cb3c038 |
| Task A | update_kline_cache.py 批量下载 | 9e9e838 |
| Task C | 并行预下载 (ThreadPoolExecutor) | 950de32 |
| Task D | 多维度排序 (涨跌幅×量比) | dcbe012 |
| Task E | 东财检测日志 | db9a3c3 |
| Task F | 资金流传入风险检查 | db9a3c3 |

### Phase F — P0 紧急修复 ✅
| Task | 内容 | 提交 |
|------|------|------|
| F-1 | WebSocket 修复（mock→腾讯实时） | cd50810 |
| F-2 | KLINE_PATH 配置化（3处硬编码→config） | 4a4e662 |
| F-3 | 裸 except 修复（51处→except Exception+print） | ae7d0f1 |

### Phase G — P1 架构优化 ✅
| Task | 内容 | 提交 |
|------|------|------|
| G-1 | 止损公式优化 + 支撑位2 KeyError修复 | 90abf9e + 4227691 |
| G-2 | committee.py import移到模块顶部 | ed2ee90 |
| G-3 | 文件结构清理（缓存/界面/旧文件+CSV移入data/） | 67376af |

### Phase H — P2 策略优化 ✅
| Task | 内容 | 提交 |
|------|------|------|
| H-1 | 评分权重加入资金流向(15%)+板块强度(10%) | 9ff3252 |
| H-2 | K线数据源改为新浪API（多源回退） | e02edcc + 07e44ce |
| H-3 | 全部止损显示 | 已自动完成 |
| H-4 | 放量突破策略（量比>2+涨幅>5%→+15%） | 6aed52c |
| H-5 | LLM调用优化 53→40次 | a2e94a5 |
| H-6 | 报告TOP10 + 板块过滤验证 | b672958 |

### Phase D — 前端脚手架 ✅ 已完成 (D-1)
| Task | 内容 | 状态 |
|------|------|------|
| D-1 | Vue3+Vite+Tailwind 脚手架 + 设计系统 + 4基础组件 | ✅ e50fbe0 |
| D-2 | Hero 首屏（Three.js粒子 + GSAP Pin锁屏 + 流式文案） | ✅ 进行中 |
| D-3 ~ D-11 | 后续页面 | ❌ 待开发

### Phase F — P0 紧急修复 ✅
| Task | 内容 | 提交 |
|------|------|------|
| F-1 | WebSocket 修复（mock→腾讯实时） | cd50810 |
| F-2 | KLINE_PATH 配置化（3处硬编码→config） | 4a4e662 |
| F-3 | 裸 except 修复（51处→except Exception+print） | ae7d0f1 |

### Phase G — P1 架构优化 ✅
| Task | 内容 | 提交 |
|------|------|------|
| G-1 | 止损公式优化 + 支撑位2 KeyError修复 | 90abf9e + 4227691 |
| G-2 | committee.py import移到模块顶部 | ed2ee90 |
| G-3 | 文件结构清理（缓存/界面/旧文件+CSV移入data/） | 67376af |

### Phase H — P2 策略优化 ✅
| Task | 内容 | 提交 |
|------|------|------|
| H-1 | 评分权重加入资金流向(15%)+板块强度(10%) | 9ff3252 |
| H-2 | K线数据源改为新浪API（多源回退） | e02edcc + 07e44ce |
| H-3 | 全部止损显示 | 已自动完成 |
| H-4 | 放量突破策略（量比>2+涨幅>5%→+15%） | 6aed52c |
| H-5 | LLM调用优化 53→40次 | a2e94a5 |
| H-6 | 报告TOP10 + 板块过滤验证 | b672958 |

### Phase I — P3 增强功能 ❌ 未开始
Scanner/Research/Dashboard/Landing 全未开发。

---

## 3. Pipeline 完整流程

```
实时全市场扫描(腾讯/同花顺, 三级降级, ~5s)
  → 条件1: 涨跌幅 2%~7% (1335→800只)
  → 条件2: 排除 ST / 688(科创板) / 300(创业板) / 8(北交所)
  → 多维度排序: 涨跌幅 × 量比 (量价配合优先)
  → 并行预下载 K 线缓存 (ThreadPoolExecutor 10线程, 前200只)
  → 条件3: MA5 > MA10 (短期均线多头)
  → 条件4: 收盘价 > MA5 (股价站上均线)
  → 条件5: 量比 > 0.8 (成交量活跃)
  → 条件6: 3日累计涨幅 > 0 (持续上涨)
  → 条件7: MA5斜率 > 0 (均线仍在上升)
  → 规则 Agent 评分 (0 LLM):
      Technical: 方向强度/市场状态/均线排列/MACD信号
      Chip: 筹码集中度/获利盘比例/主力行为
      Pattern: 6种K线形态
      Risk: 五条红线 + 止损/目标/仓位
  → 综合性评分 = 方向强度×50% + 筹码集中度×30% + 形态×20%
  → TOP 15 → LLM角色辩论 (45次):
       趋势派(游资操盘手): 趋势+资金流+龙虎榜+新闻+题材+公告
       价值派(私募研究员): 筹码+基本面+技术参考
       情绪派(量化交易员): 形态+情绪周期+板块强度
  → 角色辩论评分排序 → TOP 8 → 委员会裁决 (8次):
       加权投票 + 分歧分析
       输出: 最终信号(BUY/WATCH/SELL) + 评分 + 共识 + 止损/目标/仓位
  → 总耗时: ~80s (缓存命中) ~120s (首次)
```

---

## 4. 数据源与新鲜度

| 数据维度 | 来源 | 新鲜度 | 状态 |
|---------|------|--------|------|
| 实时价格/涨跌幅 | 腾讯/同花顺 | 实时 | ✅ |
| 技术指标(MA/RSI/MACD) | gzip数据集 | 2026-06-16 (18天) | ⚠️ 东财挂了 |
| 资金流向(主力净流入) | akshare | 实时(盘中) | ✅ Task3已接入 |
| 板块扫描(90行业) | 同花顺24h | 实时 | ✅ Task4已接入 |
| 情绪(涨停/跌停) | 腾讯备用(64样本) | 实时但残缺 | ⚠️ 东财挂了 |
| 龙虎榜 | akshare | 每日更新 | ✅ Task6已接入 |
| 新闻 | 同花顺/新浪 | 实时 | ✅ Task7已接入 |
| 公告 | 巨潮 | 每日更新 | ✅ Task7已接入 |
| 热点题材 | akshare | 实时 | ✅ Task7已接入 |

---

## 5. 已知问题 (代码审查发现)

### 🔴 Bug (0个)
全部已修复。

### 🟡 警告 (1个)
1. **情绪数据盘后残缺** — 东财不可用，腾讯备用仅64样本，改用 DataSourceManager 全量并发扫描回退

---

## 6. 剩余待做任务

### Phase D — 前端重写 (最大工程)
- D-1: Vue3脚手架
- D-2~D-5: Landing Page (Hero/功能演示/方法论网格/CTA)
- D-6: Overview看板
- D-7: Scanner页面
- D-8: Research页面
- D-9~D-11: Portfolio/Knowledge/路由

### 5个遗留优化
- Task G: 缓存文件清理 (data/kline/ 已膨胀到1353个文件)
- Task H: LLM调用缩减 (53→41次)
- 裸 except 修复 (9个agent文件)
- 仓位0%修复 (risk.py止损公式)
- KLINE_PATH 配置化 (pipeline.py硬编码)

### 依赖关系
```
Phase A ✅ → Phase B ✅ → Phase C ✅ → Pipeline ✅
    ↓
Phase D (前端) ──→ 依赖 Phase B 的 API 端点
    ↓
执行层/持仓管理 ──→ 依赖前端页面完成后
    ↓
回测中心 ──→ 最后做
```

---

## 7. 关键架构决策

1. **三级降级**: 东财→同花顺→腾讯。东财挂了大半个月, 自动降级工作正常
2. **6+4 Agent**: 6个规则引擎(0LLM) + 3个角色LLM + 1个委员会LLM = 53次调用/次选股
3. **缓存策略**: data/kline/ 本地CSV缓存, 5天内不重新下载, 过期自动从同花顺更新
4. **分级计算**: Scanner阶段只跑规则引擎(0LLM), 点击穿透才跑LLM
5. **K线数据源**: 主用2.5M行gzip全量数据集(到6月16日), 备用同花顺API
6. **选股频率**: 每次运行都是实时扫描 + 本地缓存K线技术分析

---

## 8. 回退指南

```
# 全部回退到 Phase A 前
git reset --hard 3acce92

# 回退到某个 Phase 结束
git reset --hard 5712b9a  # Phase A end
git reset --hard 88f0b1c  # Phase B end
git reset --hard b841bc6  # Phase C end
git reset --hard db9a3c3  # Pipeline 结束
git reset --hard 67376af  # Phase G 结束
git reset --hard 41a5ff0  # 最新（所有修复 + F/G/H）
```


## 9. 运行指南

### 运行选股
```bash
cd ~/Desktop/StockQuant_副本
python3 -c "from agents.pipeline import run; print(run())"
```

### 运行 API 服务器
```bash
python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

### 测试各端点
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/scanner
curl http://127.0.0.1:8000/api/research/600519
# WebSocket (需 websocat)
python3 -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://127.0.0.1:8000/ws/scanner'))"
```

### 回测验证
```bash
python3 verify_weights.py 600519   # 单只回测
python3 verify_agents.py 300750    # 新旧引擎一致性对比
python3 update_kline_cache.py      # 批量下载最新K线数据
```

---

## 10. 环境配置

### Python 版本
- 系统: Python 3.11.6 (系统)
- Bundled: Python 3.12.13 (有 python-docx)
- 本系统使用 **系统 Python** (有 pandas/numpy/akshare)

### 关键依赖
```txt
pandas, numpy, requests, akshare>=1.14.0
fastapi>=0.104.0, uvicorn>=0.24.0, websockets>=12.0
httpx>=0.25.0, pydantic>=2.0, scipy
```

### .env 文件 (必须)
```txt
DEEPSEEK_API_KEY=sk-c293cc72cb6f4e728d82ff047c2f05df
LLM_PROVIDER=deepseek        # 可选: openai
API_HOST=127.0.0.1           # 可选, 默认127.0.0.1
API_PORT=8000                # 可选, 默认8000
```

### 数据文件
```txt
全A股K线数据_汇总.csv.gz → /Users/harris/Desktop/新股票量化/
  (2,550,287 行, 5078 只股票, 1993-06-29 → 2026-06-16, 49 MB gzip)
缓存目录 → data/kline/ (1353 个CSV文件)
数据库目录 → data/db/ (3 个DB文件)
```

---

## 11. 文件依赖图

```
pipeline.py (入口)
  ├── agents/technical.py  → 工具库/数据工具.py (计算全部技术指标)
  ├── agents/chip.py       → 工具库/筹码分布.py (计算筹码分布)
  │                       → 工具库/交易决策引擎.py (判断主力行为)
  ├── agents/pattern.py    → 工具库/形态识别_增强.py (6种K线形态)
  │                       → 工具库/形态识别.py (W底检测)
  ├── agents/risk.py       → 工具库/交易决策引擎.py (BIAS/背离/红线/盈亏比)
  ├── agents/trend_follower.py → server/llm/__init__.py (create_llm_adapter)
  ├── agents/value_investor.py  → server/llm/__init__.py (create_llm_adapter)
  ├── agents/sentiment_trader.py → server/llm/__init__.py (create_llm_adapter)
  └── agents/committee.py  → server/llm/__init__.py (create_llm_adapter)

server/app.py (API服务器)
  ├── server/routes/ws.py       → config.CACHE_DIR
  ├── server/routes/scanner.py  → server/routes/ws.py (_scan_market_top50)
  └── server/routes/research.py → 工具库/数据工具.py / 交易决策引擎.py
```

---

## 12. 当前数据状态 (2026-07-04 21:13)

### 缓存目录 (data/kline/)
```
CSV文件数: 1353 个
最新数据日期: 2026-01-07 (抽样100个)
数据源: gzip全量数据集 + 同花顺自动下载
```

### 数据库目录 (data/db/)
```
DB文件数: 3 个
```

### K线缓存（2026-07-04）
```
缓存目录: data/kline/ (1524 文件)
数据源: 新浪财经K线API (money.finance.sina.com.cn)
最新数据: 2026-07-03 (已验证可用)
覆盖范围: 1221只热门股已更新到最新，其余使用全量数据集兜底
```

### K线缓存（2026-07-05）
```
缓存目录: data/kline/ (1524 文件)
数据源: 新浪财经K线API (money.finance.sina.com.cn)
最新数据: 2026-07-03 (已验证可用)
覆盖范围: 1221只热门股已更新到最新，其余使用全量数据集兜底
```

### K线全量数据集
```
位置: /Users/harris/Desktop/新股票量化/全A股K线数据_汇总.csv.gz
状态: 到 2026-06-16 (18天前)
覆盖: 5078只, 2,550,287行
```

---

## 13. 关键文件保护列表

以下文件改动可能导致系统崩溃, 修改前必须创建checkpoint:

| 风险等级 | 文件 | 原因 |
|---------|------|------|
| 🔴 极高 | agents/pipeline.py | 核心编排流程, 含7步过滤+排序+预下载+规则Agent+LLM |
| 🔴 极高 | agents/trend_follower.py | LLM Prompt错误会导致所有趋势分析失败 |
| 🔴 极高 | agents/value_investor.py | LLM Prompt错误会导致所有价值分析失败 |
| 🔴 极高 | agents/sentiment_trader.py | LLM Prompt错误会导致所有情绪分析失败 |
| 🔴 极高 | agents/committee.py | LLM Prompt错误会导致委员会裁决失败 |
| 🟡 高 | agents/risk.py | 止损公式错误会导致仓位和风控全部失效 |
| 🟡 高 | 工具库/数据工具.py | 1729行, 所有数据获取的根基 |
| 🟢 中 | config.py | 路径配置错误会导致整个系统找不到文件 |
| 🟢 中 | server/目录 | API端点, 修改需同时更新前端 |

---

## 14. LLM 成本估算 (单次选股)

```
规则Agent: 0次LLM → $0
角色辩论: 15只 × 3角色 = 45次 → ~$0.23 (DeepSeek)
委员会: 8只 × 1次 = 8次 → ~$0.04
总计: 53次 → ~$0.27/次 (DeepSeek)
如果用GPT-4o: ~$2.50/次
```

---

## 15. 已知设计缺陷 (非代码Bug, 架构层面)

1. **仓位0%不是Bug, 是过分保守的设计** — 止损公式用布林中轨-ATR/2, 当股价贴近中轨时盈亏比<1。修复需调整 risk.py 的止损计算
2. **情绪数据非交易时段为0** — 腾讯备用源只有64只样本, 不足以计算真实涨跌停。不影响功能
3. **K线数据到6月16日** — 东财挂了18天, data/kline/缓存有部分同花顺下载的最新数据。不影响选股逻辑, 但技术指标不是最新的
4. **LLM agent 缓存策略** — 同一股票30秒内不重复计算(IndicatorRegistry DecisionCache), 但WebSocket推送时不会复用缓存(需要手动调缓存)
5. **W底检测永不触发** — 需要5分钟线, pipeline只传日K线。这是一个已知未完成的功能


### D-2: HeroSection 全量重写 ✅ 完成
- Commit: 21e0226
- HeroSection.vue (140行): video六层 + 5句GSAP(blur/scale/y) + 双CTA
- NavBar.vue (80行): 胶囊形(1160px/999px/blur26) + 8项菜单
- App.vue (43行): Lenis初始化(lerp0.08/dur1.2)
- Landing.vue (144行): 7屏完整滚动官网
- router: 新增 Backtest/Methodology/About 路由
- 新建: Backtest.vue/Methodology.vue/About.vue 占位页
- package.json: 新增 @studio-freight/lenis

### D-2.5: Hero 文案设计 + NavBar 重构 + 卡片展开交互 ✅ 完成
- Commit: 2818506
- HeroSection: 5句文案分散布局(iOS毛玻璃pill,不同位置/大小)
- NavBar: 6按钮均匀排布(space-evenly) + 独立毛玻璃pill按钮
- Landing: methodology + dataSources 卡片点击展开详情

### D-3: WhyTrust + WhyInsight 独立组件 + 全屏 ScrollTrigger ✅ 完成
- Commit: 02bfa31
- 新建: WhyTrustSection.vue (87行) — 4数字 CountUp + GSAP stagger
- 新建: WhyInsightSection.vue (60行) — 左文右视频 + GSAP fromTo
- 新建: countup.js 依赖
- Landing.vue: 替换内联section为独立组件 + 全屏 ScrollTrigger 入场动画
  (协同研判/研究方法/数据来源/Footer全部接入GSAP动画) ⏳ Next ⏳ Next
- 六层结构 (video + gradient + noise + bloom + CTA + 文案)
- 5句 GSAP 文案轮播 + NavBar胶囊化 + Lenis初始化
### E-1: K线缓存数据更新 ✅ 完成
- Commit: 34a19c5
- 从 新股票量化/ 项目拷贝 5365 个 CSV 缓存到 data/kline/
- 数据范围: 2024-06 ~ 2026-07-03, 153MB
- /api/research/600519 返回真实指标: MA/RSI/MACD/ATR/ADX/决策信号
- .gitignore 已加 data/kline/ + __pycache__/

### E-2: 新建 /api/overview 聚合端点 ✅ 完成
- Commit: 0db2a00
- 新建: server/routes/overview.py (164行)
- 修改: server/app.py (注册 overview_router)
- 6 组数据: A股指数/全球指数/市场情绪/热门板块/实时快讯/AI日志
- 每组独立 mock 兜底

### E-3: Overview 前端换真实数据 ✅ 完成
- Commit: 5924ccb
- 6 个数据变量: plain → ref() 包裹
- 新增: fetchOverview() — API 字段映射 + 失败保 mock
- 模板/CSS/GSAP 完全不动

### E-4: Research 前端接真实指标 ✅ 完成
- Commit: 360d545
- 指标面板: 8 项全部 computed 从 apiData.indicators 读取
- 决策信号: signal/score/reasoning 从 apiData.decision 读取
- 止损位: stopLoss 从 apiData.key_levels 读取
- K线/筹码/Agent投票保留 mock（API 暂不返回这些）
- 全部有 mock 兜底

### E-5: 全链路端到端测试 ⏳ Next
- Landing → Overview → Scanner → Research 全流程验证
- 改 Research.vue: K线/筹码/指标/Agent投票/AI报告全换真实数据
- 改 Overview.vue: 5块mock→fetch(/api/overview)
- 新建 server/routes/overview.py
- 聚A股指数/全球指数/市场情绪/热门板块/实时快讯/AI日志


## Phase E 实时数据 P0 Debug 进展 (2026-07-06)

### P0 已修复
| # | 问题 | 文件 | Commit |
|---|------|------|--------|
| 1 | ws.py DataFrame→list 转换缺失 | ws.py | 5316e9e |
| 2 | ws.py 字段中英文不匹配 | ws.py | d4c0068 |
| 3 | DataSourceManager .empty 无守卫 | 数据源管理器.py | da4b7f9 |
| 4 | scanner data_source 标签错误 | scanner.py | 756bf25 |
| 5 | Backtest optimizations 未声明 | Backtest.vue | 756bf25 |
| 6 | ws.py 过滤 code 缺少中文 fallback | ws.py | bc0c52b |
| 7 | DataSourceManager 最新价未加入 result | 数据源管理器.py | 62da6b1 |

### 当前数据链路状态
- Scanner: Source=live ✅ 代码/名称/涨跌幅/换手率真实
- Scanner: price=0 🟡 最新价修复中(诊断代码覆盖了修复)
- 腾讯 API: 4658只股票扫描成功 ✅
- 板块过滤: 300/301/688/689/8xx 已排除 ✅
- 东方财富 API: ❌ proxy 残留阻断

### 剩余 P1
- Scanner 页面滚动条
- Research K 线 mock
- 东方财富 proxy 清理
