import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Landing', component: () => import('@/views/Landing.vue') },
  { path: '/overview', name: 'Overview', component: () => import('@/views/Overview.vue') },
  { path: '/scanner', name: 'Scanner', component: () => import('@/views/Scanner.vue') },
  { path: '/research/:code', name: 'Research', component: () => import('@/views/Research.vue') },
  { path: '/backtest', name: 'Backtest', component: () => import('@/views/Backtest.vue') },
  { path: '/methodology', name: 'Methodology', component: () => import('@/views/Methodology.vue') },
  { path: '/about', name: 'About', component: () => import('@/views/About.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// Route guard: first visit must go through Landing
router.beforeEach((to, from, next) => {
  const visited = sessionStorage.getItem('visited')
  if (!visited && to.path !== '/') {
    next('/')
  } else {
    next()
  }
})

export default router
