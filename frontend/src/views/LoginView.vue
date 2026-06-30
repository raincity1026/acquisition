<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login } = useAuth()
const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await login(email.value.trim(), password.value)
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
  return '登录失败，请检查后端是否启动'
}
</script>

<template>
  <div class="auth">
    <!-- 左上角品牌 -->
    <header class="brand">
      <span class="mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none">
          <rect x="3" y="10" width="3.4" height="9" rx="1" fill="currentColor" />
          <rect x="10.3" y="5" width="3.4" height="14" rx="1" fill="currentColor" />
          <rect x="17.6" y="13" width="3.4" height="6" rx="1" fill="currentColor" opacity=".55" />
        </svg>
      </span>
      <span class="word">盘后复盘</span>
    </header>

    <!-- 居中表单 -->
    <main class="center">
      <div class="box">
        <h1 class="title">欢迎回来</h1>
        <p class="subtitle">盘后 A 股复盘 · 多股归一对比</p>

        <form class="form" @submit.prevent="submit">
          <label class="field">
            <span class="lbl">邮箱</span>
            <InputText v-model="email" type="email" placeholder="you@example.com" fluid autofocus />
          </label>
          <label class="field">
            <span class="lbl">密码</span>
            <Password v-model="password" placeholder="输入密码" :feedback="false" toggle-mask fluid />
          </label>
          <Button type="submit" label="登录" :loading="busy" fluid class="submit" />
          <p v-if="error" class="err">{{ error }}</p>
        </form>

        <p class="alt">还没有账号？<RouterLink to="/register">注册</RouterLink></p>
      </div>
    </main>

    <!-- 底部协议 -->
    <footer class="legal">登录即代表同意《服务条款》与《隐私政策》</footer>
  </div>
</template>

<style scoped>
.auth {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--c-surface-0);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6);
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--c-text);
}
.mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  background: var(--c-text);
  color: #fff;
}

.center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}
.box {
  width: 380px;
  max-width: 100%;
}
.title {
  margin: 0;
  text-align: center;
  font-size: 32px;
  font-weight: var(--fw-semibold);
  letter-spacing: -0.02em;
  color: var(--c-text);
}
.subtitle {
  margin: var(--space-3) 0 var(--space-8);
  text-align: center;
  font-size: var(--fs-md);
  color: var(--c-text-secondary);
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.lbl {
  font-size: var(--fs-sm);
  font-weight: var(--fw-medium);
  color: var(--c-text);
}
.form :deep(.p-inputtext) {
  border-radius: var(--radius-md);
  font-size: var(--fs-base);
  padding-block: 10px;
}
/* 深色主按钮（参考的近黑风格，取设计令牌的主文字色）*/
.submit {
  margin-top: var(--space-3);
  border-radius: var(--radius-md);
  padding-block: 11px;
  font-weight: var(--fw-semibold);
  background: var(--c-text);
  border-color: var(--c-text);
}
.submit:hover {
  background: #000;
  border-color: #000;
}
.err {
  margin: 0;
  text-align: center;
  font-size: var(--fs-sm);
  color: var(--c-danger);
}
.alt {
  margin: var(--space-6) 0 0;
  text-align: center;
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
}
.alt a {
  color: var(--c-text);
  font-weight: var(--fw-medium);
  text-decoration: none;
}
.alt a:hover {
  text-decoration: underline;
}

.legal {
  padding: var(--space-6);
  text-align: center;
  font-size: var(--fs-caption);
  color: var(--c-text-tertiary);
}
</style>
