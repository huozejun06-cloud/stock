# Product Spec — 洞见 INSIGHT V3.2

> 产品定位、品牌、页面架构、信息架构。

---

## 品牌

| 属性 | 值 |
|------|-----|
| 中文名 | 洞见 |
| 英文名 | INSIGHT |
| 定位 | AI 量化投资研究平台 |
| 调性 | Apple 官网 x Perplexity x Linear |
| Logo | 中文"洞见" + 底部小字 INSIGHT |

---

## 产品理念

不是预测市场，而是帮助理解市场。

先看风险，再看机会。

---

## 信息架构



---

## 导航结构

8 项胶囊导航 (max-width 1160px, radius 999px):

1. 市场全景
2. 机会扫描
3. 深度研究
4. 协同研判
5. 策略验证
6. 研究方法
7. 关于洞见
8. [开始体验] CTA

---

## 路由设计

| 路径 | 页面 | 说明 |
|------|------|------|
| / | Landing | 首次访问展示完整 Landing |
| /overview | 市场全景 | 系统内首页 |
| /scanner | 机会扫描 | 实时选股 |
| /research/:code | 深度研究 | 个股穿透 |
| /backtest | 策略验证 | 回测中心 |
| /methodology | 研究方法 | 方法论 + 指标实验室 |
| /about | 关于洞见 | 项目介绍 |

---

## 技术栈

Vue3 + Vite + Pinia + Vue Router + GSAP + ECharts + Tailwind CSS + Lenis
FastAPI + Python + DeepSeek + SQLite + WebSocket
