import http from './index'

export interface Tenant {
  id: string
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateTenantParams {
  name: string
  description?: string
  is_active?: boolean
}

export interface UpdateTenantParams {
  name?: string
  description?: string
  is_active?: boolean
}

export function getTenants(params?: { page?: number; page_size?: number }) {
  return http.get<{ items: Tenant[]; total: number }>('/tenants', { params })
}

export function getTenant(id: string) {
  return http.get<Tenant>(`/tenants/${id}`)
}

export function createTenant(data: CreateTenantParams) {
  return http.post<Tenant>('/tenants', data)
}

export function updateTenant(id: string, data: UpdateTenantParams) {
  return http.put<Tenant>(`/tenants/${id}`, data)
}

export function deleteTenant(id: string) {
  return http.delete(`/tenants/${id}`)
}
