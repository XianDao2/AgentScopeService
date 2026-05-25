import http from './index'

export interface AgentDefinition {
  id: string
  name: string
  agent_type: string
  sys_prompt: string
  model_id: string
  model_name: string
  tool_group_ids: string[]
  tool_group_names: string[]
  knowledge_base_ids: string[]
  max_retries: number
  is_active: boolean
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface CreateAgentParams {
  name: string
  agent_type: string
  sys_prompt?: string
  model_id: string
  tool_group_ids?: string[]
  knowledge_base_ids?: string[]
  max_retries?: number
  tenant_id?: string
}

export interface UpdateAgentParams {
  name?: string
  agent_type?: string
  sys_prompt?: string
  model_id?: string
  tool_group_ids?: string[]
  knowledge_base_ids?: string[]
  max_retries?: number
  is_active?: boolean
}

export interface AgentSession {
  id: string
  agent_id: string
  agent_name: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
}

export function getAgents(params?: { page?: number; page_size?: number; tenant_id?: string }) {
  return http.get<{ items: AgentDefinition[]; total: number }>('/agent/definitions', { params })
}

export function getAgent(id: string) {
  return http.get<AgentDefinition>(`/agent/definitions/${id}`)
}

export function createAgent(data: CreateAgentParams) {
  return http.post<AgentDefinition>('/agent/definitions', data)
}

export function updateAgent(id: string, data: UpdateAgentParams) {
  return http.put<AgentDefinition>(`/agent/definitions/${id}`, data)
}

export function deleteAgent(id: string) {
  return http.delete(`/agent/definitions/${id}`)
}

export function getSessions(params?: { page?: number; page_size?: number; agent_id?: string }) {
  return http.get<{ items: AgentSession[]; total: number }>('/sessions', { params })
}

export function createSession(data: { agent_id: string; title?: string }) {
  return http.post<AgentSession>('/sessions', data)
}

export function deleteSession(id: string) {
  return http.delete(`/sessions/${id}`)
}
