import { ref } from 'vue'
import {
  apiAddWatch,
  apiCreateGroup,
  apiDeleteGroup,
  apiGetWatchlist,
  apiListGroups,
  apiRemoveWatch,
  apiRenameGroup,
  apiSetSymbolGroups,
  type Group,
  type WatchItem,
} from '../api/watchlist'

const items = ref<WatchItem[]>([])
const groups = ref<Group[]>([])
const loading = ref(false)

export function useWatchlist() {
  async function reload(): Promise<void> {
    loading.value = true
    try {
      ;[items.value, groups.value] = await Promise.all([apiGetWatchlist(), apiListGroups()])
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
  async function createGroup(name: string): Promise<void> {
    await apiCreateGroup(name)
    await reload()
  }
  async function renameGroup(id: number, name: string): Promise<void> {
    await apiRenameGroup(id, name)
    await reload()
  }
  async function deleteGroup(id: number): Promise<void> {
    await apiDeleteGroup(id)
    await reload()
  }
  async function setSymbolGroups(symbol: string, groupIds: number[]): Promise<void> {
    await apiSetSymbolGroups(symbol, groupIds)
    await reload()
  }

  return {
    items,
    groups,
    loading,
    reload,
    add,
    remove,
    createGroup,
    renameGroup,
    deleteGroup,
    setSymbolGroups,
  }
}
