# Motion System — 洞见 INSIGHT

> 全站动画统一规范。GSAP + ScrollTrigger + Lenis 参数唯一来源。

---

## Lenis 平滑滚动

| 参数 | 值 |
|------|-----|
| lerp | 0.08 |
| duration | 1.2 |
| smoothWheel | true |

初始化位置: App.vue onMounted

---

## GSAP ScrollTrigger 统一动画

所有区块进入动画:

| 属性 | 值 |
|------|-----|
| opacity | 0 -> 1 |
| translateY | 60px -> 0 |
| scale | 0.96 -> 1 |
| filter | blur(8px) -> blur(0) |
| duration | 0.9s |
| ease | power3.out |
| stagger | 120ms |

---

## Hero 文案动画

| 属性 | 值 |
|------|-----|
| duration | 1.2s |
| ease | power4.out |
| pin | true |
| scrub | 1.2 |
| end | "+=2500" |

---

## 卡片动画

| 属性 | 值 |
|------|-----|
| duration | 0.8s |
| ease | power2.out |
| stagger | 120ms |

---

## Hover 微交互

| 属性 | 值 |
|------|-----|
| translateY | -6px |
| transition | 300ms ease |
| active scale | 0.98 |

---

## 视频屏幕切换动画

上一屏退出:
| 属性 | 值 |
|------|-----|
| scale | 1 -> 1.05 |
| opacity | 1 -> 0 |
| blur | 0 -> 12px |

下一屏进入:
| 属性 | 值 |
|------|-----|
| opacity | 0 -> 1 |
| scale | 0.95 -> 1 |
| blur | 12px -> 0 |

---

## 禁止项

- 禁止使用 AOS、Animate.css 等第三方动画库
- 禁止在 Scanner 列表行使用 GSAP ScrollTrigger
- 禁止动画 duration 超过 1.5s
