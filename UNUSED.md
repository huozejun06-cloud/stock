# UNUSED.md — 未使用依赖和代码

## 未使用npm依赖
| 包 | 原因 |
|----|------|
| `lucide-vue-next` | 未导入任何组件(已废弃，应用@lucide/vue) |
| `three` | HeroSection改用video背景,Three.js粒子已移除 |
| `countup.js` | WhyTrustSection用GSAP实现计数,未用countup |

## 冗余文件
| 路径 | 说明 |
|------|------|
| `kline/` | 旧缓存目录(与data/kline/重复) |
| `缓存/` | 旧缓存目录(与data/kline/重复) |
| `data/全A股K线数据_汇总.csv` | 172MB CSV,已从git移除 |

## 未调用函数/组件
| 位置 | 说明 |
|------|------|
| GlassCard.vue | 定义了但未在任何页面使用(页面直接用`.glass-card` class) |
| SignalBadge.vue | 定义了但未在任何页面使用 |

## 建议清理
```bash
npm uninstall lucide-vue-next three countup.js
rm -rf kline/ 缓存/
```
