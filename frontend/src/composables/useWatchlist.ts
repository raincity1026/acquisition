import { ref } from 'vue'
import { apiAddWatch, apiGetWatchlist, apiRemoveWatch, type WatchItem } from '../api/watchlist'

const items = ref<WatchItem[]>([])
const loading = ref(false)

export function useWatchlist() {
  async function reload(): Promise<void> {
    loading.value = true
    try {
      items.value = await apiGetWatchlist()
    } finally {
      loading.value = false
    }
  }
  async function add(symbol: string): Promise<void> {
    await apiAddWatch(symbol)
    await reload()
    // 后端异步抓行情，稍后再刷一次以显示最新价/涨跌幅
    setTimeout(reload, 2500)
  }
  async function remove(symbol: string): Promise<void> {
    await apiRemoveWatch(symbol)
    await reload()
  }

  return { items, loading, reload, add, remove }
}
