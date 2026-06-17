<script setup lang="ts">
import { computed, ref } from 'vue'
import ChartToolbar from '../components/ChartToolbar.vue'
import ChartView from '../components/ChartView.vue'
import CompareChart from '../components/CompareChart.vue'
import { useCompare } from '../composables/useCompare'
import { useKline } from '../composables/useKline'
import { useSelection } from '../composables/useSelection'
import type { Adjust, Indicator, Period } from '../types/kline'

const { symbols, toggleCompare } = useSelection()
const isCompare = computed(() => symbols.value.length >= 2)
const isEmpty = computed(() => symbols.value.length === 0)

// 单股态
const primary = computed(() => symbols.value[0] ?? '')
const period = ref<Period>('d')
const adjust = ref<Adjust>('qfq')
const indicators = ref<Indicator[]>(['MA', 'VOL'])
const { bars, loading: sLoading, error: sError } = useKline(primary, period, adjust)

// 对比态
const baseDate = ref<string | null>(null)
const logAxis = ref(false)
const { data: cmp, loading: cLoading, error: cError } = useCompare(symbols, baseDate)
</script>

<template>
  <div class="market">
    <div v-if="isEmpty" class="empty">← 从左侧自选勾选，或用上方搜索选择标的</div>

    <!-- 单股态 -->
    <template v-else-if="!isCompare">
      <ChartToolbar
        v-model:period="period"
        v-model:adjust="adjust"
        v-model:indicators="indicators"
      />
      <div class="status">
        <span v-if="sLoading">加载中…</span>
        <span v-else-if="sError" class="err">{{ sError }}</span>
        <span v-else class="muted">{{ primary }} · {{ bars.length }} 根</span>
      </div>
      <ChartView :bars="bars" :indicators="indicators" />
    </template>

    <!-- 对比态 -->
    <template v-else>
      <div class="cmp-toolbar">
        <span v-for="s in symbols" :key="s" class="chip">
          {{ s }}
          <button class="x" @click="toggleCompare(s)">×</button>
        </span>
        <label class="ctl">基准日 <input type="date" v-model="baseDate" /></label>
        <label class="ctl chk"><input type="checkbox" v-model="logAxis" /> 对数轴</label>
        <span class="muted">归一化对比（指标已隐藏）</span>
      </div>
      <div class="status">
        <span v-if="cLoading">加载中…</span>
        <span v-else-if="cError" class="err">{{ cError }}</span>
        <span v-else-if="cmp" class="muted">基准日 {{ cmp.base_date }} = 0%</span>
      </div>
      <CompareChart v-if="cmp" :resp="cmp" :log-axis="logAxis" />
    </template>
  </div>
</template>

<style scoped>
.market {
  min-width: 0;
}
.empty {
  color: #999;
  padding: 60px 20px;
  text-align: center;
}
.cmp-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 16px;
  padding: 4px 12px 10px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: #f0f2f5;
  border-radius: 14px;
  font-size: 13px;
}
.chip .x {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #888;
  font-size: 15px;
  line-height: 1;
}
.ctl {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}
.status {
  padding: 0 12px 6px;
  min-height: 20px;
  font-size: 13px;
}
.err {
  color: #c62828;
}
.muted {
  color: #888;
}
</style>
