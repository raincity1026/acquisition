<script setup lang="ts">
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Menu from 'primevue/menu'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, reactive, ref } from 'vue'
import type { Group } from '../api/watchlist'
import { useWatchlist } from '../composables/useWatchlist'
import WatchRow from './WatchRow.vue'

const { items, groups, reload, createGroup, renameGroup, deleteGroup } = useWatchlist()
const confirm = useConfirm()
const toast = useToast()

onMounted(reload)

const ungrouped = computed(() => items.value.filter((i) => i.group_ids.length === 0))
function itemsOf(gid: number) {
  return items.value.filter((i) => i.group_ids.includes(gid))
}

// 新建/重命名 共用一个对话框
const dlg = reactive({ visible: false, mode: 'create' as 'create' | 'rename', id: 0, name: '' })
function openCreate() {
  Object.assign(dlg, { visible: true, mode: 'create', id: 0, name: '' })
}
function openRename(g: Group) {
  Object.assign(dlg, { visible: true, mode: 'rename', id: g.id, name: g.name })
}
async function submitGroup() {
  const name = dlg.name.trim()
  if (!name) return
  try {
    if (dlg.mode === 'create') await createGroup(name)
    else await renameGroup(dlg.id, name)
    dlg.visible = false
  } catch (e) {
    toast.add({ severity: 'error', summary: '操作失败', detail: errMsg(e), life: 3000 })
  }
}
function confirmDelete(g: Group) {
  confirm.require({
    header: '删除分组',
    message: `删除分组「${g.name}」？组内股票会回到默认分组（不会从自选删除）。`,
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: '取消', text: true },
    acceptProps: { label: '删除', severity: 'danger' },
    accept: () => deleteGroup(g.id),
  })
}

// 分组「…」菜单：重命名/删除。单实例共享，点击时记住当前分组
const menu = ref()
const menuGroup = ref<Group | null>(null)
const menuItems = computed(() => [
  {
    label: '重命名',
    icon: 'pi pi-pencil',
    command: () => menuGroup.value && openRename(menuGroup.value),
  },
  {
    label: '删除',
    icon: 'pi pi-trash',
    command: () => menuGroup.value && confirmDelete(menuGroup.value),
  },
])
function openMenu(e: Event, g: Group) {
  menuGroup.value = g
  menu.value.toggle(e)
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
      <Button label="分组" icon="pi pi-plus" text size="small" @click="openCreate" />
    </div>

    <p v-if="items.length === 0" class="empty">用上方搜索添加标的</p>

    <!-- 无分组：扁平 -->
    <ul v-if="groups.length === 0" class="list">
      <WatchRow v-for="it in items" :key="it.symbol" :item="it" />
    </ul>

    <!-- 有分组：命名分组段（含空组）+ 默认分组段 -->
    <template v-else>
      <section v-for="g in groups" :key="g.id" class="section">
        <div class="title">
          <span class="gname">{{ g.name }}</span>
          <span class="count">{{ itemsOf(g.id).length }}</span>
          <Button
            icon="pi pi-ellipsis-h"
            text
            rounded
            size="small"
            severity="secondary"
            aria-label="分组操作"
            @click="openMenu($event, g)"
          />
        </div>
        <ul class="list">
          <WatchRow v-for="it in itemsOf(g.id)" :key="g.id + '-' + it.symbol" :item="it" />
        </ul>
      </section>

      <section class="section">
        <div class="title">
          <span class="gname">默认分组</span>
          <span class="count">{{ ungrouped.length }}</span>
        </div>
        <ul class="list">
          <WatchRow v-for="it in ungrouped" :key="'def-' + it.symbol" :item="it" />
        </ul>
      </section>
    </template>

    <Menu
      ref="menu"
      :model="menuItems"
      popup
      :pt="{ root: { style: 'min-width:6rem;transform:translateX(calc(-100% + 24px))' } }"
    />

    <Dialog
      v-model:visible="dlg.visible"
      :header="dlg.mode === 'create' ? '新建分组' : '重命名分组'"
      modal
      :style="{ width: '300px' }"
    >
      <InputText v-model="dlg.name" placeholder="分组名" fluid autofocus @keyup.enter="submitGroup" />
      <template #footer>
        <Button label="取消" text @click="dlg.visible = false" />
        <Button label="确定" @click="submitGroup" />
      </template>
    </Dialog>
  </aside>
</template>

<style scoped>
.watchlist {
  width: 250px;
  border-right: 1px solid var(--c-border);
  padding: var(--space-3) var(--space-2);
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-1) var(--space-2);
}
.head h3 {
  font-size: var(--fs-base);
  font-weight: var(--fw-semibold);
  margin: 0;
}
.empty {
  color: var(--c-text-tertiary);
  font-size: var(--fs-sm);
  padding: 0 var(--space-2);
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.section {
  margin-bottom: var(--space-2);
}
.title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  font-size: var(--fs-caption);
  color: var(--c-text-secondary);
  background: var(--c-surface-50);
  border-radius: var(--radius-sm);
}
.gname {
  font-weight: var(--fw-semibold);
}
.count {
  color: var(--c-text-tertiary);
}
.title :deep(.p-button) {
  width: 24px;
  height: 24px;
}
.title :deep(.p-button:first-of-type) {
  margin-left: auto;
}
</style>
