# PRODUCTION_REPORT.md — 生产环境联调报告

> ⚡ = 沙箱内实际运行验证 | 🔶 = 需用户在本地Mac运行验证
> 沙箱限制: 无法绑定端口(EPERM)，不能启动FastAPI/Vite/浏览器

---

## ⚡ 已验证：模块导入与函数调用

| 模块 | 函数 | 结果 | 证据 |
|------|------|------|------|
| `server.routes.scanner` | `_cache_stocks(10)` | ✅ 返回10只 | 首只: 600769 ¥21.78 |
| `server.routes.research` | `_analyze_stock('600519')` | ✅ 计算完成 | price=1194.45, signal=禁止交易, score=28.8 |
| `server.routes.overview` | `_mock_indices()` | ✅ 4指数 | 上证/深证/创业板/科创50 |
| `server.routes.overview` | `_mock_sentiment()` | ✅ 情绪数据 | market_temp=65 |
| `config` | CACHE_DIR | ✅ | /Users/harris/Desktop/StockQuant_副本/data/kline |
| `config` | DEEPSEEK_API_KEY | ✅ 已配置 | API_KEY_set=True |
| `agents.pipeline` | `run` | ✅ 可导入 | 未实际调用(避免LLM调用) |
| `工具库.数据源管理器` | `get_manager` | ✅ 可导入 | 网络调用需用户本地验证 |

## ⚡ 已验证：K线缓存数据

| 项目 | 值 |
|------|-----|
| 文件数 | 5195 |
| 数据日期 | 2026-07-03 |
| 600519 最新价 | 1194.45 |
| 002594 涨跌幅 | +5.86% |

---

## 🔶 需用户在本地Mac运行验证（精确命令）

### 1. 启动后端
```bash
cd /Users/harris/Desktop/StockQuant_副本
lsof -ti:8000 | xargs kill -9 2>/dev/null
python3 server/app.py &
sleep 3
```

### 2. API测试
```bash
echo "=== /health ===" && curl -s http://localhost:8000/health
echo "=== /api/scanner (前3只) ===" && curl -s http://localhost:8000/api/scanner | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'{s[\"code\"]} ¥{s[\"price\"]}') for s in d['stocks'][:3]]"
echo "=== /api/research/600519 ===" && curl -s http://localhost:8000/api/research/600519 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'signal={d[\"decision\"][\"signal_name\"]}, score={d[\"decision\"][\"total_score\"]}')"
echo "=== /api/overview ===" && curl -s http://localhost:8000/api/overview | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'indices:{len(d[\"indices\"])}, global:{len(d[\"global\"])}, sentiment:{d[\"sentiment\"][\"market_temp\"]}')"
```

### 3. 前端
```bash
cd /Users/harris/Desktop/StockQuant_副本/frontend
npx vite --host &
sleep 3
```
打开 http://localhost:5173 → F12 → Network标签 → 截图 → 发给我

---

## 结论

| 状态 | 说明 |
|------|------|
| ✅ 后端代码 | 全模块可导入，关键函数运行正确 |
| ✅ K线数据 | 5195只完整，可读可计算 |
| ✅ API逻辑 | Scanner/Research/Overview代码路径已验证 |
| 🔶 网络连通 | 需用户在本地验证DataSourceManager DNS |
| 🔶 前端渲染 | 需用户在浏览器验证Network/Console |

---

## 🔶 用户本地实际运行结果 (2026-07-06 实测)

### 后端启动 ✅
```
Uvicorn running on http://0.0.0.0:8000
```

### /health ✅
```json
{"status":"ok","version":"0.1.0","llm_configured":true,"llm_provider":"deepseek"}
```
HTTP 200, DeepSeek API Key 已配置。

### /api/scanner ⚠️ (发现新bug)
```
东财: ❌ HTTPS proxy error (127.0.0.1:10809)
同花顺: ✅ 可用
腾讯: ✅ 可用 → 扫描 4658 只股票

⚠️ 全市场扫描失败: 'str' object has no attribute 'get'
DataSourceManager 返回 0 只股票
降级到 CSV 缓存 → 返回 50 只

实际返回:
  603137 ¥17.22 chg=10.03%  ← CSV缓存真实价
  603466 ¥11.63 chg=10.03%
  603915 ¥16.03 chg=10.02%
```

**发现**: 
- `data_source: "live"` 标签有误导性——实际用的是CSV缓存
- DataSourceManager 有 bug: `'str' object has no attribute 'get'` 导致腾讯返回的4658只数据全丢弃
- git http.proxy 残留(127.0.0.1:10809) 干扰了东财API

### /api/research/600519 ✅
```json
{"signal":"禁止交易","score":28.8}
```
HTTP 200, 来自CSV真实指标。

### /api/overview ⚠️
```
proxy timeout at 127.0.0.1:10809 (read timeout=5)
返回: indices:4, global:4, sentiment:20 (mock值)
```
proxy残留干扰，情绪值为mock(20度='中性')。

### 前端 Vue Warning ❌
```
[Vue warn]: Property "optimizations" was accessed during render 
but is not defined on instance. (at <Backtest>)
```
Backtest.vue 缺少 `optimizations` 变量声明。

---

## 🔴 实际运行发现的新问题

| # | 问题 | 严重度 | 证据 |
|---|------|--------|------|
| 1 | DataSourceManager `'str' object has no attribute 'get'` | 🔴 P0 | 腾讯返回4658只后被丢弃 |
| 2 | `data_source: "live"` 标签不准确 | 🟡 P1 | 实际是CSV缓存 |
| 3 | git http.proxy残留 127.0.0.1:10809 | 🟡 P1 | 干扰东财API+overview |
| 4 | Backtest.vue `optimizations` 变量未声明 | 🟡 P2 | Vue template错误 |
