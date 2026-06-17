import { ref, watch, type Ref } from 'vue'
import { fetchCompare } from '../api/compare'
import type { CompareResponse } from '../types/kline'

// 多股对比数据获取。symbols(≥2) 或 baseDate 变化即重新请求。
export function useCompare(symbols: Ref<string[]>, baseDate: Ref<string | null>) {
  const data = ref<CompareResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function reload() {
    if (symbols.value.length < 2) {
      data.value = null
      return
    }
    loading.value = true
    error.value = null
    try {
      data.value = await fetchCompare({ symbols: symbols.value, baseDate: baseDate.value })
    } catch (e: unknown) {
      data.value = null
      error.value = humanizeError(e)
    } finally {
      loading.value = false
    }
  }

  watch([symbols, baseDate], reload, { immediate: true, deep: true })

  return { data, loading, error, reload }
}

function humanizeError(e: unknown): string {
  if (typeof e === 'object' && e !== null && 'response' in e) {
    const resp = (e as { response?: { status?: number; data?: { detail?: string } } }).response
    if (resp?.status === 404) return resp.data?.detail ?? '有标的查无数据'
    if (resp?.status === 503) return '数据源暂不可用，请稍后重试'
    if (resp?.data?.detail) return resp.data.detail
  }
  return '对比请求失败，请检查后端是否已启动'
}
