import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import { createApp } from 'vue'
import 'primeicons/primeicons.css'
import './styles/tokens.css'
import './style.css'
import './api/http' // 安装 axios 拦截器（JWT 注入 + 401 跳登录）
import App from './App.vue'
import router from './router'
import { AppPreset } from './theme/preset'

createApp(App)
  .use(router)
  .use(PrimeVue, {
    theme: { preset: AppPreset, options: { darkModeSelector: '.dark', cssLayer: false } },
  })
  .use(ToastService)
  .use(ConfirmationService)
  .mount('#app')
