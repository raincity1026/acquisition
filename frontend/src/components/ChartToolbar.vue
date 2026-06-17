<script setup lang="ts">
import type { Adjust, Indicator, Period } from '../types/kline'

const period = defineModel<Period>('period', { required: true })
const adjust = defineModel<Adjust>('adjust', { required: true })
const indicators = defineModel<Indicator[]>('indicators', { required: true })

const PERIODS: { v: Period; label: string }[] = [
  { v: 'd', label: '日' },
  { v: 'w', label: '周' },
  { v: 'm', label: '月' },
]
const ADJUSTS: { v: Adjust; label: string }[] = [
  { v: 'qfq', label: '前复权' },
  { v: 'hfq', label: '后复权' },
  { v: 'none', label: '不复权' },
]
const INDICATORS: Indicator[] = ['MA', 'VOL', 'MACD', 'KDJ', 'RSI']
</script>

<template>
  <div class="toolbar">
    <div class="group seg">
      <button
        v-for="p in PERIODS"
        :key="p.v"
        :class="{ active: period === p.v }"
        @click="period = p.v"
      >
        {{ p.label }}
      </button>
    </div>

    <div class="group seg">
      <button
        v-for="a in ADJUSTS"
        :key="a.v"
        :class="{ active: adjust === a.v }"
        @click="adjust = a.v"
      >
        {{ a.label }}
      </button>
    </div>

    <div class="group">
      <label v-for="ind in INDICATORS" :key="ind" class="chk">
        <input type="checkbox" :value="ind" v-model="indicators" />
        {{ ind }}
      </label>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  padding: 4px 12px 10px;
}
.group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.seg button.active {
  background: #1565c0;
  color: #fff;
  border-color: #1565c0;
}
.chk {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  cursor: pointer;
}
button {
  padding: 5px 10px;
  cursor: pointer;
}
</style>
