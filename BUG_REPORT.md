# BUG_REPORT.md — 按优先级排列

## 🔴 P0 — 阻塞（刚通过实际运行发现）

| # | 问题 | 位置 | 证据 | 修复方案 |
|---|------|------|------|---------|
| 1 | DataSourceManager `'str' object has no attribute 'get'` | 工具库/数据源管理器.py | 腾讯返回4658只后被丢弃 | 定位`.get`调用,修复str/object类型错误 |
| 1a | `data_source: "live"` 标签错误 | scanner.py | CSV缓存时也显示live | 改`_cache_stocks`路径设置`data_source="cache"` |
| 1b | proxy残留 127.0.0.1:10809 | git config + Python | 东财+overview超时 | `git config --unset http.proxy` |

## 🟡 P1 — 严重

| # | 问题 | 位置 | 修复方案 |
|---|------|------|---------|
| 2 | Scanner滚动条 | Scanner.vue | 三栏布局重写 |
| 3 | Scanner/Research K线不一致 | Scanner.vue+Research.vue | 统一从CSV读取 |
| 4 | Overview情绪=20(mock) | overview.py | 修复`_try_real_sentiment` |

## 🟢 P2 — 中等

| # | 问题 | 位置 |
|---|------|------|
| 5 | Backtest.vue `optimizations` 未声明 | Backtest.vue |
| 6 | NavBar 600519硬编码 | NavBar.vue |

## ⚪ P3 — 低

| # | 问题 |
|---|------|
| 7 | 视频文件未提供 |
| 8 | Backtest全mock |
