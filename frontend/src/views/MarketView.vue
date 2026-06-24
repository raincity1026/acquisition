<script setup lang="ts">
import Chip from 'primevue/chip'
import DatePicker from 'primevue/datepicker'
import ToggleSwitch from 'primevue/toggleswitch'
import { computed, ref, watch } from 'vue'
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
const baseDateObj = ref<Date | null>(null)
watch(baseDateObj, (d) => {
  baseDate.value = d
    ? `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    : null
})
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
        <Chip
          v-for="s in symbols"
          :key="s"
          :label="s"
          removable
          @remove="toggleCompare(s)"
        />
        <label class="ctl">
          基准日
          <DatePicker v-model="baseDateObj" date-format="yy-mm-dd" show-icon size="small" placeholder="默认起点" />
        </label>
        <label class="ctl"><ToggleSwitch v-model="logAxis" /> 对数轴</label>
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
  color: var(--c-text-tertiary);
  padding: 60px 20px;
  text-align: center;
}
.cmp-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-4);
  padding: var(--space-1) var(--space-3) var(--space-3);
}
.ctl {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
}
.status {
  padding: 0 var(--space-3) var(--space-2);
  min-height: 20px;
  font-size: var(--fs-sm);
}
.err {
  color: var(--c-danger);
}
.muted {
  color: var(--c-text-tertiary);
}
</style>
