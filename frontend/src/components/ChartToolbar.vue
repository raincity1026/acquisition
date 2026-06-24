<script setup lang="ts">
import SelectButton from 'primevue/selectbutton'
import type { Adjust, Indicator, Period } from '../types/kline'

const period = defineModel<Period>('period', { required: true })
const adjust = defineModel<Adjust>('adjust', { required: true })
const indicators = defineModel<Indicator[]>('indicators', { required: true })

const PERIODS = [
  { label: '日', value: 'd' },
  { label: '周', value: 'w' },
  { label: '月', value: 'm' },
]
const ADJUSTS = [
  { label: '前复权', value: 'qfq' },
  { label: '后复权', value: 'hfq' },
  { label: '不复权', value: 'none' },
]
const INDICATORS: Indicator[] = ['MA', 'VOL', 'MACD', 'KDJ', 'RSI']
</script>

<template>
  <div class="toolbar">
    <SelectButton
      v-model="period"
      :options="PERIODS"
      option-label="label"
      option-value="value"
      :allow-empty="false"
      size="small"
    />
    <SelectButton
      v-model="adjust"
      :options="ADJUSTS"
      option-label="label"
      option-value="value"
      :allow-empty="false"
      size="small"
    />
    <SelectButton v-model="indicators" :options="INDICATORS" multiple size="small" />
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  align-items: center;
  padding: var(--space-1) var(--space-3) var(--space-3);
}
</style>
