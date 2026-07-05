# MOCK_LIST.md — 全项目Mock扫描

## 纯Mock (永远不接入真实数据)
| 文件 | 行 | 内容 |
|------|-----|------|
| Research.vue | 296-300 | K线OHLC `Math.random()` |
| Scanner.vue | 176-187 | fallbackStocks数组生成 |
| Scanner.vue | 254-257 | K线预览 `Math.random()` |
| Backtest.vue | 114 | 收益曲线 `Math.random()` |
| Backtest.vue | 127 | 月度收益 `Math.random()` |

## 兜底Mock (API失败时触发)
| 文件 | 行 | 触发条件 |
|------|-----|---------|
| scanner.py | 17-37 | DataSourceManager返回空 |
| scanner.py | `_cache_stocks()` | API失败→读CSV真实价(已替代mock) |
| overview.py | 14-65 | 各子模块API失败 |
| research.py | 96-103 | CSV缓存不存在 |
| Scanner.vue | 164-192 | fetch()网络错误 |

## 字段级Mock (部分字段随机填充)
| 文件 | 字段 |
|------|------|
| Scanner.vue fetchStocks | `sector`, `trendScore`, `chipScore` |
| Research.vue | `fundFlow`, `bigOrder`, `profitRatio`, `concentration` |

## 已消除的Mock
| 位置 | 原来是 | 现在 |
|------|--------|------|
| Scanner price | `(10+Math.random()*200).toFixed(2)` | CSV真实收盘价 |
| Research indicators | 硬编码`1,188.50` | `apiData.value.indicators` |
