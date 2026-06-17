// 与后端 /api/kline 返回结构对应
export interface ApiBar {
  date: string // "2024-12-31"
  open: number
  high: number
  low: number
  close: number
  volume: number | null
  amount: number | null
  trade_status: number // 1 正常 / 0 停牌
}

export type Period = 'd' | 'w' | 'm'
export type Adjust = 'qfq' | 'hfq' | 'none'

// M1 支持的指标。MA 叠主图，其余各自副图。
export type Indicator = 'MA' | 'VOL' | 'MACD' | 'KDJ' | 'RSI'

// 与后端 /api/compare 返回结构对应
export interface CompareSeries {
  symbol: string
  name: string
  values: (number | null)[] // 累计涨跌幅(%)，与 dates 对齐
  latest_pct: number | null
}

export interface CompareResponse {
  base_date: string
  dates: string[]
  series: CompareSeries[]
}
