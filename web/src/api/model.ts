import http from './index'

export interface ModelProvider {
  id: string
  name: string
  provider_type: string
  api_key: string
  base_url: string
  is_active: boolean
  tenant_id: string
  created_at: string
}

export interface ModelConfig {
  id: string
  name: string
  model_id: string
  provider_id: string
  provider_name: string
  max_tokens: number
  temperature: number
  top_p: number
  is_active: boolean
  tenant_id: string
  created_at: string
}

export interface CreateProviderParams {
  name: string
  provider_type: string
  api_key: string
  base_url?: string
  tenant_id: string
}

export interface UpdateProviderParams {
  name?: string
  provider_type?: string
  api_key?: string
  base_url?: string
  is_active?: boolean
}

export interface CreateModelParams {
  name: string
  model_id: string
  provider_id: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  tenant_id?: string
}

export interface UpdateModelParams {
  name?: string
  model_id?: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  is_active?: boolean
}

export function getProviders(params?: { page?: number; page_size?: number; tenant_id?: string }) {
  return http.get<{ items: ModelProvider[]; total: number }>('/model/providers', { params })
}

export function getProvider(id: string) {
  return http.get<ModelProvider>(`/model/providers/${id}`)
}

export function createProvider(data: CreateProviderParams) {
  return http.post<ModelProvider>('/model/providers', data)
}

export function updateProvider(id: string, data: UpdateProviderParams) {
  return http.put<ModelProvider>(`/model/providers/${id}`, data)
}

export function deleteProvider(id: string) {
  return http.delete(`/model/providers/${id}`)
}

export function getModels(params?: { page?: number; page_size?: number; provider_id?: string; tenant_id?: string }) {
  return http.get<{ items: ModelConfig[]; total: number }>('/model/models', { params })
}

export function getModel(id: string) {
  return http.get<ModelConfig>(`/model/models/${id}`)
}

export function createModel(data: CreateModelParams) {
  return http.post<ModelConfig>('/model/models', data)
}

export function updateModel(id: string, data: UpdateModelParams) {
  return http.put<ModelConfig>(`/model/models/${id}`, data)
}

export function deleteModel(id: string) {
  return http.delete(`/model/models/${id}`)
}
