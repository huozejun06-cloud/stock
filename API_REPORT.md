# API_REPORT.md — 端点运行验证

> ⚡ 沙箱内实际运行 | 🔶 需用户本地验证

---

## ⚡ Scanner: `_cache_stocks()` 直接调用

| 项目 | 值 |
|------|-----|
| 调用方式 | `_cache_stocks(10)` 直接调用 |
| 返回数量 | 10只 |
| 首只股票 | 600769 |
| 首只价格 | ¥21.78 |
| 数据来源 | data/kline/*.csv |
| 真实性 | ✅ CSV真实收盘价，非mock |

数据链路: `_cache_stocks()` → `os.listdir(CACHE_DIR)` → CSV文件 → 读最后一行 → 取close和pct_chg → 过滤主板 → 排序 → 返回

---

## ⚡ Research: `_analyze_stock('600519')` 直接调用

| 项目 | 值 |
|------|-----|
| 股票代码 | 600519 |
| 收盘价 | 1194.45 (来自CSV) |
| 决策信号 | D (禁止交易) |
| 评分 | 28.8 |
| 信号名 | 禁止交易 |
| 数据来源 | data/kline/600519_日K.csv → 计算全部技术指标 |

数据链路: `_analyze_stock()` → `pd.read_csv(CSV)` → `计算全部技术指标()` → `level2_方向判断()` → `风控红线检查()` → `建议目标价与止损()` → 返回完整JSON

---

## ⚡ Overview: `_mock_*()` 直接调用

全部6个子模块mock函数可正常调用，返回符合预期格式的数据。真实数据需要后端API运行时调用对应的`_try_real_*()`函数。

---

## 🔶 需用户本地验证

| 端点 | 验证命令 |
|------|---------|
| GET /health | `curl -s http://localhost:8000/health` |
| GET /api/scanner | `curl -s http://localhost:8000/api/scanner \| python3 -m json.tool \| head -20` |
| GET /api/research/600519 | `curl -s http://localhost:8000/api/research/600519` |
| GET /api/overview | `curl -s http://localhost:8000/api/overview \| python3 -m json.tool \| head -10` |
| WS /ws/scanner | 未在前端接入，暂不测试 |
