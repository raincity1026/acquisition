import axios from 'axios'

export interface WatchItem {
  symbol: string
  name: string
  last_close: number | null
  change_pct: number | null
  group_ids: number[]
}

export interface Group {
  id: number
  name: string
}

export interface SearchHit {
  symbol: string
  name: string
  market: string
  type: string
}

export async function apiGetWatchlist(): Promise<WatchItem[]> {
  const { data } = await axios.get<WatchItem[]>('/api/watchlist')
  return data
}

export async function apiAddWatch(symbol: string): Promise<void> {
  await axios.post('/api/watchlist', { symbol })
}

export async function apiRemoveWatch(symbol: string): Promise<void> {
  await axios.delete(`/api/watchlist/${symbol}`)
}

export async function apiSearch(q: string): Promise<SearchHit[]> {
  const { data } = await axios.get<SearchHit[]>('/api/search', { params: { q, limit: 15 } })
  return data
}

// ---- 分组 ----
export async function apiListGroups(): Promise<Group[]> {
  const { data } = await axios.get<Group[]>('/api/watchlist/groups')
  return data
}

export async function apiCreateGroup(name: string): Promise<Group> {
  const { data } = await axios.post<Group>('/api/watchlist/groups', { name })
  return data
}

export async function apiRenameGroup(id: number, name: string): Promise<void> {
  await axios.patch(`/api/watchlist/groups/${id}`, { name })
}

export async function apiDeleteGroup(id: number): Promise<void> {
  await axios.delete(`/api/watchlist/groups/${id}`)
}

export async function apiSetSymbolGroups(symbol: string, groupIds: number[]): Promise<void> {
  await axios.put(`/api/watchlist/${symbol}/groups`, { group_ids: groupIds })
}
