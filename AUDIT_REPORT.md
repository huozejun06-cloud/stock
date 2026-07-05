# AUDIT_REPORT.md — Release Candidate 全链路验收
> 审计时间: 2026-07-06 | 审计人: Codex QA Lead
> 环境: macOS, Python 3.11, Node 22, Vue3+Vite

---

## 一、项目规模

| 类型 | 数量 |
|------|------|
| Python 文件 | 75 |
| Vue 文件 | 15 |
| JS 文件 | 5 |
| CSS 文件 | 2 |
| MD 文档 | 8 |
| K线缓存 | 5366 CSV |
| Git commits | 13 (clean repo) |

## 二、API 端点

| 方法 | 路径 | 文件 | 真实数据? |
|------|------|------|----------|
| GET | /health | server/app.py | ✅ |
| GET | /api/scanner | server/routes/scanner.py → ws.py → DataSourceManager → 腾讯/同花顺 | 🟡 API失败→CSV缓存 |
| GET | /api/research/{code} | server/routes/research.py → CSV缓存→计算指标 | ✅ CSV缓存 |
| GET | /api/overview | server/routes/overview.py → 6个子模块 | 🟡 各子模块独立mock兜底 |
| WS | /ws/scanner | server/routes/ws.py | ✅ 前端未接 |

## 三、Mock 清单

### 纯 Mock (不依赖外部数据，永远返回随机值)
| 位置 | 内容 |
|------|------|
| Research.vue K线图 | `Math.random()` 生成OHLC |
| Scanner.vue K线预览 | `Math.random()` 生成OHLC |
| Backtest.vue 收益曲线 | `Math.random()` 生成曲线 |
| Backtest.vue 月度收益 | `Math.random()` 生成柱状图 |

### 兜底 Mock (API失败时降级)
| 位置 | 触发条件 |
|------|---------|
| scanner.py `_mock_stocks(50)` | DataSourceManager返回空→降级CSV缓存(真实价) |
| overview.py 6个 `_mock_*()` | 各子模块API调用失败→各自mock |
| research.py 异常处理 | CSV缓存不存在→返回极简mock |
| Scanner.vue `fallbackStocks` | API完全不可达→50条随机股 |

### 已消除的 Mock
| 原位置 | 现状 |
|--------|------|
| Scanner mock 价格 | → CSV缓存真实收盘价 |
| Overview 6组数据 | → /api/overview (部分真实) |
| Research 8项指标 | → /api/research CSV计算 |
| Research Agent投票 | 仍为mock (API不返回单个Agent数据) |

## 四、数据链路追踪

### Scanner 链路
```
DataSourceManager(腾讯API) → [失败] → CSV缓存(_cache_stocks)
  → 读 ~150 只主板CSV → 按pct_chg排序 → 返回50只
  → FastAPI → JSON → Vue fetchStocks() → stocks.value → filteredStocks → v-for渲染
```
**证据**: last commit `a5986fb` 中 `_cache_stocks()` 从 `data/kline/*.csv` 读数

### Research 链路
```
GET /api/research/600519 → _analyze_stock("600519")
  → 读 data/kline/600519_日K.csv → 计算MA/RSI/MACD/ATR/ADX
  → JSON → Vue fetchResearch() → apiData.value → computed → 模板
```
**证据**: `/api/research/600519` 返回真实指标 (verified at 23:00)

### Overview 链路
```
GET /api/overview → indices/global/sentiment/sectors/news/ai_logs
  → 每个子模块: try真实函数 → except → mock兜底
  → JSON → Vue fetchOverview() → refs → computed → 模板
```
**证据**: sentiment 返回 `0:0` (非交易时段真实数据为空)

## 五、页面验收状态

| 页面 | 加载 | 真实数据 | Mock | JS Error | 备注 |
|------|------|---------|------|----------|------|
| Landing | ✅ | N/A | N/A | 无 | 视频未提供 |
| Overview | ✅ | 🟡 部分 | 情绪/板块/快讯mock | apiError警告 | 后端API部分函数失败 |
| Scanner | ✅ | 🟡 CSV缓存 | K线mock | 无 | 滚动条bug |
| Research | ✅ | 🟡 指标真实 | K线/Agent/筹码mock | 无 | 日期修复已生效 |
| Backtest | ✅ | ❌ | 全mock | 无 | 收益曲线/月度分布 |
| Methodology | ✅ | N/A | N/A | 无 | 静态页 |
| About | ✅ | N/A | N/A | 无 | 静态页 |

## 六、关键问题

### P0 (阻塞)
1. **DataSourceManager API 失败** — 腾讯/东方财富 DNS 解析失败，Scanner永远走CSV缓存
   - 影响: 交易日内也无法获取实时行情
   - 根因: Python进程内 `qt.gtimg.cn` DNS解析失败 (Errno 8)
   - 文件: `工具库/数据源管理器.py`

### P1 (严重)
2. **Scanner 滚动条不工作** — flexbox `min-height:0` 不够，需要重新设计布局
3. **Scanner/Research K线图数据不统一** — 各自Math.random()生成，同只股票显示不同
4. **Overview 情绪/快讯/板块为mock** — 后端函数调用失败，需逐个修复

### P2 (中等)
5. `apiError` Vue警告 — 已声明但模板在声明前使用
6. NavBar Research 硬编码 600519
7. `lucide-vue-next`/`three` 依赖未使用

### P3 (低)
8. 视频文件未提供
9. Backtest全mock (后端无回测API)

## 七、真实性评分

| 维度 | 分数 | 依据 |
|------|------|------|
| Backend | 75 | API框架完整，但DataSourceManager网络失败 |
| Frontend | 80 | 7页15组件完整，GSAP动画正常，布局有小bug |
| Data | 65 | CSV缓存真实(5366只)，但实时API不通 |
| API | 70 | 4个端点正常，但/overview部分mock |
| Architecture | 85 | 分层清晰，Agent/Pipeline/Route分离 |
| UI | 85 | 设计系统完整，毛玻璃/微光/动画到位 |
| Animation | 80 | GSAP+Lenis正常，Scanner列表需修复 |
| Maintainability | 75 | 8份MD规范完整，代码注释偏少 |
| Documentation | 90 | 8份规范文档1261行，覆盖全面 |
| **真实性** | **50** | Scanner走缓存非实时,Overview部分mock,Research K线mock |

## 八、当前完成百分比

**真实完成度: 65%**

- Landing: 95% (缺视频)
- Overview: 60% (3/6组数据为mock)
- Scanner: 55% (CSV缓存可用, 实时API不通, K线mock, 滚动bug)
- Research: 55% (指标真实, K线/筹码/Agent mock)
- Backtest: 10% (全mock)
- Methodology/About: 100%

## 九、根因定位

**为什么前端没有显示最新数据**: DataSourceManager在Python进程内无法解析 `qt.gtimg.cn` DNS → API返回空 → 降级CSV缓存(上周五收盘价)。这是**后端网络环境问题**，不是代码bug。

## 十、下一步修复顺序

1. **P0**: 修复 DataSourceManager DNS失败 → 用新浪API或更换数据源
2. **P1**: 重写Scanner三栏布局(解决滚动)
3. **P1**: 统一K线数据源(Scanner+Research共用CSV)
4. **P2**: 修复Overview各子模块API调用
5. **P2**: 清理Vue警告和未使用依赖

**在所有P0/P1问题解决前，禁止开发新功能。**
