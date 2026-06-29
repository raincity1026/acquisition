// 集中配置全局 axios：API 基地址、自动带 JWT、401 清 token 跳登录。
import axios from 'axios'
import { clearToken, getToken } from '../auth/token'

// 生产(EdgeOne 构建)设 VITE_API_BASE=https://api.stocks.marsian.cn；
// 本地开发不设 → 空 → 相对路径 /api 走 vite 代理。
axios.defaults.baseURL = import.meta.env.VITE_API_BASE || ''

axios.interceptors.request.use((cfg) => {
  const t = getToken()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

axios.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      clearToken()
      if (location.pathname !== '/login') location.assign('/login')
    }
    return Promise.reject(err)
  },
)
