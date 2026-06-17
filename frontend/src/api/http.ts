// 集中配置全局 axios：自动带 JWT；401 清 token 跳登录。
import axios from 'axios'
import { clearToken, getToken } from '../auth/token'

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
