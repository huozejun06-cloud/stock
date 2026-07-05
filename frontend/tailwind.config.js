/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#080B13',
          secondary: '#0d0e14',
          tertiary: '#12131a',
          card: '#111318',
        },
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          dim: '#64748b',
        },
        accent: {
          purple: '#8b5cf6',
          orange: '#ff6b35',
          gold: '#f0c040',
          highlight: '#6c8cff',
        },
        signal: {
          buy: '#21d07a',
          watch: '#eab308',
          sell: '#ff5b6e',
        },
        border: {
          DEFAULT: '#1e293b',
          hover: '#334155',
        },
      },
      boxShadow: {
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.3)',
        'glow-orange': '0 0 20px rgba(255, 107, 53, 0.3)',
        'glow-highlight': '0 0 20px rgba(108, 140, 255, 0.3)',
      },
      backdropBlur: {
        glass: '26px',
      },
      fontFamily: {
        hero: ['Noto Serif SC', 'serif'],
        body: ['HarmonyOS Sans SC', 'PingFang SC', 'sans-serif'],
        number: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
