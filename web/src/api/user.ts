import http from './index'

export interface User {
  id: string
  username: string
  email: string
  tenant_id: string
  tenant_name: string
  roles: string[]
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
}

export interface CreateUserParams {
  username: string
  password: string
  email?: string
  tenant_id: string
  roles?: string[]
  is_active?: boolean
}

export interface UpdateUserParams {
  email?: string
  password?: string
  roles?: string[]
  is_active?: boolean
  tenant_id?: string
}

export function getUsers(params?: { page?: number; page_size?: number; tenant_id?: string }) {
  return http.get<{ items: User[]; total: number }>('/users', { params })
}

export function getUser(id: string) {
  return http.get<User>(`/users/${id}`)
}

export function createUser(data: CreateUserParams) {
  return http.post<User>('/users', data)
}

export function updateUser(id: string, data: UpdateUserParams) {
  return http.put<User>(`/users/${id}`, data)
}

export function deleteUser(id: string) {
  return http.delete(`/users/${id}`)
}
