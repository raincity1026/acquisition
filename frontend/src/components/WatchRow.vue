<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import type { WatchItem } from '../api/watchlist'
import { useSelection } from '../composables/useSelection'
import { useWatchlist } from '../composables/useWatchlist'

defineProps<{ item: WatchItem }>()
const { view, inCompare, toggleCompare } = useSelection()
const { remove } = useWatchlist()

function cls(v: number | null): string {
  if (v === null || v === 0) return 'text-flat'
  return v > 0 ? 'text-up' : 'text-down'
}
function fmtPct(v: number | null): string {
  if (v === null) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`
}
</script>

<template>
  <li class="row">
    <Checkbox
      :model-value="inCompare(item.symbol)"
      binary
      aria-label="加入对比"
      @update:model-value="() => toggleCompare(item.symbol)"
    />
    <span class="info" @click="view(item.symbol)">
      <span class="name">{{ item.name }}</span>
      <span class="code">{{ item.symbol }}</span>
    </span>
    <span class="quote tnum">
      <span class="px">{{ item.last_close?.toFixed(2) ?? '—' }}</span>
      <span class="pct" :class="cls(item.change_pct)">{{ fmtPct(item.change_pct) }}</span>
    </span>
    <Button
      class="del-btn"
      icon="pi pi-times"
      text
      rounded
      size="small"
      severity="secondary"
      aria-label="从自选删除"
      @click="remove(item.symbol)"
    />
  </li>
</template>

<style scoped>
.row {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
}
.row:hover {
  background: var(--c-surface-50);
}
.info {
  display: flex;
  flex-direction: column;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}
.name {
  font-size: var(--fs-sm);
}
.code {
  font-size: var(--fs-caption);
  color: var(--c-text-tertiary);
}
.quote {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.px {
  font-size: var(--fs-sm);
}
.pct {
  font-size: var(--fs-caption);
}
.row :deep(.p-button) {
  width: 26px;
  height: 26px;
}
/* 删除按钮绝对定位、默认脱离文档流（不占位，行内容用满宽度）。
   hover 该行/键盘聚焦时：报价淡出、× 在原位淡入（互换），避免叠字，也不抖动。 */
.del-btn {
  position: absolute;
  right: var(--space-1);
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s;
}
.quote {
  transition: opacity 0.12s;
}
.row:hover .quote,
.row:focus-within .quote {
  opacity: 0;
}
.row:hover .del-btn,
.row:focus-within .del-btn {
  opacity: 1;
  pointer-events: auto;
}
</style>
