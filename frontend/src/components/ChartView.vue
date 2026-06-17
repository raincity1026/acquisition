<script setup lang="ts">
import { dispose, init, type Chart, type KLineData } from 'klinecharts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { ApiBar, Indicator } from '../types/kline'

const props = defineProps<{
  bars: ApiBar[]
  indicators: Indicator[] // 当前开启的指标
}>()

const container = ref<HTMLDivElement | null>(null)
let chart: Chart | null = null

// 主图 pane id（klinecharts v9 常量）。MA 叠这里，其余指标各建独立副图。
const MAIN_PANE = 'candle_pane'
// 已创建指标 → 所在 paneId
const created = new Map<Indicator, string>()

function toKLineData(bars: ApiBar[]): KLineData[] {
  return bars.map((b) => ({
    timestamp: new Date(b.date).getTime(), // date 字符串 → 毫秒时间戳
    open: b.open,
    high: b.high,
    low: b.low,
    close: b.close,
    volume: b.volume ?? undefined,
    turnover: b.amount ?? undefined, // amount → turnover
  }))
}

function applyData() {
  if (chart) chart.applyNewData(toKLineData(props.bars))
}

function addIndicator(name: Indicator) {
  if (!chart || created.has(name)) return
  if (name === 'MA') {
    // 叠加主图，默认周期 5/10/20/60
    const id = chart.createIndicator({ name: 'MA', calcParams: [5, 10, 20, 60] }, true, {
      id: MAIN_PANE,
    })
    if (id) created.set('MA', MAIN_PANE)
  } else {
    const id = chart.createIndicator(name) // 独立副图
    if (id) created.set(name, id)
  }
}

function removeIndicator(name: Indicator) {
  if (!chart) return
  const paneId = created.get(name)
  if (paneId === undefined) return
  chart.removeIndicator(paneId, name)
  created.delete(name)
}

function syncIndicators() {
  const want = new Set(props.indicators)
  for (const name of want) addIndicator(name)
  for (const name of [...created.keys()]) {
    if (!want.has(name)) removeIndicator(name)
  }
}

onMounted(() => {
  chart = init(container.value!)
  applyData()
  syncIndicators()
})

onBeforeUnmount(() => {
  if (container.value) dispose(container.value)
  chart = null
  created.clear()
})

watch(() => props.bars, applyData)
watch(() => props.indicators, syncIndicators, { deep: true })
</script>

<template>
  <div ref="container" class="chart"></div>
</template>

<style scoped>
.chart {
  width: 100%;
  height: 560px;
}
</style>
