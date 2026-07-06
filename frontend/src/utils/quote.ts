import type { ApiBar } from '../types/kline'

export interface QuoteSummary {
  last: number
  changePct: number | null // 涨跌幅(%)，无昨收时 null
  open: number
  high: number
  low: number
  prevClose: number | null
  volume: number | null
  amount: number | null
  amplitude: number | null // 振幅(%) = (最高-最低)/昨收*100
  high52: number | null
  low52: number | null
}

const WINDOW = 250 // 约一年交易日

export function deriveQuote(bars: ApiBar[]): QuoteSummary | null {
  if (bars.length === 0) return null
  const last = bars[bars.length - 1]
  const prevClose = bars.length >= 2 ? bars[bars.length - 2].close : null
  const changePct = prevClose ? ((last.close - prevClose) / prevClose) * 100 : null
  const amplitude = prevClose ? ((last.high - last.low) / prevClose) * 100 : null
  const window = bars.slice(-WINDOW)
  const high52 = Math.max(...window.map((b) => b.high))
  const low52 = Math.min(...window.map((b) => b.low))
  return {
    last: last.close,
    changePct,
    open: last.open,
    high: last.high,
    low: last.low,
    prevClose,
    volume: last.volume,
    amount: last.amount,
    amplitude,
    high52,
    low52,
  }
}
