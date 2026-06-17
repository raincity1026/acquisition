<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { CompareResponse } from '../types/kline'

const props = defineProps<{
  resp: CompareResponse
  logAxis: boolean
}>()

// 区分标的的线色（避开红/绿，免与涨跌色混淆）
const PALETTE = ['#1565c0', '#ef6c00', '#00897b', '#6a1b9a', '#5d4037', '#c2185b', '#546e7a', '#00838f']

const container = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function colorOf(i: number): string {
  return PALETTE[i % PALETTE.length]
}

// 图例：名称 + 当前累计涨跌幅，红涨绿跌
const legend = computed(() =>
  props.resp.series.map((s, i) => ({
    name: s.name,
    color: colorOf(i),
    pct: s.latest_pct,
  })),
)

function fmtPct(v: number | null): string {
  if (v === null) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
function pctColor(v: number | null): string {
  if (v === null) return '#888'
  return v >= 0 ? '#d32f2f' : '#2e7d32' // A股红涨绿跌
}

function buildOption(): echarts.EChartsCoreOption {
  const { dates, series, base_date } = props.resp
  const log = props.logAxis
  return {
    animation: false,
    grid: { left: 60, right: 24, top: 16, bottom: 40 },
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const arr = params as { axisValue: string; value: number | null; color: string; seriesName: string }[]
        const head = `<div style="margin-bottom:4px">${arr[0]?.axisValue ?? ''}</div>`
        const rows = arr
          .map((p) => {
            if (p.value === null) return ''
            const pct = log ? (Number(p.value) - 1) * 100 : Number(p.value)
            const c = pct >= 0 ? '#d32f2f' : '#2e7d32'
            return `<div><span style="color:${p.color}">●</span> ${p.seriesName}: <b style="color:${c}">${fmtPct(pct)}</b></div>`
          })
          .join('')
        return head + rows
      },
    },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: log
      ? { type: 'log', axisLabel: { formatter: (v: number) => `${((v - 1) * 100).toFixed(0)}%` } }
      : { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: series.map((s, i) => ({
      name: s.name,
      type: 'line',
      showSymbol: false,
      connectNulls: false, // 上市晚/base前的 null 不连线
      lineStyle: { width: 1.6 },
      color: colorOf(i),
      data: s.values.map((v) => (v === null ? null : log ? 1 + v / 100 : v)),
      // 基准日竖虚线 + 0% 基准横线（只挂在第一条上，silent）
      markLine:
        i === 0
          ? {
              silent: true,
              symbol: 'none',
              label: { formatter: '基准日', position: 'insideEndTop', color: '#999' },
              lineStyle: { type: 'dashed', color: '#bbb' },
              data: [{ xAxis: base_date }, { yAxis: log ? 1 : 0 }],
            }
          : undefined,
    })),
  }
}

function render() {
  if (chart) chart.setOption(buildOption(), true)
}

function onResize() {
  chart?.resize()
}

onMounted(() => {
  chart = echarts.init(container.value!)
  render()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})

watch(() => [props.resp, props.logAxis], render, { deep: true })
</script>

<template>
  <div class="compare">
    <div class="legend">
      <span v-for="item in legend" :key="item.name" class="item">
        <span class="dot" :style="{ background: item.color }"></span>
        {{ item.name }}
        <b :style="{ color: pctColor(item.pct) }">{{ fmtPct(item.pct) }}</b>
      </span>
    </div>
    <div ref="container" class="chart"></div>
  </div>
</template>

<style scoped>
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 4px 12px 8px;
  font-size: 13px;
}
.legend .item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.chart {
  width: 100%;
  height: 520px;
}
</style>
