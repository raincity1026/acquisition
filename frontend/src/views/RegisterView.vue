<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { register } = useAuth()
const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  if (password.value.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  busy.value = true
  try {
    await register(email.value.trim(), password.value)
    router.push('/')
  } catch (e: unknown) {
    error.value = errMsg(e)
  } finally {
    busy.value = false
  }
}

function errMsg(e: unknown): string {
  if (typeof e === 'object' && e && 'response' in e) {
    const r = (e as { response?: { data?: { detail?: string } } }).response
    if (r?.data?.detail) return r.data.detail
  }
  return '注册失败，请检查后端是否启动'
}
</script>

<template>
  <div class="auth">
    <form class="card" @submit.prevent="submit">
      <h2>注册</h2>
      <input v-model="email" type="email" placeholder="邮箱" required />
      <input v-model="password" type="password" placeholder="密码（至少 6 位）" required />
      <button :disabled="busy" type="submit">{{ busy ? '注册中…' : '注册' }}</button>
      <p v-if="error" class="err">{{ error }}</p>
      <p class="alt">已有账号？<RouterLink to="/login">登录</RouterLink></p>
    </form>
  </div>
</template>

<style scoped>
.auth {
  display: flex;
  justify-content: center;
  padding-top: 80px;
}
.card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 300px;
  padding: 28px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
}
.card h2 {
  margin: 0 0 4px;
}
.card input {
  padding: 8px 10px;
}
.card button {
  padding: 9px;
  background: #1565c0;
  color: #fff;
  border-color: #1565c0;
  cursor: pointer;
}
.err {
  color: #c62828;
  font-size: 13px;
  margin: 0;
}
.alt {
  font-size: 13px;
  margin: 0;
}
</style>
