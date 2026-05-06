import { apiClient } from './client'
import type { UserOut } from './auth'

export interface UserCreate {
  email: string
  password: string
  full_name?: string
  role_id: number
}

export interface UserUpdate {
  full_name?: string
  role_id?: number
  is_active?: boolean
}

export interface UserListResponse {
  items: UserOut[]
  total: number
  page: number
  page_size: number
}

export interface Role {
  id: number
  name: string
  description: string | null
}

export const usersApi = {
  list: (page = 1, page_size = 20) =>
    apiClient.get<UserListResponse>('/users', { params: { page, page_size } }).then((r) => r.data),

  get: (id: string) => apiClient.get<UserOut>(`/users/${id}`).then((r) => r.data),

  create: (payload: UserCreate) => apiClient.post<UserOut>('/users', payload).then((r) => r.data),

  update: (id: string, payload: UserUpdate) => apiClient.patch<UserOut>(`/users/${id}`, payload).then((r) => r.data),

  roles: () => apiClient.get<Role[]>('/users/roles').then((r) => r.data),
}
