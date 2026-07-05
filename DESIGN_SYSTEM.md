# Design System — 洞见 INSIGHT

> 全站唯一设计 Token 来源。所有颜色、字体、间距、圆角、阴影从本文档取用。
> 对应实现文件：frontend/src/styles/tokens.css

---

## 色彩

### 背景
| Token | 值 | 用途 |
|-------|-----|------|
| --color-bg | #080B13 | 全局背景 |
| --color-nav | rgba(18, 22, 32, 0.45) | 导航栏背景 |

### 强调色
| Token | 值 | 用途 |
|-------|-----|------|
| --color-primary | #ff6b35 | CTA 按钮、强调 |
| --color-highlight | #6c8cff | 数据高亮 |
| --color-purple | #8b5cf6 | 科技微光、粒子 |
| --color-green | #21d07a | 上涨/BUY |
| --color-red | #ff5b6e | 下跌/SELL |

### 文字
| Token | 值 | 用途 |
|-------|-----|------|
| --text-primary | #e2e8f0 | 主文字 |
| --text-secondary | #94a3b8 | 次要文字 |
| --text-dim | #64748b | 禁用/提示 |

---

## 圆角
| Token | 值 | 用途 |
|-------|-----|------|
| --radius-btn | 16px | 按钮 |
| --radius-card | 24px | 卡片 |
| --radius-hero | 32px | Hero 元素 |
| --radius-modal | 28px | 弹窗 |

---

## 毛玻璃
| Token | 值 |
|-------|-----|
| --blur-glass | 26px |

---

## 阴影
| Token | 值 |
|-------|-----|
| --shadow-sm | 0 4px 12px rgba(0,0,0,.25) |
| --shadow-md | 0 10px 30px rgba(0,0,0,.3) |
| --shadow-lg | 0 20px 60px rgba(0,0,0,.35) |
| --shadow-xl | 0 40px 100px rgba(0,0,0,.4) |

---

## 间距
| Token | 值 | 用途 |
|-------|-----|------|
| --space-section | 120px | Section 上下 padding |
| --space-container | 1440px | Container max-width |

---

## 字体
| Token | 值 | 用途 |
|-------|-----|------|
| --font-hero | 'Noto Serif SC', serif | Hero 标题 |
| --font-body | 'HarmonyOS Sans SC', 'PingFang SC', sans-serif | 正文 |
| --font-number | 'Inter', sans-serif | 数字 |
| --font-code | 'JetBrains Mono', monospace | 代码 |

---

## UI 一致性铁律

1. 所有按钮高度：48px
2. 所有标题 margin-bottom：24px
3. 所有 Section padding：120px（上下各）
4. 所有 Container max-width：1440px
5. 所有 Card border-radius：24px
6. 所有 Glass backdrop-filter blur：26px
7. 所有 Hover 位移：translateY(-6px)
8. 所有 Hover 微光扩散半径：<=20px

---

## 禁止项

- 禁止纯黑 #000000、纯白 #ffffff
- 禁止 blur 值不是 12/20/26/40 中的任意一个
- 禁止 radius 值不是 16/24/28/32 中的任意一个
- 禁止内联 style（除 GSAP 动画控制外）
- 禁止 !important
- 禁止硬编码颜色值（必须使用 Token 或 Tailwind class）
