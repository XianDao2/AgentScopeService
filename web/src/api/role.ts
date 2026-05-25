import http from './index'

export interface Role {
  id: string
  name: string
  description: string
  permissions: string[]
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface CreateRoleParams {
  name: string
  description?: string
  permissions?: string[]
  tenant_id: string
}

export interface UpdateRoleParams {
  name?: string
  description?: string
  permissions?: string[]
}

export function getRoles(params?: { page?: number; page_size?: number; tenant_id?: string }) {
  return http.get<{ items: Role[]; total: number }>('/roles', { params })
}

export function getRole(id: string) {
  return http.get<Role>(`/roles/${id}`)
}

export function createRole(data: CreateRoleParams) {
  return http.post<Role>('/roles', data)
}

export function updateRole(id: string, data: UpdateRoleParams) {
  return http.put<Role>(`/roles/${id}`, data)
}

export function deleteRole(id: string) {
  return http.delete(`/roles/${id}`)
}
