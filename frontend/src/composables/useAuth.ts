import { computed, ref } from 'vue'
import { apiLogin, apiMe, apiRegister } from '../api/auth'
import { clearToken, getToken, setToken } from '../auth/token'

const email = ref<string | null>(null)

export function useAuth() {
  const isAuthed = computed(() => !!getToken())

  async function login(e: string, p: string): Promise<void> {
    setToken(await apiLogin(e, p))
    email.value = e
  }
  async function register(e: string, p: string): Promise<void> {
    setToken(await apiRegister(e, p))
    email.value = e
  }
  function logout(): void {
    clearToken()
    email.value = null
  }
  // 刷新页面后用已存 token 拉回身份
  async function loadMe(): Promise<void> {
    if (!getToken()) return
    try {
      email.value = (await apiMe()).email
    } catch {
      logout()
    }
  }

  return { email, isAuthed, login, register, logout, loadMe }
}
