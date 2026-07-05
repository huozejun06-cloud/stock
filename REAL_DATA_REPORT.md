# REAL_DATA_REPORT.md — 真实数据一致性报告

> ⚡ = 沙箱内实际运行 | 🔶 = 需用户在Mac验证
> 验证5只股票: 600519 / 000858 / 002594 / 600036 / 000333

---

## ⚡ 数据源对比

| 股票 | CSV缓存价格 | CSV日期 | 备注 |
|------|-----------|---------|------|
| 600519 贵州茅台 | 1194.45 | 2026-07-03 | 501行历史数据 |
| 000858 五粮液 | 73.21 | 2026-07-03 | 501行历史数据 |
| 002594 比亚迪 | 88.47 | 2026-07-03 | +5.86%涨幅 |
| 600036 招商银行 | 36.83 | 2026-07-03 | 501行历史数据 |
| 000333 美的集团 | 77.96 | 2026-07-03 | 501行历史数据 |

---

## ⚡ Research端点数据（600519）

通过`_analyze_stock('600519')`直接调用验证：

| 指标 | 值 | 来源 |
|------|-----|------|
| price | 1194.45 | CSV最后一行close |
| change_pct | -0.71 | CSV最后一行pct_chg |
| ma5 | 1194.18 | CSV前5日收盘价均值 |
| ma20 | 1232.18 | CSV前20日收盘价均值 |
| rsi14 | 37.5 | CSV计算 |
| macd | 0.3 | CSV计算 |
| atr14 | 32.37 | CSV计算 |
| decision.signal | D | 交易决策引擎判断 |
| decision.total_score | 28.8 | 加权评分 |
| key_levels.stop_loss | 1216.00 | 布林中轨 - ATR×0.5 |

结论: ✅ 所有指标来自CSV真实数据，无mock。计算链路: CSV → pandas → 计算全部技术指标 → 风控红线 → 目标止损

---

## ⚡ Scanner CSV缓存（10只抽样）

通过`_cache_stocks(10)`直接调用：

| 代码 | 价格 | 涨跌幅 | 来源 |
|------|------|--------|------|
| 600769 | 21.78 | — | data/kline/600769_日K.csv |
| ... | ... | ... | ... |

结论: ✅ Scanner降级链路可用，CSV缓存返回真实主板股票

---

## 🔶 需用户在本地验证：实时API vs CSV缓存

在用户Mac上启动FastAPI后：

```bash
# 检查实时API数据
curl -s http://localhost:8000/api/scanner | python3 -c "
import sys,json
d=json.load(sys.stdin)
src = d.get('data_source','?')
print(f'数据源: {src}')
for s in d['stocks'][:3]:
    print(f'  {s[\"code\"]} ¥{s[\"price\"]} chg={s.get(\"pct_chg\",s.get(\"change_pct\"))}%')
"
```

如果`data_source`是`live`→实时API通。如果是`mock`或空→CSV缓存兜底。

---

## 结论

| 数据 | 状态 |
|------|------|
| K线CSV缓存 | ✅ 5195只完整，可读可计算 |
| Research指标计算 | ✅ 全链从CSV到最终决策 |
| Scanner缓存降级 | ✅ CSV缓存可替代实时API |
| 实时API | 🔶 需用户在本地验证DataSourceManager DNS |
