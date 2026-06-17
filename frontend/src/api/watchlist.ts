import axios from 'axios'

export interface WatchItem {
  symbol: string
  name: string
  last_close: number | null
  change_pct: number | null
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
