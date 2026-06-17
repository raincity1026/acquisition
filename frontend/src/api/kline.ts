import axios from 'axios'
import type { Adjust, ApiBar, Period } from '../types/kline'

export interface KlineQuery {
  symbol: string
  period: Period
  adjust: Adjust
  start?: string
  end?: string
}

// 调 M0 的 GET /api/kline。复权与周/月聚合都由后端算，前端不自算。
export async function fetchKline(q: KlineQuery): Promise<ApiBar[]> {
  const { data } = await axios.get<ApiBar[]>('/api/kline', {
    params: {
      symbol: q.symbol,
      period: q.period,
      adjust: q.adjust,
      start: q.start,
      end: q.end,
    },
  })
  return data
}
