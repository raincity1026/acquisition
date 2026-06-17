<script setup lang="ts">
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
    <input
      v-model="q"
      placeholder="搜索代码或名称，如 茅台 / 600519"
      @input="onInput"
      @focus="open = hits.length > 0"
    />
    <ul v-if="open && hits.length" class="dropdown">
      <li v-for="h in hits" :key="h.symbol">
        <span class="meta" @click="chart(h)">
          <b>{{ h.name }}</b> <span class="code">{{ h.symbol }}</span>
        </span>
        <button class="add" title="加自选" @click="star(h)">＋自选</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.search {
  position: relative;
  width: 320px;
}
.search input {
  width: 100%;
  padding: 7px 10px;
}
.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin: 4px 0 0;
  padding: 4px;
  list-style: none;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  max-height: 340px;
  overflow: auto;
  z-index: 20;
}
.dropdown li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 4px;
}
.dropdown li:hover {
  background: #f6f7f9;
}
.meta {
  cursor: pointer;
  flex: 1;
}
.code {
  color: #999;
  font-size: 12px;
}
.add {
  border: none;
  background: transparent;
  color: #1565c0;
  cursor: pointer;
  font-size: 12px;
}
</style>
