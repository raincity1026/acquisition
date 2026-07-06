import { describe, expect, it } from 'vitest'
import type { ApiBar } from '../types/kline'
import { deriveQuote } from './quote'

function bar(date: string, o: number, h: number, l: number, c: number): ApiBar {
  return { date, open: o, high: h, low: l, close: c, volume: 100, amount: 1000, trade_status: 1 }
}

describe('deriveQuote', () => {
  it('空数组返回 null', () => {
    expect(deriveQuote([])).toBeNull()
  })

  it('单根：prevClose/changePct 为 null，52 周取自身', () => {
    const q = deriveQuote([bar('2026-01-02', 10, 12, 9, 11)])!
    expect(q.last).toBe(11)
    expect(q.prevClose).toBeNull()
    expect(q.changePct).toBeNull()
    expect(q.high52).toBe(12)
    expect(q.low52).toBe(9)
  })

  it('两根：涨跌幅与振幅按昨收算', () => {
    const q = deriveQuote([bar('2026-01-02', 10, 11, 9, 10), bar('2026-01-03', 10, 13, 10, 12)])!
    expect(q.changePct).toBeCloseTo(20) // (12-10)/10*100
    expect(q.amplitude).toBeCloseTo(30) // (13-10)/10*100
    expect(q.high52).toBe(13)
    expect(q.low52).toBe(9)
  })
})
