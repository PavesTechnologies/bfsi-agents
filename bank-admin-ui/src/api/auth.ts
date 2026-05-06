import { apiClient } from './client'

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserOut {
  id: string
  email: string
  full_name: string | null
  role: { id: number; name: string; description: string | null }
  is_active: boolean
  created_at: string
  last_login_at: string | null
}

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<TokenResponse>('/auth/login', { email, password }).then((r) => r.data),

  logout: (refresh_token: string) =>
    apiClient.post('/auth/logout', { refresh_token }),

  me: () => apiClient.get<UserOut>('/auth/me').then((r) => r.data),

  changePassword: (current_password: string, new_password: string) =>
    apiClient.patch('/auth/me/password', { current_password, new_password }).then((r) => r.data),
}
