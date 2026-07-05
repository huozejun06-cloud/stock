# Coding Rules — 洞见 INSIGHT

> Vue3 + TypeScript 开发规范。所有代码必须遵守。

---

## Vue3 规范

- 使用 Composition API (<script setup>)
- 单个 .vue 文件自包含 (SFC)，禁止超过 3 层嵌套
- Props 使用 defineProps 类型声明
- Emits 使用 defineEmits

---

## 目录结构

```
frontend/src/
  components/
    layout/       (NavBar, Footer)
    landing/      (HeroSection, WhyTrust, WhyInsight, ...)
    dashboard/    (Overview panels)
    scanner/      (Scanner filters, list, preview)
    research/     (KLine, Chip, Agent, Report)
    ui/           (GlassCard, CtaButton, SignalBadge)
  views/          (Landing, Overview, Scanner, Research, Backtest, Methodology, About)
  router/         (index.js)
  stores/         (Pinia stores)
  styles/         (main.css, tokens.css)
  assets/         (images, icons)
```

---

## 禁止项

- 禁止出现 "// 后端数据对接留空"
- 禁止出现 "/* 样式请自行补充 */"
- 禁止内联 style (GSAP 动画控制除外)
- 禁止 !important
- 禁止硬编码颜色值
- 禁止硬编码 padding/margin 值 (使用 Tailwind class)
- 禁止 TypeScript any 类型
- 禁止匿名函数超过 5 行

---

## ECharts 规范

| 属性 | 值 |
|------|-----|
| 字体 | Inter |
| tooltip | 毛玻璃样式 |
| 坐标轴 | 灰色 |
| grid | 透明背景 |
| series | 渐变填充 |
| animation | 600ms |

---

## 命名规范

- 组件文件: PascalCase (HeroSection.vue)
- 目录: kebab-case (src/components/landing/)
- CSS class: kebab-case
- 变量/函数: camelCase
- Store: camelCase (useScannerStore)
