import axios from 'axios'
import type { CompareResponse } from '../types/kline'

export interface CompareQuery {
  symbols: string[]
  baseDate?: string | null
  start?: string
  end?: string
}

// 调 M2 的 GET /api/compare。对齐与归一化都由后端算。
export async function fetchCompare(q: CompareQuery): Promise<CompareResponse> {
  const { data } = await axios.get<CompareResponse>('/api/compare', {
    params: {
      symbols: q.symbols.join(','),
      base_date: q.baseDate || undefined,
      start: q.start,
      end: q.end,
    },
  })
  return data
}
