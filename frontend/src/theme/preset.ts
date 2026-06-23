import { definePreset } from '@primevue/themes'
import Aura from '@primevue/themes/aura'

// 让 PrimeVue 组件的主色与设计令牌（tokens.css 的 --c-primary-*）一致。
export const AppPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
      950: '#172554',
    },
    // 圆角与令牌对齐
    borderRadius: {
      none: '0',
      xs: '4px',
      sm: '6px',
      md: '6px',
      lg: '8px',
      xl: '12px',
    },
  },
})
