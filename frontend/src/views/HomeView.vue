<script setup lang="ts">
import Button from 'primevue/button'
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
      <SearchBox />
      <div class="user">
        <span class="email">{{ email }}</span>
        <Button label="退出" severity="secondary" text size="small" @click="doLogout" />
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
  gap: var(--space-5);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--c-border);
  background: var(--c-surface-0);
}
.user {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-sm);
}
.user .email {
  color: var(--c-text-secondary);
}
.body {
  display: flex;
  align-items: flex-start;
}
.main {
  flex: 1;
  min-width: 0;
  padding-top: var(--space-2);
}
</style>
