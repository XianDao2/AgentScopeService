import http from './index'

export interface ToolGroup {
  id: string
  name: string
  description: string
  tools: ToolItem[]
  is_active: boolean
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface ToolItem {
  name: string
  description: string
  parameters: Record<string, any>
  is_registered: boolean
}

export interface CreateToolGroupParams {
  name: string
  description?: string
  tenant_id: string
}

export interface UpdateToolGroupParams {
  name?: string
  description?: string
  is_active?: boolean
}

export interface RegisterToolParams {
  tool_name: string
  tool_config: Record<string, any>
}

export function getToolGroups(params?: { page?: number; page_size?: number; tenant_id?: string }) {
  return http.get<{ items: ToolGroup[]; total: number }>('/tool-groups', { params })
}

export function getToolGroup(id: string) {
  return http.get<ToolGroup>(`/tool-groups/${id}`)
}

export function createToolGroup(data: CreateToolGroupParams) {
  return http.post<ToolGroup>('/tool-groups', data)
}

export function updateToolGroup(id: string, data: UpdateToolGroupParams) {
  return http.put<ToolGroup>(`/tool-groups/${id}`, data)
}

export function deleteToolGroup(id: string) {
  return http.delete(`/tool-groups/${id}`)
}

export function registerTool(id: string, data: RegisterToolParams) {
  return http.post(`/tool-groups/${id}/tools`, data)
}

export function unregisterTool(id: string, toolName: string) {
  return http.delete(`/tool-groups/${id}/tools/${toolName}`)
}

export function toggleToolGroup(id: string, is_active: boolean) {
  return http.put<ToolGroup>(`/tool-groups/${id}`, { is_active })
}
