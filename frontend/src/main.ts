import { createApp } from 'vue'
import './style.css'
import './api/http' // 安装 axios 拦截器（JWT 注入 + 401 跳登录）
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
