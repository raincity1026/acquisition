<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Group } from '../api/watchlist'
import { useWatchlist } from '../composables/useWatchlist'
import WatchRow from './WatchRow.vue'

const { items, groups, reload, createGroup, renameGroup, deleteGroup } = useWatchlist()

onMounted(reload)

const addingGroup = ref(false)
const newGroupName = ref('')

const ungrouped = computed(() => items.value.filter((i) => i.group_ids.length === 0))
function itemsOf(gid: number) {
  return items.value.filter((i) => i.group_ids.includes(gid))
}

async function submitGroup() {
  const name = newGroupName.value.trim()
  if (!name) return
  try {
    await createGroup(name)
    newGroupName.value = ''
    addingGroup.value = false
  } catch (e) {
    alert(errMsg(e))
  }
}
async function doRename(g: Group) {
  const name = prompt('重命名分组', g.name)?.trim()
  if (name && name !== g.name) {
    try {
      await renameGroup(g.id, name)
    } catch (e) {
      alert(errMsg(e))
    }
  }
}
async function doDelete(g: Group) {
  if (confirm(`删除分组「${g.name}」？组内股票会回到默认分组（不会从自选删除）。`)) {
    await deleteGroup(g.id)
  }
}

function errMsg(e: unknown): string {
  if (typeof e === 'object' && e && 'response' in e) {
    const r = (e as { response?: { data?: { detail?: string } } }).response
    if (r?.data?.detail) return r.data.detail
  }
  return '操作失败'
}
</script>

<template>
  <aside class="watchlist">
    <div class="head">
      <h3>自选股</h3>
      <button class="addgrp" title="新建分组" @click="addingGroup = !addingGroup">＋ 分组</button>
    </div>
    <div v-if="addingGroup" class="newgrp">
      <input v-model="newGroupName" placeholder="新分组名" @keyup.enter="submitGroup" />
      <button @click="submitGroup">建</button>
    </div>

    <p v-if="items.length === 0" class="empty">用上方搜索添加标的</p>

    <!-- 无分组：扁平展示 -->
    <ul v-if="groups.length === 0" class="list">
      <WatchRow v-for="it in items" :key="it.symbol" :item="it" :groups="groups" />
    </ul>

    <!-- 有分组：命名分组段（含空组便于管理）+ 默认分组段 -->
    <template v-else>
      <section v-for="g in groups" :key="g.id" class="section">
        <div class="title">
          <span class="gname">{{ g.name }}</span>
          <span class="count">{{ itemsOf(g.id).length }}</span>
          <button class="mini" title="重命名" @click="doRename(g)">✎</button>
          <button class="mini" title="删除分组" @click="doDelete(g)">🗑</button>
        </div>
        <ul class="list">
          <WatchRow
            v-for="it in itemsOf(g.id)"
            :key="g.id + '-' + it.symbol"
            :item="it"
            :groups="groups"
          />
        </ul>
      </section>

      <section class="section">
        <div class="title">
          <span class="gname">默认分组</span>
          <span class="count">{{ ungrouped.length }}</span>
        </div>
        <ul class="list">
          <WatchRow
            v-for="it in ungrouped"
            :key="'def-' + it.symbol"
            :item="it"
            :groups="groups"
          />
        </ul>
      </section>
    </template>
  </aside>
</template>

<style scoped>
.watchlist {
  width: 250px;
  border-right: 1px solid #eee;
  padding: 10px 8px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px 8px;
}
.head h3 {
  font-size: 14px;
  margin: 0;
}
.addgrp {
  border: none;
  background: transparent;
  color: #1565c0;
  cursor: pointer;
  font-size: 12px;
}
.newgrp {
  display: flex;
  gap: 6px;
  padding: 0 4px 8px;
}
.newgrp input {
  flex: 1;
  padding: 4px 6px;
  min-width: 0;
}
.empty {
  color: #999;
  font-size: 13px;
  padding: 0 8px;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.section {
  margin-bottom: 8px;
}
.title {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #666;
  background: #fafafa;
  border-radius: 4px;
}
.gname {
  font-weight: 600;
}
.count {
  color: #aaa;
}
.mini {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  margin-left: auto;
  opacity: 0.6;
}
.mini:last-child {
  margin-left: 0;
}
.mini:hover {
  opacity: 1;
}
</style>
