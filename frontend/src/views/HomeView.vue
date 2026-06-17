<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MarketView from './MarketView.vue'
import SearchBox from '../components/SearchBox.vue'
import WatchlistPanel from '../components/WatchlistPanel.vue'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { email, logout, loadMe } = useAuth()

onMounted(loadMe)

function doLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <h1>股票复盘</h1>
      <SearchBox />
      <div class="user">
        <span class="email">{{ email }}</span>
        <button @click="doLogout">退出</button>
      </div>
    </header>
    <div class="body">
      <WatchlistPanel />
      <main class="main"><MarketView /></main>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 16px;
  border-bottom: 1px solid #eee;
}
.topbar h1 {
  font-size: 17px;
  margin: 0;
  white-space: nowrap;
}
.user {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.user .email {
  color: #666;
}
.user button {
  padding: 5px 10px;
  cursor: pointer;
}
.body {
  display: flex;
  align-items: flex-start;
}
.main {
  flex: 1;
  min-width: 0;
  padding-top: 8px;
}
</style>
