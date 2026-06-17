import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../auth/token'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/HomeView.vue'), meta: { auth: true } },
    { path: '/login', component: () => import('../views/LoginView.vue') },
    { path: '/register', component: () => import('../views/RegisterView.vue') },
  ],
})

// 路由守卫：受保护页未登录 → 跳登录；已登录访问登录/注册 → 跳首页
router.beforeEach((to) => {
  const authed = !!getToken()
  if (to.meta.auth && !authed) return '/login'
  if ((to.path === '/login' || to.path === '/register') && authed) return '/'
  return true
})

export default router
