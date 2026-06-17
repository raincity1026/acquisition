import { ref, watch, type Ref } from 'vue'
import { fetchKline } from '../api/kline'
import type { Adjust, ApiBar, Period } from '../types/kline'

// 数据获取 + loading/error 状态。symbol/period/adjust 任一变化即重新请求。
export function useKline(symbol: Ref<string>, period: Ref<Period>, adjust: Ref<Adjust>) {
  const bars = ref<ApiBar[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function reload() {
    const sym = symbol.value.trim()
    if (!sym) return
    loading.value = true
    error.value = null
    try {
      bars.value = await fetchKline({ symbol: sym, period: period.value, adjust: adjust.value })
      if (bars.value.length === 0) error.value = `「${sym}」无数据`
    } catch (e: unknown) {
      bars.value = []
      error.value = humanizeError(e)
    } finally {
      loading.value = false
    }
  }

  watch([symbol, period, adjust], reload, { immediate: true })

  return { bars, loading, error, reload }
}

function humanizeError(e: unknown): string {
  if (typeof e === 'object' && e !== null && 'response' in e) {
    const resp = (e as { response?: { status?: number; data?: { detail?: string } } }).response
    if (resp?.status === 404) return resp.data?.detail ?? '未知标的'
    if (resp?.status === 503) return '数据源暂不可用，请稍后重试'
    if (resp?.data?.detail) return resp.data.detail
  }
  return '请求失败，请检查后端是否已启动'
}
