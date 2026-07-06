import axios from 'axios'

export interface InstrumentDetail {
  symbol: string
  name: string
  market: string
  type: string
  ipo_date: string | null
  industry: string | null
  pe_ttm: number | null
  pb_mrq: number | null
  total_mv: number | null
  circ_mv: number | null
}

// 调后端 GET /api/instrument/{symbol}：低频基本面（name/市场/上市日 + PE/PB/行业/市值）
export async function fetchInstrument(symbol: string): Promise<InstrumentDetail> {
  const { data } = await axios.get<InstrumentDetail>(`/api/instrument/${symbol}`)
  return data
}
