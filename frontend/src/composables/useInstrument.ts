import { ref, watch, type Ref } from 'vue'
import { fetchInstrument, type InstrumentDetail } from '../api/instrument'

// 详情随 symbol 变化重取；失败不致命（detail=null，前端显示「—」）
export function useInstrument(symbol: Ref<string>) {
  const detail = ref<InstrumentDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function reload() {
    const sym = symbol.value.trim()
    if (!sym) {
      detail.value = null
      return
    }
    loading.value = true
    error.value = null
    try {
      detail.value = await fetchInstrument(sym)
    } catch {
      detail.value = null
      error.value = '详情加载失败'
    } finally {
      loading.value = false
    }
  }

  watch(symbol, reload, { immediate: true })

  return { detail, loading, error }
}
