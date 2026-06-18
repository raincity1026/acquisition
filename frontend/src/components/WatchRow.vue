<script setup lang="ts">
import { ref } from 'vue'
import type { Group, WatchItem } from '../api/watchlist'
import { useSelection } from '../composables/useSelection'
import { useWatchlist } from '../composables/useWatchlist'

const props = defineProps<{ item: WatchItem; groups: Group[] }>()
const { view, inCompare, toggleCompare } = useSelection()
const { remove, setSymbolGroups } = useWatchlist()

const menuOpen = ref(false)

function isIn(gid: number): boolean {
  return props.item.group_ids.includes(gid)
}
async function toggleGroup(gid: number) {
  const next = isIn(gid)
    ? props.item.group_ids.filter((g) => g !== gid)
    : [...props.item.group_ids, gid]
  await setSymbolGroups(props.item.symbol, next)
}

function pctColor(v: number | null): string {
  if (v === null) return '#888'
  return v >= 0 ? '#d32f2f' : '#2e7d32' // 红涨绿跌
}
function fmtPct(v: number | null): string {
  if (v === null) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
</script>

<template>
  <li class="row">
    <input
      type="checkbox"
      title="加入对比"
      :checked="inCompare(item.symbol)"
      @change="toggleCompare(item.symbol)"
    />
    <span class="info" @click="view(item.symbol)">
      <span class="name">{{ item.name }}</span>
      <span class="code">{{ item.symbol }}</span>
    </span>
    <span class="quote">
      <span class="px">{{ item.last_close?.toFixed(2) ?? '—' }}</span>
      <span class="pct" :style="{ color: pctColor(item.change_pct) }">{{
        fmtPct(item.change_pct)
      }}</span>
    </span>
    <div class="grp">
      <button
        class="grp-btn"
        :disabled="groups.length === 0"
        title="设置分组"
        @click="menuOpen = !menuOpen"
      >
        ⊞
      </button>
      <template v-if="menuOpen">
        <div class="backdrop" @click="menuOpen = false"></div>
        <ul class="grp-menu">
          <li v-for="g in groups" :key="g.id">
            <label>
              <input type="checkbox" :checked="isIn(g.id)" @change="toggleGroup(g.id)" />
              {{ g.name }}
            </label>
          </li>
        </ul>
      </template>
    </div>
    <button class="x" title="从自选删除" @click="remove(item.symbol)">×</button>
  </li>
</template>

<style scoped>
.row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 6px;
}
.row:hover {
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
.grp {
  position: relative;
}
.grp-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #888;
  font-size: 14px;
}
.grp-btn:disabled {
  opacity: 0.3;
  cursor: default;
}
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 10;
}
.grp-menu {
  position: absolute;
  right: 0;
  top: 100%;
  z-index: 11;
  margin: 4px 0 0;
  padding: 4px;
  list-style: none;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
  min-width: 120px;
  max-height: 240px;
  overflow: auto;
}
.grp-menu label {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 6px;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
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
