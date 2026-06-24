<script setup lang="ts">
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
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
    <Card class="card">
      <template #title>注册</template>
      <template #content>
        <form class="form" @submit.prevent="submit">
          <InputText v-model="email" type="email" placeholder="邮箱" fluid autofocus />
          <Password
            v-model="password"
            placeholder="密码（至少 6 位）"
            :feedback="false"
            toggle-mask
            fluid
          />
          <Button type="submit" label="注册" :loading="busy" fluid />
          <p v-if="error" class="err">{{ error }}</p>
          <p class="alt">已有账号？<RouterLink to="/login">登录</RouterLink></p>
        </form>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.auth {
  display: flex;
  justify-content: center;
  padding-top: 80px;
}
.card {
  width: 320px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.err {
  color: var(--c-danger);
  font-size: var(--fs-sm);
  margin: 0;
}
.alt {
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
  margin: 0;
}
</style>
