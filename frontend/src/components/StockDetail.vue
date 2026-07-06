<script setup lang="ts">
import { computed } from 'vue'
import type { InstrumentDetail } from '../api/instrument'
import { deriveQuote } from '../utils/quote'
import type { ApiBar } from '../types/kline'
import GroupAssignButton from './GroupAssignButton.vue'

const props = defineProps<{
  symbol: string
  bars: ApiBar[]
  detail: InstrumentDetail | null
}>()

const q = computed(() => deriveQuote(props.bars))
const name = computed(() => props.detail?.name ?? props.symbol)
// 涨跌染色：changePct 为 null 或 0 时视为平（中性色），避免误导性红绿
const changeClass = computed(() => {
  const p = q.value?.changePct
  if (p === null || p === undefined || p === 0) return 'text-flat'
  return p > 0 ? 'text-up' : 'text-down'
})

function pct(v: number | null): string {
  return v === null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
function num(v: number | null, digits = 2): string {
  return v === null ? '—' : v.toFixed(digits)
}
// 市值(元) → 亿/万亿
function money(v: number | null): string {
  if (v === null) return '—'
  if (v >= 1e12) return `${(v / 1e12).toFixed(2)}万亿`
  return `${(v / 1e8).toFixed(2)}亿`
}
// 成交额(元) → 亿；成交量(手)
function amount(v: number | null): string {
  return v === null ? '—' : `${(v / 1e8).toFixed(2)}亿`
}
function vol(v: number | null): string {
  return v === null ? '—' : `${(v / 1e4).toFixed(1)}万手`
}
</script>

<template>
  <div class="detail">
    <div class="head">
      <span class="name">{{ name }}</span>
      <span class="sym">{{ symbol }}</span>
      <span v-if="detail?.industry" class="tag">{{ detail.industry }}</span>
      <GroupAssignButton :symbol="symbol" />
    </div>

    <div class="quote">
      <span class="price tnum" :class="changeClass">{{ num(q?.last ?? null) }}</span>
      <span class="chg tnum" :class="changeClass">{{ pct(q?.changePct ?? null) }}</span>
    </div>

    <div class="grid">
      <span>今开 <b class="tnum">{{ num(q?.open ?? null) }}</b></span>
      <span>最高 <b class="tnum">{{ num(q?.high ?? null) }}</b></span>
      <span>最低 <b class="tnum">{{ num(q?.low ?? null) }}</b></span>
      <span>昨收 <b class="tnum">{{ num(q?.prevClose ?? null) }}</b></span>
      <span>振幅 <b class="tnum">{{ pct(q?.amplitude ?? null) }}</b></span>
      <span>量 <b class="tnum">{{ vol(q?.volume ?? null) }}</b></span>
      <span>额 <b class="tnum">{{ amount(q?.amount ?? null) }}</b></span>
      <span>52周 <b class="tnum">{{ num(q?.low52 ?? null) }}~{{ num(q?.high52 ?? null) }}</b></span>
      <span>PE <b class="tnum">{{ num(detail?.pe_ttm ?? null) }}</b></span>
      <span>PB <b class="tnum">{{ num(detail?.pb_mrq ?? null) }}</b></span>
      <span>总市值 <b class="tnum">{{ money(detail?.total_mv ?? null) }}</b></span>
      <span>流通 <b class="tnum">{{ money(detail?.circ_mv ?? null) }}</b></span>
      <span>上市 <b>{{ detail?.ipo_date ?? '—' }}</b></span>
    </div>
  </div>
</template>

<style scoped>
.detail {
  padding: var(--space-3);
  border-bottom: 1px solid var(--c-border);
}
.head {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}
.name {
  font-size: var(--fs-md);
  font-weight: var(--fw-semibold);
}
.sym {
  color: var(--c-text-tertiary);
  font-size: var(--fs-sm);
}
.tag {
  font-size: var(--fs-caption);
  color: var(--c-text-secondary);
  background: var(--c-surface-50);
  border-radius: var(--radius-sm);
  padding: 0 var(--space-2);
}
.quote {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin: var(--space-2) 0;
}
.price {
  font-size: var(--fs-xl);
  font-weight: var(--fw-semibold);
}
.chg {
  font-size: var(--fs-md);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: var(--space-1) var(--space-4);
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
}
.grid b {
  color: var(--c-text);
  font-weight: var(--fw-medium);
}
</style>
