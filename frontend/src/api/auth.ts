import axios from 'axios'

export async function apiRegister(email: string, password: string): Promise<string> {
  const { data } = await axios.post<{ access_token: string }>('/api/auth/register', {
    email,
    password,
  })
  return data.access_token
}

export async function apiLogin(email: string, password: string): Promise<string> {
  const { data } = await axios.post<{ access_token: string }>('/api/auth/login', {
    email,
    password,
  })
  return data.access_token
}

export async function apiMe(): Promise<{ user_id: number; email: string }> {
  const { data } = await axios.get<{ user_id: number; email: string }>('/api/me')
  return data
}
