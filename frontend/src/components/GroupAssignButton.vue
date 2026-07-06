<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Popover from 'primevue/popover'
import { computed, ref } from 'vue'
import { useWatchlist } from '../composables/useWatchlist'

const props = defineProps<{ symbol: string }>()
const { items, groups, add, setSymbolGroups } = useWatchlist()

const op = ref()

// 当前标的在自选中的归组（不在自选则视为空）
const groupIds = computed(
  () => items.value.find((i) => i.symbol === props.symbol)?.group_ids ?? [],
)
const watched = computed(() => items.value.some((i) => i.symbol === props.symbol))
// 已归入分组时，标签后加 (n) 表示当前所属分组数
const btnLabel = computed(() =>
  groupIds.value.length > 0 ? `自选分组(${groupIds.value.length})` : '自选分组',
)

function isIn(gid: number): boolean {
  return groupIds.value.includes(gid)
}
async function toggleGroup(gid: number) {
  // 未在自选：先加入自选，再归入该组（“+自选分组”一步到位）
  if (!watched.value) {
    await add(props.symbol)
    await setSymbolGroups(props.symbol, [gid])
    return
  }
  const next = isIn(gid) ? groupIds.value.filter((g) => g !== gid) : [...groupIds.value, gid]
  await setSymbolGroups(props.symbol, next)
}
</script>

<template>
  <Button
    class="grp-btn"
    icon="pi pi-plus"
    :label="btnLabel"
    text
    size="small"
    severity="secondary"
    :disabled="groups.length === 0"
    aria-label="加入自选分组"
    @click="op.toggle($event)"
  />

  <Popover ref="op">
    <ul class="grp-menu">
      <li v-for="g in groups" :key="g.id">
        <Checkbox
          :model-value="isIn(g.id)"
          binary
          :input-id="'sd-g' + g.id + symbol"
          @update:model-value="() => toggleGroup(g.id)"
        />
        <label :for="'sd-g' + g.id + symbol">{{ g.name }}</label>
      </li>
    </ul>
  </Popover>
</template>

<style scoped>
.grp-btn {
  margin-left: auto;
  align-self: center;
  white-space: nowrap;
}
.grp-menu {
  list-style: none;
  margin: 0;
  padding: 0;
  min-width: 130px;
}
.grp-menu li {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  font-size: var(--fs-sm);
}
.grp-menu label {
  cursor: pointer;
}
</style>
