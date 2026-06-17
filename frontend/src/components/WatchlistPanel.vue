<script setup lang="ts">
import { onMounted } from 'vue'
import { useSelection } from '../composables/useSelection'
import { useWatchlist } from '../composables/useWatchlist'

const { items, reload, remove } = useWatchlist()
const { view, inCompare, toggleCompare } = useSelection()

onMounted(reload)

function pctColor(v: number | null): string {
  if (v === null) return '#888'
  return v >= 0 ? '#d32f2f' : '#2e7d32' // A股红涨绿跌
}
function fmtPct(v: number | null): string {
  if (v === null) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
</script>

<template>
  <aside class="watchlist">
    <h3>自选股</h3>
    <p v-if="items.length === 0" class="empty">用上方搜索添加标的</p>
    <ul>
      <li v-for="it in items" :key="it.symbol">
        <input
          type="checkbox"
          title="加入对比"
          :checked="inCompare(it.symbol)"
          @change="toggleCompare(it.symbol)"
        />
        <span class="info" @click="view(it.symbol)">
          <span class="name">{{ it.name }}</span>
          <span class="code">{{ it.symbol }}</span>
        </span>
        <span class="quote">
          <span class="px">{{ it.last_close?.toFixed(2) ?? '—' }}</span>
          <span class="pct" :style="{ color: pctColor(it.change_pct) }">{{
            fmtPct(it.change_pct)
          }}</span>
        </span>
        <button class="x" title="删除" @click="remove(it.symbol)">×</button>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.watchlist {
  width: 240px;
  border-right: 1px solid #eee;
  padding: 10px 8px;
}
.watchlist h3 {
  font-size: 14px;
  margin: 4px 8px 10px;
}
.empty {
  color: #999;
  font-size: 13px;
  padding: 0 8px;
}
ul {
  list-style: none;
  margin: 0;
  padding: 0;
}
li {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 6px;
}
li:hover {
  background: #f6f7f9;
}
.info {
  display: flex;
  flex-direction: column;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}
.name {
  font-size: 13px;
}
.code {
  font-size: 11px;
  color: #999;
}
.quote {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.px {
  font-size: 13px;
}
.pct {
  font-size: 11px;
}
.x {
  border: none;
  background: transparent;
  color: #bbb;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}
.x:hover {
  color: #c62828;
}
</style>
