/// <reference types="vite/client" />

interface ImportMetaEnv {
  // 后端 API 基地址；生产指向 https://api.stocks.marsian.cn，本地不设走 vite 代理
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
