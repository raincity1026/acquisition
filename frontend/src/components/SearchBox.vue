<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { ref } from 'vue'
import { apiSearch, type SearchHit } from '../api/watchlist'
import { useSelection } from '../composables/useSelection'
import { useWatchlist } from '../composables/useWatchlist'

const { view } = useSelection()
const { add } = useWatchlist()

const q = ref('')
const hits = ref<SearchHit[]>([])
const open = ref(false)
let timer: number | undefined

function onInput() {
  window.clearTimeout(timer)
  const term = q.value.trim()
  if (!term) {
    hits.value = []
    open.value = false
    return
  }
  timer = window.setTimeout(async () => {
    try {
      hits.value = await apiSearch(term)
      open.value = true
    } catch {
      hits.value = []
    }
  }, 250)
}

function chart(hit: SearchHit) {
  view(hit.symbol)
  close()
}
async function star(hit: SearchHit) {
  await add(hit.symbol)
  close()
}
function close() {
  open.value = false
  q.value = ''
  hits.value = []
}
</script>

<template>
  <div class="search">
    <span class="p-input-icon-left">
      <InputText
        v-model="q"
        placeholder="搜索代码或名称，如 茅台 / 600519"
        fluid
        @input="onInput"
        @focus="open = hits.length > 0"
      />
    </span>
    <ul v-if="open && hits.length" class="dropdown">
      <li v-for="h in hits" :key="h.symbol">
        <span class="meta" @click="chart(h)">
          <b>{{ h.name }}</b> <span class="code">{{ h.symbol }}</span>
        </span>
        <Button label="自选" icon="pi pi-plus" text size="small" @click="star(h)" />
      </li>
    </ul>
  </div>
</template>

<style scoped>
.search {
  position: relative;
  width: 340px;
}
.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin: var(--space-1) 0 0;
  padding: var(--space-1);
  list-style: none;
  background: var(--c-surface-0);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  max-height: 340px;
  overflow: auto;
  z-index: var(--z-dropdown);
}
.dropdown li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
}
.dropdown li:hover {
  background: var(--c-surface-50);
}
.meta {
  cursor: pointer;
  flex: 1;
  font-size: var(--fs-sm);
}
.code {
  color: var(--c-text-tertiary);
  font-size: var(--fs-caption);
}
</style>
